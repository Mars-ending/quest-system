# AI1 · L3 起步骨架：通用数值梯度自检
# 用法：float64 + 中心差分；所有参数相对误差 < 1e-6
import numpy as np

def num_grad(f, x, h=1e-5):
    g = np.zeros_like(x)
    it = np.nditer(x, flags=["multi_index"])
    while not it.finished:
        i = it.multi_index
        old = x[i]
        x[i] = old + h; fp = f(x)
        x[i] = old - h; fm = f(x)
        x[i] = old
        g[i] = (fp - fm) / (2 * h)
        it.iternext()
    return g

def rel_err(a, b):
    return np.abs(a - b) / np.maximum(np.maximum(np.abs(a), np.abs(b)), 1e-8)

# 你的任务：实现 layer_norm(x, gamma, beta, eps) 及其对 x/gamma/beta 的解析梯度，
# 然后用 num_grad 对照。Dropout 同理（记得缓存正向 mask）。
print("骨架就位")
