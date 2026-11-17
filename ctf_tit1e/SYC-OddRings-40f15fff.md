# SYC - Odd Rings（附件 `40f15fff / chall.py`）

- 类型：Crypto（线性方程组）
- 附件：`chall.py`、`data`
- Flag：`syc{odd_rings_close_the_key}`

## 1. 题目代码

```python
P = 257

def seal(message, key):
    if len(message) != len(key) or len(key) % 2 != 1:
        raise ValueError("an odd tape and equally long key are required")
    ciphertext = [(m + k) % P for m, k in zip(message, key)]
    receipt = [(key[i] + key[(i + 1) % len(key)]) % P
               for i in range(len(key))]
    return ciphertext, receipt
```

公开数据 `data`：

```json
{"p": 257, "n": 65, "length": 28, "ciphertext": [...], "receipt": [...]}
```

`message = flag + 随机填充`，`key` 是 65 个 `[0,257)` 的随机数，`ciphertext = message + key`，`receipt` 是**环形相邻密钥之和**。

## 2. 思路

回执只暴露相邻和：

```
a_i = k_i + k_{i+1 mod n}  (mod 257)
```

这是一个环上的线性方程组。当 `n` 为奇数时系数矩阵可逆（交替符号会把中间项全部消掉）：

```
a_0 - a_1 + a_2 - ... + a_{64} = 2*k_0
```

所以

```
k_0 = (a_0 - a_1 + a_2 - ... + a_{64}) * 2^{-1} mod 257
k_{i+1} = a_i - k_i
```

求出整条 key 后 `message = ciphertext - key`，取前 `length = 28` 字节即得 flag。题目名 `odd_rings_close_the_key` 也直接点出了"奇数环可解"。

## 3. Exp

```python
import json

d = json.load(open('data'))
p, n, length = d['p'], d['n'], d['length']
c, a = d['ciphertext'], d['receipt']

s = sum(a[i] if i % 2 == 0 else -a[i] for i in range(n))
k = [(s * pow(2, -1, p)) % p]
for i in range(n - 1):
    k.append((a[i] - k[-1]) % p)

assert all((k[i] + k[(i + 1) % n]) % p == a[i] for i in range(n))

m = [(c[i] - k[i]) % p for i in range(n)]
print(bytes(m[:length]))
```

输出：

```
b'syc{odd_rings_close_the_key}'
```

## 4. 小结

- 关键点：环长为奇数时，相邻和方程组的秩为满秩；偶数环会出现两个自由度（需额外信息）。
- 用 `-a_i` 交替求和即可一次求出初值，避免解矩阵。
