#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import secrets
import threading
import time
from pwn import context
from pwnlib.tubes.server import server

context.log_level = "error"

P = (1 << 61) - 1
DIM = 8
QUERY_LIMIT = 10


def valid_ticket(v):
    return (type(v) is list and len(v) == DIM
            and all(type(x) is int and 1 <= x < P for x in v)
            and sum(v) % P == 1)


def tag(v, coefficients, offset):
    return (offset + sum(x * s for x, s in zip(v, coefficients))
            + sum(v) ** 2) % P


MAX_LINE = 512
MAX_CONNECTIONS = 64
IDLE_TIMEOUT = 10.0
SESSION_TIMEOUT = 60.0


def no_duplicates(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON key")
        obj[key] = value
    return obj


class TicketHandler:
    def __init__(self, tube, secret, *, idle_timeout, session_timeout):
        self.tube = tube
        self.secret = secret
        self.idle_timeout = idle_timeout
        self.session_timeout = session_timeout

    def send(self, obj):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError
        self.tube.settimeout(min(self.idle_timeout, remaining))
        self.tube.sendline(json.dumps(obj, separators=(",", ":")).encode())

    def read(self):
        # recv(1) keeps buffering bounded; recompute the absolute deadline even
        # when a client continuously trickles bytes.
        line = bytearray()
        while len(line) <= MAX_LINE:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError
            self.tube.settimeout(min(self.idle_timeout, remaining))
            b = self.tube.recv(1)
            if not b:
                raise TimeoutError
            if b == b"\n":
                if not line:
                    raise ValueError("empty line")
                return json.loads(line.decode("utf-8"), object_pairs_hook=no_duplicates)
            line.extend(b)
        raise ValueError("oversized line")

    def handle(self):
        self.deadline = time.monotonic() + self.session_timeout
        try:
            coefficients = [secrets.randbelow(P) for _ in range(DIM)]
            offset = secrets.randbelow(P)
            # Sampling without rejection: the last coordinate cannot be zero.
            target = [secrets.randbelow(P - 1) + 1 for _ in range(DIM - 2)]
            excluded = (1 - sum(target)) % P
            x = secrets.randbelow(P - 1 - int(excluded != 0)) + 1
            if excluded != 0 and x >= excluded:
                x += 1
            target.append(x)
            target.append((1 - sum(target)) % P)
            self.send({"version": 1, "p": P, "dimension": DIM,
                       "target": target, "query_limit": QUERY_LIMIT})
            queries = 0
            # At most ten sign requests and one final verification per connection.
            for _ in range(QUERY_LIMIT + 1):
                obj = self.read()
                if type(obj) is not dict:
                    raise ValueError("object required")
                if obj.get("op") == "sign" and set(obj) == {"op", "ticket"}:
                    queries += 1
                    v = obj["ticket"]
                    if queries > QUERY_LIMIT or not valid_ticket(v) or v == target:
                        raise ValueError("invalid sign request")
                    self.send({"tag": tag(v, coefficients, offset)})
                elif obj.get("op") == "claim" and set(obj) == {"op", "tag"}:
                    value = obj["tag"]
                    if type(value) is not int or not 0 <= value < P:
                        raise ValueError("invalid tag")
                    if value == tag(target, coefficients, offset):
                        self.send({"flag": self.secret})
                    else:
                        self.send({"error": "verification failed"})
                    return
                else:
                    raise ValueError("invalid operation")
            self.send({"error": "request limit"})
        except TimeoutError:
            try:
                self.send({"error": "timeout"})
            except (OSError, EOFError, TimeoutError):
                pass
        except (ValueError, UnicodeError, RecursionError):
            try:
                self.send({"error": "invalid request"})
            except (OSError, EOFError, TimeoutError):
                pass
        except (OSError, EOFError):
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=31337)
    ap.add_argument("--flag-file", type=Path, default=Path(__file__).resolve().with_name("flag.txt"))
    ap.add_argument("--idle-timeout", type=float, default=IDLE_TIMEOUT)
    ap.add_argument("--session-timeout", type=float, default=SESSION_TIMEOUT)
    ap.add_argument("--max-connections", type=int, default=MAX_CONNECTIONS)
    args = ap.parse_args()
    secret = args.flag_file.read_text(encoding="ascii").rstrip("\r\n")
    if not re.fullmatch(r"syc\{[a-z0-9_]{1,120}\}", secret):
        ap.error("invalid deployment flag")
    if not (0 < args.idle_timeout <= 10 and 0 < args.session_timeout <= 60
            and 1 <= args.max_connections <= 64):
        ap.error("invalid resource limits")
    slots = threading.BoundedSemaphore(args.max_connections)

    def dispatch(tube):
        # Run in the accept thread, before starting a per-client worker.
        if not slots.acquire(blocking=False):
            tube.close()
            return

        def worker():
            try:
                TicketHandler(tube, secret, idle_timeout=args.idle_timeout,
                              session_timeout=args.session_timeout).handle()
            finally:
                tube.close()
                slots.release()

        try:
            context.Thread(target=worker, daemon=True).start()
        except BaseException:
            tube.close()
            slots.release()
            raise

    listener = server(args.port, bindaddr=args.host, fam="ipv4",
                      callback=dispatch, blocking=True)
    print(f"[+] listening on {args.host}:{listener.lport}", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
