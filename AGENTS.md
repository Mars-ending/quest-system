# AGENTS.md — quest-system 项目上下文

给在这个仓库里工作的 agent（Jetson Hermes / 任何 CLI agent）：动手前先读完。

## 这是什么

自托管「6 小时任务引擎」。数据层 = markdown 账本 + git；引擎 `engine.py`（状态机）
+ `bank.py`（题库，接口 `next_task(items) -> dict | None`）；`web/quest_web.py` 是挂进
已有单文件门户的路由钩子；`agent/` 是点评与哨兵的实测 prompt；`tests/smoke.py` 是验收线。

**线上部署**（改完仓库要同步的地方）：
- 数据本体：Jetson `~/quest/`（真实账本，隐私）
- 网页：Jetson `~/jetson-portal/server.py`（quest 块以内联形式存在，是 `web/quest_web.py` 的展开版）
  改了 web/ 之后：同步内联块 → `python3 -m py_compile` → 重启 portal（kill pidfile 进程再拉起）

## 布局（改哪里）

| 要改什么 | 去哪 |
|---|---|
| 状态机/命令 | `engine.py` |
| 题目内容/新题 | `bank.py`（不动引擎） |
| 网页/路由/计时器 | `web/quest_web.py` + 同步内联块 |
| 出题/点评行为 | `agent/*.txt`（prompt） |
| 设计与坑 | `docs/DESIGN.md`（先读 §5、§8） |

## 铁律

1. **隐私**：`~/quest/quest-log.md`、`evals/`、`submissions/`、`timer.json` 是用户真实数据——绝不复制进本仓库或任何 push；`data/` 里只放编造示例。
2. **测试**：改完必跑 `python3 tests/smoke.py`（全过才算完成）；所有 py 过 `python3 -m py_compile`；sh 过 `bash -n`。
3. **兼容**：目标机 Python 3.8——f-string 不嵌套同类引号、不用 dict `|` 合并、不用 3.9+ 语法。
4. **网页链接一律相对路径**：页面挂在 `/jetson/` 路径前缀反代下，根绝对路径 = 公网 404（教训见 DESIGN.md）。
5. **零依赖**：纯 Python 标准库；不加新监听端口、不动 nginx/隧道。
6. **提交**：一行英文信息、动词开头；直接推 master（个人项目）。

## 常用命令

```bash
python3 tests/smoke.py          # 冒烟（必过）
bash -n scripts/install-jetson.sh
git push                        # core.sshCommand 已配好，直接推
python3 ~/quest/engine.py state # 看线上真实状态（只读）
```
