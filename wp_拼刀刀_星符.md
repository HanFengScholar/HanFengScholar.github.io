# CTF Writeup：拼刀刀 & 第六十四枚星符

---

## 一、拼刀刀（Reverse · 440 分）

### 1. 题目信息

- **附件**：`KanYiDao.exe`（PE32 控制台程序，32 位，8 个段）
- **靶机**：`nc1.ctfplus.cn 37633`
- **提示**：新人专享的 Flag 礼包到账
- **程序名含义**：KanYiDao = "砍一刀"（拼多多砍价梗）

### 2. 协议初探

直接 `nc` 连上靶机，没有任何 banner 输出。这说明程序是**客户端**——它主动连接服务器并发送请求。

从二进制中提取关键字符串：

```
{"op":"ping"}
{"op":"redeem","lucky_code":"%s","special_code":"%s"}
```

程序只有两个 JSON 操作：`ping` 和 `redeem`。手工模拟协议：

```python
import socket, json
# 通过 HTTP CONNECT 代理连接靶机
s = socket.create_connection(('127.0.0.1', 18080))
s.sendall(b'CONNECT nc1.ctfplus.cn:37633 HTTP/1.1\r\nHost: nc1.ctfplus.cn:37633\r\n\r\n')
# 读取 200 响应头...

# 测试 ping
s.sendall(b'{"op":"ping"}\n')
# 收到: {"ok":true}\n

# 测试 redeem（任意 code）
s.sendall(json.dumps({"op":"redeem","lucky_code":"x","special_code":"y"}).encode()+b'\n')
# 收到: {"ok":false,"error":"INVALID_CODE"}
```

所以核心是：**找到正确的 lucky_code 和 special_code**。

### 3. 逆向分析 code 生成逻辑

`redeem` 函数位于 `0x40b074`，其调用者在 `0x40a6f0`：

```asm
40a6cd:  mov    eax, [ebp+0x8]      ; 全局对象指针
40a6d0:  add    eax, 0x5a           ; lucky_code 来源：对象偏移 0x5a
40a6d6:  lea    edx, [eax+0x66]     ; special_code 来源：对象偏移 0x66
...
40a6f0:  call   0x40b074            ; redeem(obj, lucky_str, special_str, outbuf)
```

继续向上追溯，找到写入偏移 `0x5a` / `0x66` 的逻辑（`0x40aa0c`~`0x40aa50`）：

```asm
; 状态 1（lucky_code）：当金额 == 6 时
40aa12:  cmp    eax, 0x1            ; state == 1?
40aa15:  jne    0x40aa38
40aa17:  mov    eax, [ebp+0x8]
40aa1a:  lea    edx, [eax+0x5a]     ; 写入 lucky_code
40aa1d:  mov    eax, [ebp-0x10]     ; 砍价金额
40aa20:  ...
40aa27:  call   0x40ab48            ; 生成 code
40aa2f:  mov    dword [eax+0x4e], 0x2

; 其他状态（special_code）：当金额 == 1000 时
40aa38:  ...
40aa3b:  lea    edx, [eax+0x66]     ; 写入 special_code
40aa48:  call   0x40ab48
```

关键：金额分别为 **6**（lucky）和 **1000**（special）时生成对应 code。

### 4. Code 编码函数 `0x40ab48`

```asm
40ab4e:  cmp    dword [ebp+0x8], 0x0   ; 金额 <= 0?
40ab52:  je     error
40ab69:  mov    eax, [ebp+0x8]          ; eax = 金额
40ab6c:  xor    eax, 0x13572468         ; 异或魔数
40ab71:  mov    [esp+0x8], eax
40ab75:  mov    [esp+0x4], 0x40e822     ; 格式串 "KD-%08X"
40ab7d:  mov    eax, [ebp+0xc]          ; 输出缓冲区
40ab83:  call   sprintf
```

提取格式串 `0x40e822`：`KD-%08X`

**编码公式**：

```
code = sprintf("KD-%08X", amount ^ 0x13572468)
```

### 5. 计算两个 code

```python
for amount, name in [(6, 'lucky_code'), (1000, 'special_code')]:
    print(name, 'KD-%08X' % (amount ^ 0x13572468))
```

输出：

```
lucky_code   = KD-1357246E   (6  ^ 0x13572468 = 0x1357246E)
special_code = KD-13572780   (1000 ^ 0x13572468 = 0x13572780)
```

### 6. 兑换 Flag

```python
req = json.dumps({"op":"redeem","lucky_code":"KD-1357246E","special_code":"KD-13572780"})
s.sendall(req.encode() + b'\n')
# 收到: {"ok":true,"flag":"SYC{73232585-2c69-44e5-805b-a613337acb60}"}
```

**Flag：`SYC{73232585-2c69-44e5-805b-a613337acb60}`**

### 7. 完整利用脚本

```python
import socket, json

def conn(host, port):
    s = socket.create_connection(('127.0.0.1', 18080), timeout=10)
    s.sendall(f'CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n'.encode())
    resp = b''
    while b'\r\n\r\n' not in resp:
        resp += s.recv(4096)
    s.settimeout(5)
    return s

s = conn('nc1.ctfplus.cn', 37633)
# ping
s.sendall(b'{"op":"ping"}\n')
print(s.recv(4096))
# redeem
lucky   = 'KD-%08X' % (6    ^ 0x13572468)
special = 'KD-%08X' % (1000 ^ 0x13572468)
req = json.dumps({"op":"redeem","lucky_code":lucky,"special_code":special})
s.sendall(req.encode() + b'\n')
print(s.recv(4096))
```

### 8. 关键考点

- 静态逆向定位 JSON 协议与 code 生成函数
- 识别 `xor 0x13572468` + `KD-%08X` 的编码模式
- 无需运行 Windows 程序，直接用 Python 模拟协议拿 flag

---

## 二、第六十四枚星符（Reverse · 502 分）

### 1. 题目信息

- **靶机**：`nc1.ctfplus.cn 38236`
- **提示**：每次连线换星图 / 记住闪烁顺序 / 第六十四枚星符归位
- **核心隐喻**：星空 = 编码字母表，每次连接随机洗牌

### 2. 协议观察

连接后服务器立即返回：

```
flag: +376zUnRn6n3nLtjxaZSK6fFbeN3nM3MbTbOxL+UNa+UHe+DbTbVNJq=
Send text to encode (empty line to quit):
```

这是一个**编码 oracle**：发送任意文本，返回编码结果。目标是解码那个 flag。

### 3. 判断编码类型

发送单个字符测试：

```
'A' (0x41) -> LL==
'B' (0x42) -> L7==
'C' (0x43) -> LW==
0x00       -> HH==  (某次连接)
0x00       -> ee==  (另一次连接)
```

分析：
- 输出以 `=` 结尾 → **base64 家族**
- 1 字节 → 4 字符（2 有效 + `==`），3 字节 → 4 字符，与标准 base64 分组一致
- 不同连接同一输入结果不同 → **字母表每次连接随机洗牌**

结论：**自定义 base64 字母表替换**，结构与标准 base64 完全相同，只是 64 个字符的映射表（"星图"）每次连接随机生成。

### 4. 映射表恢复策略

设 6 位值 `v` 映射到字符 `M[v]`。需要在**同一连接**内获得全部 64 个 `M[v]`。

**构造探测输入**：32 组 × 3 字节 = 96 字节，每组设计为：

```
组 j:  b0 = (2j) << 2,  b1 = 0,  b2 = 2j + 1
```

该组对应的 4 个 6 位值为：

```
v0 = b0 >> 2          = 2j
v1 = (b0&3)<<4 | b1>>4 = 0
v2 = (b1&0xf)<<2 | b2>>6 = 0
v3 = b2 & 0x3f        = 2j + 1
```

所以输出的 128 个字符中：

| 输出位置 | 对应 6 位值 | 含义 |
|---------|-----------|------|
| `4j`     | `2j`      | `M[2j]` |
| `4j+1`   | `0`       | `M[0]`（校验） |
| `4j+2`   | `0`       | `M[0]`（校验） |
| `4j+3`   | `2j+1`    | `M[2j+1]` |

遍历 `j = 0..31` 即可一次性覆盖 `M[0]..M[63]`。

### 5. 解码 Flag

1. 用 `M` 建逆映射 `rev[char] = value`
2. 去掉 flag 编码末尾的 `=`
3. 每个字符查 `rev` 得到 6 位值
4. 拼接所有 6 位为二进制流，按 8 位切分还原字节

### 6. 完整利用脚本

```python
import socket, time

def conn(host, port):
    s = socket.create_connection(('127.0.0.1', 18080), timeout=10)
    s.sendall(f'CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n'.encode())
    resp = b''
    while b'\r\n\r\n' not in resp:
        resp += s.recv(4096)
    s.settimeout(2)
    return s

s = conn('nc1.ctfplus.cn', 38236)
time.sleep(0.5)
# 读 banner 和 flag
data = b''
while True:
    try:
        c = s.recv(4096)
        if not c: break
        data += c
    except socket.timeout: break
banner = data.decode()
flag_enc = [l for l in banner.split('\n') if l.startswith('flag:')][0].split('flag: ')[1].strip()
print('Flag enc:', flag_enc)

# 构造 96 字节探测输入
payload = b''
for j in range(32):
    payload += bytes([(2*j) << 2, 0x00, 2*j + 1])
s.sendall(payload + b'\n')
time.sleep(1.5)
out = b''
while True:
    try:
        c = s.recv(8192)
        if not c: break
        out += c
        if b'encode' in out or b'endlessly' in out: break
    except socket.timeout: break
enc_out = out.decode().split('\n')[0].strip()

# 恢复映射表 M[0..63]
M = {}
for j in range(32):
    M[2*j]     = enc_out[4*j]
    M[2*j + 1] = enc_out[4*j + 3]
rev = {c: v for v, c in M.items()}
assert len(rev) == 64

# 解码 flag
vals = [rev[c] for c in flag_enc.rstrip('=')]
bits = ''.join(f'{v:06b}' for v in vals)
flag = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits)-7, 8))
print('Flag:', flag.decode())
```

### 7. 运行示例（某次连接）

```
Flag enc: AHWhpG1L1h1H1X0qEzcgNhwQT5BH1lHlTCTMEXAGBzAG65A/TCTfB3Y=
Mapping:
 0->u   1->V   2->4   3->h   4->+   5->x   6->5   7->i
 8->0   9->v  10->b  11->E  12->1  13->T  14->N  15->I
16->R  17->r  18->m  19->z  20->A  21->J  22->X  23->3
24->B  25->6  26->2  27->F  28->c  29->j  30->p  31->s
32->w  33->f  34->l  35->C  36->M  37->W  38->9  39->P
40->e  41->8  42->O  43->o  44->U  45->Q  46->7  47->n
48->d  49->g  50->Z  51->k  52->Y  53->H  54->G  55->/
56->L  57->q  58->S  59->a  60->D  61->t  62->y  63->K
Flag: SYC{c80351b9-7188-4f52-b63d-e6a56de763aa}
```

**Flag：`SYC{c80351b9-7188-4f52-b63d-e6a56de763aa}`**

### 8. 关键考点

- 识别 base64 结构特征（`=` padding、字符集大小 64）
- 理解"每次连线换星图" = 字母表按连接随机化，必须在同连接内恢复映射
- 设计**单请求覆盖全部 64 值**的探测输入，绕过服务器请求次数限制
- 映射表逆变换还原明文

### 9. 注意事项

- 服务器有请求次数限制（约 3 次编码请求），所以探测输入必须**一次覆盖全部 64 个值**
- 96 字节输入产生 128 字符输出，需用循环 `recv` 确保读完
- flag 末尾的 `=` 需在解码前去除
- 映射表唯一性校验：`len(rev) == 64`

---

## 两题对比小结

| 维度 | 拼刀刀 | 第六十四枚星符 |
|-----|--------|--------------|
| 题型 | 客户端协议逆向 | 编码 oracle |
| 核心 | 逆向 code 生成算法（xor + 格式化） | 恢复随机化 base64 字母表 |
| 动态性 | code 固定（与连接无关） | 字母表每次连接随机 |
| 交互 | 单次 redeem 请求 | 需在同连接内探测+解码 |
| 难度来源 | 静态逆向定位编码逻辑 | 设计高效的映射表恢复策略 |
