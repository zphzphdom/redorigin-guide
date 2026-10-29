# 公网部署与 API 接入说明

作品零第三方依赖、单进程、约 120 KB。公网发布有两条路：**临时隧道**（1 分钟，免账号）与 **固定域名**（需要域名或云账号）。

---

## 一、临时公网（评测用，免账号）

### 首选：Cloudflare Quick Tunnel（无警告页、自动 HTTPS）

```powershell
# 二选一获取 cloudflared.exe：
#   a) 官方下载（需能访问 GitHub）
#   b) 镜像下载（本仓库自带脚本，支持断点续传）
python tools\get_cloudflared.py

# 启动（另开一个窗口先跑服务）
python run.py --port 8770
tools\cloudflared.exe tunnel --url http://127.0.0.1:8770 --no-autoupdate
```

输出里会出现 `https://<随机词>.trycloudflare.com`，这就是可直接发给评委的地址：
无账号、无警告页、自动 HTTPS，进程存活期间有效；重启后域名会变。

### 备选：SSH 反向隧道

| 服务 | 命令 | 特点 |
|---|---|---|
| localhost.run | `ssh -R 80:127.0.0.1:8770 nokey@localhost.run` | 无警告页；部分地区/时段可能 502 |
| serveo.net | `ssh -R 80:127.0.0.1:8770 serveo.net` | 稳定，但免费隧道有"Continue to Site"警告页 |

一键脚本：`powershell -ExecutionPolicy Bypass -File deploy\start_public.ps1`（走 localhost.run，断线自动重连）。

> 反向隧道下所有请求源地址都变成 `127.0.0.1`，因此服务端已把限流键改为 `X-Forwarded-For`，
> 并默认关闭免密预览接口（`/api/preview_token` 返回 403，除非设置 `ALLOW_PREVIEW=1`）。

---

## 二、固定域名（正式提交建议）

| 方案 | 需要什么 | 结果 |
|---|---|---|
| Cloudflare 命名隧道 | 一个域名 + Cloudflare 账号（免费） | `https://guide.你的域名` 固定不变 |
| Render / Railway | GitHub 仓库（`deploy/render.yaml` 已备） | `https://<name>.onrender.com` 固定 |
| 自有服务器 | 一台云主机（国内需备案） | 完全可控，可挂 SSL 与访问策略 |

Cloudflare 命名隧道：

```powershell
cloudflared tunnel login
cloudflared tunnel create redorigin
cloudflared tunnel route dns redorigin guide.example.com
cloudflared tunnel run --url http://127.0.0.1:8770 redorigin
```

> **关于"挂在 deepseek.com 下"**：DeepSeek 开放平台目前只提供 API（对话 / Search / Fetch）
> 与用量管理，没有面向第三方的智能体托管与发布入口，因此无法把作品发布到 deepseek.com 的固定网址下。
> 能做到"固定网址"的只有上面三种自建托管方式。

---

## 三、接入 DeepSeek API（联网实时生成）

配置任意一种即可，**改完重启服务生效**：

```powershell
# 方式 1：环境变量
$env:DEEPSEEK_API_KEY="sk-..."
python run.py --port 8770
```

```json
// 方式 2：data/config.json（复制 config.example.json）
{ "api_key": "sk-...", "model": "deepseek-flash", "base_url": "https://api.deepseek.com" }
```

启用后：

- 讲解/政策/农品类回答由 `deepseek-flash` 基于知识库重写，必须带 `[S1]` 引用；
- 遇到"最新/今天/开通/天气"等时效问题，自动调用官方 **Search API**（`/v1/tools/search`）补实时结果；
- 票价、开放时间等**结构化信息仍用本地官方表**，不让模型改写数字；
- 任何 4xx/5xx/超时都自动回退到本地规则，页面会标注"接口异常，已回退"。

计费参考（官方）：Search / Fetch 各 5 元每 1000 次成功请求；对话按 token 计费。
模型名：`deepseek-flash`（默认）或 `deepseek-v4-pro`。

关闭：设 `REDORIGIN_LLM=0` / `REDORIGIN_SEARCH=0`，或删除 key。

---

## 上线前检查清单

- [ ] `/health` 返回 `{"ok": true}`
- [ ] `/api/config` 显示的 `mode` 符合预期（离线评审应为 `offline-rules`）
- [ ] 未登录访问 `/api/admin/stats` 返回 401
- [ ] `/api/preview_token` 返回 403
- [ ] 评审账号能登录、对话、生成行程
- [ ] `docs/PUBLIC_URL.txt` 与 PDF/PPT 中的链接一致
- [ ] 评审结束停止隧道/下线实例，撤销测试用 API key

## 已知限制

- 数据存内存 + JSON 文件，多实例部署时日志与反馈不共享（单实例设计）；
- 免费隧道会休眠或断开，正式评审建议用固定域名方案；
- API 模式下首次回答约 1–3 秒（取决于网络与模型），离线模式为毫秒级。
