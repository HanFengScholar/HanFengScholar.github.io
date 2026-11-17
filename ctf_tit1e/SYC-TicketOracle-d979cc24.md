# SYC - Ticket Oracle（附件 `d979cc24 / chall.py`）

- 类型：Crypto / Pwn（交互式签名预言机，8 维线性代数）
- 附件：`chall.py`（服务端源码）
- Flag：未留存（附件中只有服务端程序，需连远程实例获取）
- 交互：TCP，逐行 JSON，单连接最多 10 次 `sign` + 1 次 `claim`

## 1. 协议与公式

服务端每个连接随机生成：

```python
P = (1 << 61) - 1
coefficients = [secrets.randbelow(P) for _ in range(8)]
offset       = secrets.randbelow(P)
```

然后下发 `{"target": target, "p": P, "dimension": 8, "query_limit": 10}`，其中 `target` 满足 `sum(target) % P == 1`。

签名逻辑：

```python
def tag(v, coefficients, offset):
    return (offset + sum(x * s for x, s in zip(v, coefficients))
            + sum(v) ** 2) % P
```

有效票据的约束（`valid_ticket`）：8 个整数，`1 <= x < P`，且 `sum(v) % P == 1`。

`claim` 时提交与 `tag(target, ...)` 相等的整数即可换 flag。**`target` 本身不能用于签名**（`v == target` 直接报错），所以目标是从其他合法票据的 tag 反推 `target` 的 tag。

## 2. 攻击：8 次查询即可，不需要求 offset

取 8 个单位向量 `e_0..e_7`。它们每个分量非负、且 `sum = 1`，全部合法：

```
t_j = tag(e_j) = offset + s_j + 1      (mod P)
```

于是

```
offset + s_j = t_j - 1
```

注意 `target` 满足 `sum(target) ≡ 1 (mod P)`，而公式里的 `sum(v)**2` 是**整数和**的平方，因 `sum(target) ≡ 1` 有 `sum(target)^2 ≡ 1 (mod P)`。因此

```
tag(target) = offset + Σ target_j * s_j + 1
            = Σ target_j * (offset + s_j) + 1
            = Σ target_j * (t_j - 1) + 1        (mod P)
```

`offset` 被 `sum(target) ≡ 1` 完全消掉。直接 `claim` 该值即可，只用 8 次签名，远低于 10 次上限。

> 这也是本题的设计意图：票据和 `target` 同在超平面 `sum ≡ 1` 上，二次项对该超平面是常数 1，线性部分可用单位向量"原子化"求和。

## 3. Exp（标准库 socket，无需 pwntools）

```python
import json, socket

HOST, PORT = 'TARGET_HOST', 31337

sock = socket.create_connection((HOST, PORT), timeout=15)
f = sock.makefile('rwb')

hello = json.loads(f.readline())
P, target = hello['p'], hello['target']
DIM = hello['dimension']
assert sum(target) % P == 1

tags = []
for j in range(DIM):                      # 8 次，单位向量
    v = [1 if i == j else 0 for i in range(DIM)]
    f.write((json.dumps({"op": "sign", "ticket": v}, separators=(',', ':')) + '\n').encode())
    f.flush()
    tags.append(json.loads(f.readline())['tag'])

forged = (sum(x * (t - 1) for x, t in zip(target, tags)) + 1) % P
f.write((json.dumps({"op": "claim", "tag": forged}, separators=(',', ':')) + '\n').encode())
f.flush()
print(f.readline().decode())
```

本地用服务端源码 + 随机 `flag.txt` 模拟验证：8 次签名算出的 `forged` 与真实 `tag(target)` 完全一致，`claim` 返回 flag。

## 4. 小结 / 踩坑

- 初看像需要解 9 个未知量（8 个系数 + offset），但 `claim` 只要求 `target` 的 tag，而 `offset` 的系数 `sum(target) ≡ 1` 使其自动抵消，8 次查询足够。
- 非法票据会被拒绝：必须 `1 <= x < P`，且 `sum % P == 1`；单位向量是最省事的合法构造。
- JSON 有防重复键校验（`object_pairs_hook=no_duplicates`），不要发重复字段。
- 会话 60 秒、单次空闲 10 秒超时，脚本需边发边收，不能长时间挂起。
