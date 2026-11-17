# SYC - Ech...ooo（附件 `3e9c2f8e / chall.sage + data.json`）

- 类型：Crypto（有限域离散对数 + 多项式环 + 掩码还原）
- 附件：`chall.sage`（出题脚本）、`data.json`（公开实例）
- Flag：`syc{StlIBElHGOoNeWfb_PiJF6W43lxjEJNlw_vDhlHo}`

## 1. 生成逻辑

`chall.sage` 在 `GF(65537)` 上随机生成两个 48 次不可约多项式 `f, g`，令 `H = f*g`（96 次），再取随机 `K, O, p0`：

```
inputs  = [p0, p0+f, p0+g]
outputs = K*input + O  (mod H)
C       = K*flag_poly + O (mod H)
```

所有系数都用 `cover()` 逐系数加上掩码：

```python
def cover(vals, secret, label):
    seed = int(secret).to_bytes(6, 'big')
    stream = hashlib.shake_256(b'SYC-SAGE-V2|' + label.encode() + b'|' + seed)
    buf = stream.digest(4 * len(vals))
    masks = [int.from_bytes(buf[4*i:4*i+4], 'big') % P for i in range(len(vals))]
    return [(int(c) + m) % P for c, m in zip(vals, masks)]
```

`secret` 就是 `s`。而 `data.json` 同时公开了 `GF(2^48)` 上的：

```
generator  a = 2（即多项式 x）
challenge  b = a^s
extension_modulus  E.modulus()
```

## 2. 突破口

**掩码种子 `s` 被 `a^s` 直接泄漏了。**

`GF(2^48)*` 的阶为

```
2^48 - 1 = 3^2 * 5 * 7 * 13 * 17 * 97 * 241 * 257 * 673
```

全部是小因子，Pohlig–Hellman + BSGS 秒解 `s = log_a(b)`。拿到 `s` 后按 `label` 重算 `shake_256` 掩码流，所有输出即可逐系数去掩码。

去掩码后还差 `K`。注意 `H = f*g`，所以 `f, g` 都**不可逆**，不能直接除。利用两组校准输出做 CRT：

```
y0 = K*p0   + O
y1 = K*(p0+f) + O   =>  y1 - y0 = K*f   (mod H)
y2 = K*(p0+g) + O   =>  y2 - y0 = K*g   (mod H)
```

- 模 `g`：`K ≡ (y1-y0) * f^{-1} (mod g)`
- 模 `f`：`K ≡ (y2-y0) * g^{-1} (mod f)`

两部分用多项式 CRT 合成 `K (mod H)`，再 `O = y0 - K*p0`，最后

```
message = (C - O) * K^{-1} mod H
```

取前 `length = 45` 个系数即 flag。

## 3. Exp（纯 Python 3，无需 Sage）

```python
import json, hashlib, math

D = json.load(open('data.json'))
P, W, L, EXT = D['p'], D['width'], D['length'], D['extension_degree']
MOD = sum(int(c) << i for i, c in enumerate(D['extension_modulus']))
G, B = D['generator'], D['challenge']

# ---- GF(2^48) ----
def mul(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        b >>= 1
        a <<= 1
        if a >> EXT & 1: a ^= MOD
    return r

def pw(a, e):
    r = 1
    while e:
        if e & 1: r = mul(r, a)
        a = mul(a, a); e >>= 1
    return r

inv = lambda a: pw(a, (1 << EXT) - 2)

def bsgs(base, target, q):
    m = math.isqrt(q) + 1
    table, e = {}, 1
    for j in range(m):
        table.setdefault(e, j); e = mul(e, base)
    step, gamma = inv(pw(base, m)), target
    for i in range(m + 1):
        if gamma in table:
            return i * m + table[gamma]
        gamma = mul(gamma, step)
    raise RuntimeError('dlog failed')

# ---- Pohlig-Hellman ----
order = (1 << EXT) - 1
def factor(n):
    f, d = {}, 2
    while d * d <= n:
        while n % d == 0:
            f[d] = f.get(d, 0) + 1; n //= d
        d += 1
    if n > 1: f[n] = f.get(n, 0) + 1
    return f

def crt(res):
    x, m = 0, 1
    for r, q in res:
        t = ((r - x) * pow(m, -1, q)) % q
        x += m * t; m *= q
    return x % m

res = []
for q, k in factor(order).items():
    qq = q ** k
    res.append((bsgs(pw(G, order // qq), pw(B, order // qq), qq) % qq, qq))
s = crt(res)
assert pw(G, s) == B

# ---- 去掩码 ----
def unmask(vals, label):
    seed = int(s).to_bytes(6, 'big')
    buf = hashlib.shake_256(b'SYC-SAGE-V2|' + label.encode() + b'|' + seed).digest(4 * len(vals))
    return [(int(c) - int.from_bytes(buf[4*i:4*i+4], 'big') % P) % P for i, c in enumerate(vals)]

# ---- GF(65537)[x] ----
def trim(a):
    while len(a) > 1 and a[-1] == 0: a.pop()
    return a

def padd(a, b):
    r = [0] * max(len(a), len(b))
    for i in range(len(r)):
        r[i] = ((a[i] if i < len(a) else 0) + (b[i] if i < len(b) else 0)) % P
    return trim(r)

psub = lambda a, b: padd(a, [(-x) % P for x in b])

def pmul(a, b):
    r = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b):
                r[i+j] = (r[i+j] + x*y) % P
    return trim(r)

def pdivmod(a, m):
    a = a[:]; trim(a)
    q = [0] * max(1, len(a) - len(m) + 1)
    im = pow(m[-1], -1, P)
    while len(a) >= len(m) and a != [0]:
        d, c = len(a) - len(m), a[-1] * im % P
        q[d] = c
        for i in range(len(m)):
            a[d+i] = (a[d+i] - c*m[i]) % P
        trim(a)
    return trim(q), a

pmod = lambda a, m: pdivmod(a, m)[1]

def gcdx(a, b):
    if b == [0]: return a, [1], [0]
    q, r = pdivmod(a, b)
    g, x, y = gcdx(b, r)
    return g, y, psub(x, pmul(q, y))

def pinv(a, m):
    g, x, _ = gcdx(a, m)
    return pmod([c * pow(g[0], -1, P) % P for c in x], m)

# ---- 恢复 K, O, flag ----
f, g = list(map(int, D['f'])), list(map(int, D['g']))
H = pmul(f, g)
p0 = list(map(int, D['calibration_inputs'][0]))
y = [unmask(v, 'cal-%d' % i) for i, v in enumerate(D['calibration_outputs_masked'])]
C = unmask(D['ciphertext_masked'], 'cipher')

K_g = pmod(pmul(psub(y[1], y[0]), pinv(pmod(f, g), g)), g)
K_f = pmod(pmul(psub(y[2], y[0]), pinv(pmod(g, f), f)), f)
t   = pmod(pmul(psub(K_g, K_f), pinv(pmod(f, g), g)), g)
K   = pmod(padd(K_f, pmul(f, t)), H)
O   = pmod(psub(y[0], pmod(pmul(K, p0), H)), H)

msg = pmod(pmul(psub(C, O), pinv(K, H)), H)
print(bytes(msg[:L]))
```

输出：

```
b'syc{StlIBElHGOoNeWfb_PiJF6W43lxjEJNlw_vDhlHo}'
```

校准项 `y0 / y2` 均能回代验证，说明 `K` 恢复正确。

## 4. 小结 / 踩坑

- 掩码看着很唬人，但种子 `s` 通过 `a^s` 泄漏，本质是"掩码可复现"而非"掩码未知"。
- `H = f*g`，`f`、`g` 在模 `H` 下**不可逆**；必须分别在模 `g`、模 `f` 下求 `K`，再多项式 CRT 合并。直接 `inv(f, H)` 会因 `gcd ≠ 1` 失败。
- 全程可脱离 Sage，纯 Python 实现 GF(2^48) 与 GF(65537)[x] 即可，约 1 秒内完成。
