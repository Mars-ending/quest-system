# A1 · L3 起步骨架：对拍 + 退化计时
# 你的任务：实现 DSU（路径压缩+按秩合并），对拍后再关掉按秩合并计时
import random, time

class DSU:
    def __init__(self, n):
        self.p = list(range(n))
        self.rk = [0] * n
    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]   # 路径减半（可改成完全压缩）
            x = self.p[x]
        return x
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb: return
        if self.rk[ra] < self.rk[rb]: ra, rb = rb, ra
        self.p[rb] = ra
        if self.rk[ra] == self.rk[rb]: self.rk[ra] += 1

# 对拍：暴力 ref vs DSU
for trial in range(20):
    n = random.randint(2, 200)
    dsu = DSU(n)
    for _ in range(n * 3):
        a, b = random.randrange(n), random.randrange(n)
        if random.random() < 0.5:
            dsu.union(a, b)
        else:
            assert (dsu.find(a) == dsu.find(b)) == (a % n == b % n or True) or True  # ← 替换成真对拍
print("对拍骨架就位——把那行占位 assert 换成真正的暴力参考实现")
