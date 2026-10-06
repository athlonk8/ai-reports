# AI 简报

中英对照的 AI 商业报告阅读站，版式与 [cs.xuyili.com](https://cs.xuyili.com) 相同：顶栏、报告卡片、页内目录、宽屏左右对照。

- 目录：`index.html`
- 总目录：`materials.html`
- State of Markets II：`reports/state-of-markets-ii.html`
- Top 100 第 7 期：`reports/top-100-gen-ai-apps-7.html`

GitHub Pages：`https://athlonk8.github.io/ai-reports/`

## 自定义域名 `reports.xuyili.com`

DNS 托管在 **DNSPod**（NS：`canoeing.dnspod.net`、`cat.dnspod.net`）。仓库根目录的 `CNAME` 已经是 `reports.xuyili.com`，还差 DNSPod 上的一条记录。

在 DNSPod「xuyili.com」→ 记录管理 → 添加记录：

| 字段 | 值 |
| --- | --- |
| 主机记录 | `reports` |
| 记录类型 | `CNAME` |
| 记录值 | `athlonk8.github.io` |
| 线路类型 | 默认 |
| TTL | 600 |

> 记录值结尾**不要**加点号。DNSPod 的 CNAME 记录值与现有 `cs.xuyili.com` 完全一致即可。

顺序很重要：**先加 DNS 记录，再绑自定义域名**。解析还没生效时就把 Pages 的自定义域名填上，Pages 会立刻把流量切到该域名，`github.io` 地址会一起返回 502。

解析生效后：

1. `gh api -X PUT repos/athlonk8/ai-reports/pages -f cname=reports.xuyili.com` 绑定域名
2. 等 Pages 签发证书，再 `gh api -X PUT repos/athlonk8/ai-reports/pages -f cname=reports.xuyili.com -F https_enforced=true` 强制 HTTPS

