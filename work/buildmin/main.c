#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "quickjs.h"

static void *my_malloc(void *opaque, size_t size) { return malloc(size); }
static void my_free(void *opaque, void *ptr) { free(ptr); }
static void *my_realloc(void *opaque, void *ptr, size_t size) { return realloc(ptr, size); }
static size_t my_usable(void *opaque, void *ptr) { return 0; }

static JSValue js_print(JSContext *ctx, JSValueConst this_val, int argc, JSValueConst *argv)
{
    int i;
    for (i = 0; i < argc; i++) {
        const char *s = JS_ToCString(ctx, argv[i]);
        if (!s) return JS_EXCEPTION;
        fputs(s, stdout);
        JS_FreeCString(ctx, s);
    }
    putchar('\n');
    return JS_UNDEFINED;
}

static JSValue js_gc(JSContext *ctx, JSValueConst this_val, int argc, JSValueConst *argv)
{
    JS_RunGC(JS_GetRuntime(ctx));
    return JS_UNDEFINED;
}

int main(int argc, char **argv)
{
    unsigned char hdr[4];
    unsigned int len;
    char *buf;
    size_t got = 0;
    JSMallocFunctions mf = { my_malloc, my_free, my_realloc, my_usable };
    JSRuntime *rt;
    JSContext *ctx;
    JSValue obj, exc;

    if (fread(hdr, 1, 4, stdin) != 4) return 1;
    len = ((unsigned)hdr[0] << 24) | ((unsigned)hdr[1] << 16) |
          ((unsigned)hdr[2] << 8) | hdr[3];
    if (len < 1 || len > 0x40000) return 1;
    buf = malloc(len + 1);
    if (!buf) return 1;
    while (got < len) {
        size_t n = fread(buf + got, 1, len - got, stdin);
        if (n == 0) break;
        got += n;
    }
    buf[len] = '\0';

    rt = JS_NewRuntime2(&mf, NULL);
    JS_SetMemoryLimit(rt, 0x8000000);
    JS_SetMaxStackSize(rt, 0x100000);
    ctx = JS_NewContext(rt);
    obj = JS_NewCFunction(ctx, js_print, "print", 1);
    JS_SetPropertyStr(ctx, JS_GetGlobalObject(ctx), "print", obj);
    obj = JS_NewCFunction(ctx, js_gc, "gc", 0);
    JS_SetPropertyStr(ctx, JS_GetGlobalObject(ctx), "gc", obj);

    exc = JS_Eval(ctx, buf, len, "<input>", JS_EVAL_TYPE_GLOBAL);
    free(buf);
    if (JS_IsException(exc)) {
        JSValue e = JS_GetException(ctx);
        const char *s = JS_ToCString(ctx, e);
        if (s) { fprintf(stderr, "%s\n", s); JS_FreeCString(ctx, s); }
    }
    JS_FreeContext(ctx);
    JS_FreeRuntime(rt);
    return 0;
}
