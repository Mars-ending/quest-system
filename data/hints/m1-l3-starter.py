# M1 · L3 起步骨架：病态最小二乘三解法对照
# 用法：pip install numpy mpmath 后 python3 m1-l3-starter.py
# 你的任务：补全法C，把三种解的相对误差打印成表
import numpy as np

rng = np.random.default_rng(0)
U, s0, Vt = np.linalg.svd(rng.standard_normal((200, 50)))
s = np.logspace(0, -8, 50)            # cond(X) = 1e8
X = U[:, :50] @ np.diag(s) @ Vt
w_true = np.ones(50)
y = X @ w_true
lam = 1e-6

# 法A 正规方程（期待：误差最大）
wA = np.linalg.solve(X.T @ X + lam * np.eye(50), X.T @ y)

# 法B 增广 QR（λ‖w‖² 写成 √λ·I 拼进 X 下方——想清楚为什么等价，写进推导）
A = np.vstack([X, np.sqrt(lam) * np.eye(50)])
b = np.concatenate([y, np.zeros(50)])
Q, R = np.linalg.qr(A)
wB = np.linalg.solve(R, Q.T @ b)

# 法C SVD 截断/收缩：自己写 w = V diag(f(s)) V^T
# 提示：收缩因子是 s/(s^2+lam)；对照「硬截断」 s > tau 时的情形
wC = np.zeros(50)  # ← 替换这一行

for name, w in [("normal", wA), ("qr", wB), ("svd", wC)]:
    rel = np.linalg.norm(w - w_true) / np.linalg.norm(w_true)
    print("%-8s rel_err = %.3e" % (name, rel))
