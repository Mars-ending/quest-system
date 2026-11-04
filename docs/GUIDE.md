# Quest System · 传送门（中文）

**一句话**：自托管的「6 小时任务引擎」——每天一道约 6 小时的高质量任务（数学/物理、算法/代码、AI、英语），做完交卷，由本机 agent **先跑你的代码**再写点评，全部状态落在纯 markdown + git。

> Self-hosted "6-hour task engine": one substantial task per day (math/physics, algorithms/code, AI, English); submissions are auto-reviewed by a local coding agent that actually runs your code; all state lives in plain markdown + git.

## 为什么造这个

课程结束后没人再给你出题，人就容易混沌。这个系统把「出题—计时—交卷—验收—记录」整个循环交给自己的服务器：
- **在架制**：同时只有一道题，做完才发下一道——速度用任务周转表达，不用堆积表达。
- **可验收**：每题带可判定的验收标准（对拍数字/通过的测试/写完的证明）。
- **记录一切**：题目、用时、提交、点评、调整全部进一本 markdown 账本，git 管历史。
- **agent 验收**：交卷后自动触发本机 CLI agent，它跑你的代码、逐条核对、写三段评语、自己登记状态——这条链路已实测。

## 快速开始

```bash
git clone https://github.com/Mars-ending/quest-system.git
cd quest-system
bash scripts/install-jetson.sh     # 目标机：Jetson/Pi 等 Debian 系 SBC
python3 ~/quest/engine.py issue    # 出第一题（W0 主干 · 岭回归的四种面目）
```

网页入口（可选）：把 `web/quest_web.py` 挂进你已有的单文件门户，见 `web/README.md`。

## 仓库结构

```
engine.py / bank.py       引擎（状态机）+ 题库（可替换）
quest_web.py              门户路由钩子（三种接法见 web/README.md）
agent/                    点评与哨兵的 prompt 模板（实测版）
scripts/install-jetson.sh 一键安装到 ~/quest + cron 骨架
data/                     脉络/账本骨架示例（隐私数据不进仓库）
docs/DESIGN.md            设计说明与坑
```

## License

MIT
