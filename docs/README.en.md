# Quest System

**A self-hosted "6-hour task engine"** — one substantial task per day (math/physics, algorithms/code, AI, English); submissions are auto-reviewed by a local coding agent that **actually runs your code**; all state lives in plain markdown + git.

自托管「6 小时任务引擎」中文说明见 [docs/GUIDE.md](docs/GUIDE.md)。

## Why

After coursework ends, nobody hands you problems anymore — and that's where the drift starts. This system hands the whole loop (issue → timer → submit → review → record) to your own server:

- **One task on the rack**: nothing new until the current one is accepted. Speed shows up as task turnover, not backlog.
- **Verifiable**: every task ships with checkable acceptance criteria (numbers to match, tests to pass, a proof to complete).
- **Everything is recorded**: tasks, hours, submissions, reviews, adjustments — one markdown ledger, git-tracked, append-only.
- **Agent-reviewed**: on submit, a local CLI agent is spawned; it runs your code, checks the derivation line by line, writes a 3-part review, and updates the ledger itself. (This chain is tested end-to-end.)

## Quick start

```bash
git clone https://github.com/Mars-ending/quest-system.git
cd quest-system
bash scripts/install-jetson.sh     # target: Jetson/Pi or any Debian-ish SBC
python3 ~/quest/engine.py issue    # first task (W0 · Ridge Regression, Four Faces)
```

Web UI (optional): hook `web/quest_web.py` into your existing single-file portal — see [web/README.md](web/README.md).

## Layout

```
engine.py, bank.py    state machine + question bank (swappable)
quest_web.py          portal route hooks (3 integration options)
agent/                battle-tested prompts for reviewer & sentinel
scripts/              installer + cron shell
data/                 ledger/map skeletons (no private data)
docs/                 GUIDE (中文) + DESIGN notes & pitfalls
```

## Privacy

This repo contains **code and templates only**. Your real ledger (what you did, hour curves, reviews) lives on your server and never enters a public repo. Files in `data/` are fabricated examples.

## License

MIT
