# 网页扩展：怎么接进你的门户

`quest_web.py` 是一个**路由钩子模块**，不是独立服务器。它假设你已有一个
单文件 Python 门户（`http.server` + Basic 鉴权 + 模板函数），并提供了三个接入点。

## 门户必须提供的东西

| 名字 | 形态 | 作用 |
|---|---|---|
| `H` | `BaseHTTPRequestHandler` 子类 | 已有请求处理类 |
| `check_auth(header)` | 函数 → bool | Basic 鉴权判定 |
| `shell(title, body, active)` | 函数 → str | 页面外壳模板 |
| `esc(s)` | 函数 → str | HTML 转义 |
| `self._send(code, body, ctype)` | 方法 | 响应输出 |
| `self._unauth()` | 方法 | 401 响应 |

## 三种接法

### 接法 A · monkey-patch（零改动门户，本机在用）

在门户文件里、`if __name__ == "__main__":` 之前追加：

```python
# ── quest 扩展 ──
_orig_do_GET, _orig_do_POST = H.do_GET, H.do_POST

def _q_do_GET(self):
    u = urlparse(self.path)
    path, q = unquote(u.path), parse_qs(u.query)
    if quest_route_GET(self, path, q):      # True = quest 已处理
        return
    return _orig_do_GET(self)               # 其余走门户原路由

def _q_do_POST(self):
    if quest_route_POST(self, unquote(urlparse(self.path).path)):
        return
    return _orig_do_POST(self)

H.do_GET, H.do_POST = _q_do_GET, _q_do_POST
```

并在文件头 import 区加上：`from quest_web import *`（或把 quest_web.py 内容
直接粘贴进门户文件——本机部署用的就是这种「单文件内联」形态）。

### 接法 B · 直接内联

把 `quest_web.py` 全文粘贴进门户源码尾部（`__main__` 之前），再手工加接法 A
的 6 行 patch。优点：部署还是单文件；缺点：升级要重新粘。

### 接法 C · 只用 CLI，不接网页

不接门户也完全可用：`engine.py` 五个命令 + `cron` 哨兵已覆盖全部操作，
网页只是多一个手机友好的交卷/计时入口。

## 配置（环境变量）

| 变量 | 默认 | 说明 |
|---|---|---|
| `QUEST_DATA` | `~/quest` | 数据目录（账本/提交/点评/计时器） |
| `QUEST_EVAL_CMD` | `hermes -z {prompt}` | 点评命令，`{prompt}` 会被替换 |
| `QUEST_BANK` | `bank` | 题库模块名（engine 目录下） |

## 安全要点

- 全部 `/quest/*` 路由都过 `check_auth`——门户自己的鉴权，不加新凭据。
- 只监听 127.0.0.1，对外经 SSH 反向隧道 + nginx Basic 鉴权（与门户同策略）。
- `/quest/eval/` 查看点评时 `os.path.basename + realpath` 双重夹住，防目录穿越。
- 点评 agent 以普通用户跑、限时（`QUEST_EVAL_TIMEOUT_S`，当前由进程自然退出约束）。

## 可爱主题与题目面板（2026-11-05）

- `theme.css`：整站美化（粉色系、圆角卡片、胶囊按钮、KaTeX 兼容）。追加进门户外壳
  `shell()` 的 `<style>` 里——**f-string 内花括号必须双写**（`{{`），否则 NameError。
- 题目面板 `_qpanel()`：计时页与交卷/调整表单页顶部嵌可折叠题目（`<details>`，KaTeX 渲染）。
  做题时停在计时页，题目一直在——修「开始答题后看不到题目」。
- 注意内联版 `_qlive()` 返回 `(block, text)` 二元组，仓库版返回 str；`_qpanel` 两者兼容。

## Markdown 交卷（2026-11-05）

- 交卷表单的粘贴框带格式下拉（自动识别 / Markdown / 代码 / 纯文本）；文件按
  `q00x-HHMMSS.md` 命名（修掉了旧版 `pasted-pasted-x.txt.txt` 双前缀 bug）。
- 查看页 `/quest/sub/<qid>/<file>`：`.md` 由内置迷你渲染器转 HTML（标题/列表/引用/
  围栏/粗斜体/行内码/链接），公式 `$..$` 原样保留交给 KaTeX；其他文件高亮 `<pre>`。
- 任务总览新增「📂 我的提交」面板列出在架题的提交物。
- KaTeX 注入改为 `shell(..., katex_base=...)` 显式按页面深度传：
  quest 页族 `../`、eval `../../`、sub `../../../`；门户原生页不注入。
  init 脚本 `katex/quest-katex-init.js`（readyState 守卫，defer 三件套：
  katex.min.js → auto-render.min.js → init.js）。

## Markdown 交卷（2026-11-05）

- 交卷表单的粘贴框带格式下拉（自动识别 / Markdown / 代码 / 纯文本）；文件按
  `q00x-HHMMSS.md` 命名（修掉了旧版 `pasted-pasted-x.txt.txt` 双前缀 bug）。
- 查看页 `/quest/sub/<qid>/<file>`：`.md` 由内置迷你渲染器转 HTML（标题/列表/引用/
  围栏/粗斜体/行内码/链接），公式 `$..$` 原样保留交给 KaTeX；其他文件高亮 `<pre>`。
- 任务总览新增「📂 我的提交」面板列出在架题的提交物。
- KaTeX 注入改为 `shell(..., katex_base=...)` 显式按页面深度传：
  quest 页族 `../`、eval `../../`、sub `../../../`；门户原生页不注入。
  init 脚本 `katex/quest-katex-init.js`（readyState 守卫；defer 顺序：
  katex.min.js → auto-render.min.js → init.js，三者缺一不可——漏 auto-render
  会导致 `renderMathInElement is not defined`）。
