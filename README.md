# Quest System

**一句话**：一个自托管的「6 小时任务引擎」——每天一道约 6 小时的高质量任务（数学/物理、算法/代码、AI、英语），做完交卷，由本机 agent 先跑你的代码再写点评，全部状态落在纯 markdown + git，网页可看、手机可交。

> A self-hosted "6-hour task engine": one substantial task per day across math/physics, algorithms/code, AI, and English; submissions are auto-reviewed by a local coding agent that actually runs your code; all state lives in plain markdown + git, exposed through a small authenticated web page.

## 设计原则

1. **在架制**：同时只有一道任务在架，验收通过才发下一道。速度用「任务周转」表达，不用「任务堆积」表达。
2. **可验收**：每题必须带可判定的验收标准（对拍的数字、通过的测试、写完的证明、交付的文章）——「想一想」的题不发。
3. **记录一切**：题目、用时、提交、点评、调整，全部追加进一本 markdown 账本，git 管历史，永不删除。
4. **6h 口径**：任务难度以「熟手研究生专注 6 小时」为基准；实际专注小时 ÷ 6 = 系数，只看各域趋势，不看绝对值。
5. **纯标准库**：引擎与网页扩展只用 Python 标准库（目标设备是 4GB 内存的 Jetson 级 SBC），点评 agent 用系统里已有的任何 OpenAI 兼容 CLI（如 `hermes -z`）。

## 架构

```
┌────────────────────────────────────────────────────────┐
│  数据层（唯一真实源）                                     │
│    quest-log.md   账本：任务块 = 状态机（在架→已交→…）     │
│    quest-map.md   脉络：域 → 分支 → 交叉节点               │
│    timer.json     计时器状态    submissions/ 提交物        │
│    evals/         点评存档      （全部 git 管理）          │
├────────────────────────────────────────────────────────┤
│  引擎层  engine/engine.py                                │
│    state / issue / accept / adjust / set 五个命令         │
│    输出 JSON，供网页与 cron 调用                           │
├────────────────────────────────────────────────────────┤
│  展示层  web/quest_web.py（monkey-patch 进已有门户）       │
│    /quest 总览+交卷+调整   /quest/timer 计时器             │
├────────────────────────────────────────────────────────┤
│  agent 层（可选）                                         │
│    交卷 → 触发本机 CLI agent：跑代码 → 写评语 → 登记状态    │
│    每晚 cron「哨兵」：在架就催，空了按脉络出题              │
└────────────────────────────────────────────────────────┘
```

## 快速开始

```bash
# 在一台有 git 的 Linux 机器上（Jetson/Pi/任何 SBC）
git clone https://github.com/Mars-ending/quest-system.git
cd quest-system
bash scripts/install-jetson.sh          # 装 ~/quest + 门户扩展 + cron 骨架
python3 ~/quest/engine.py state         # 应输出 {"live": [], ...}
python3 ~/quest/engine.py issue         # 出第一题
```

网页扩展依赖一个已有的单文件 Python 门户（只监听 127.0.0.1、带 Basic 鉴权）；
没有门户也可以只用 CLI：`engine.py` 五个命令覆盖全部操作。

## 目录

```
engine/     引擎：账本状态机 + W0 题库（可替换成自己的题库）
web/        门户扩展块 + 集成说明（monkey-patch，不改门户原文件）
agent/      点评与哨兵的 prompt 模板（接任意 OpenAI 兼容 CLI agent）
data/       脉络与账本的示例/骨架（私密数据不进本仓库）
scripts/    一键安装
docs/       设计说明
```

## 隐私模型

本仓库只含**代码与模板**。你的真实账本（做过什么、用时曲线、点评历史）是隐私——
它住在你的服务器上，不进任何公共仓库。`data/` 里的文件只是结构示例。

## License

MIT
