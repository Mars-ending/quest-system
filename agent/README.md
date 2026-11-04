# 点评 agent 与哨兵

系统的「验收人」和「出题人」都是本机 CLI agent（任何 OpenAI 兼容 CLI 都能接）。
这里放的是经过实测的 prompt 模板与接线方式。

## 角色 1 · 点评 agent（交卷时触发）

触发：`web/quest_web.py` 在交卷成功后自动调用 `QUEST_EVAL_CMD`。
模板：`eval-prompt.txt`（变量 `{qid}` `{engine}` `{block}`）。

实测过的行为（Jetson + hermes/deepseek）：
- 真的会去跑提交的代码，环境缺依赖会在评语里写明；
- 逐问核对题目四要素，缺失项逐条指出；
- 给「下一题走哪条支」的判词；
- 自己调用 `engine.py set` 登记状态（完成 / 退回在架），评语写进账本。

## 角色 2 · 哨兵（每晚 cron）

职责：读引擎状态 → 在架就重发题目+挂起天数（≥3 天加催办）；空了就按脉络出题
（先跑 `engine.py issue`，骨架题由出题 agent 按 quest-map 展开）；周日不出新题。
模板：`sentinel-prompt.txt`。

cron 接线（Jetson 本机，系统 crontab）：

```cron
5 21 * * * cd ~/quest && python3 scripts/sentinel.py >> ~/quest/sentinel.log 2>&1
```

`scripts/sentinel.py` 只是壳：组装 prompt → 调 `QUEST_SENTINEL_CMD`（默认
`hermes -z {prompt}`）→ 输出落日志。真正的判断在 prompt 里（读账本、守规则），
换 agent 只换一条环境变量。

## 隔离与安全

- agent 跑在数据目录（`cwd=QUEST_DATA`），只给它账本和提交物；
- prompt 里明确「验收要跑代码」，但没有给任何 sudo/网络授权；
- 点评输出落 `evals/`，网页查看时做了路径穿越防护。
