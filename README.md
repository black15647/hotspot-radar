# 📡 环境学子雷达

> 面向环境专业学生的开源热点聚合平台 —— 每日自动聚合 15+ 权威信息源，用透明的热度算法为你筛选最值得关注的环境领域资讯。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Pages](https://img.shields.io/badge/Deploy-GitHub%20Pages-blue.svg)](https://pages.github.com/)

---

## ✨ 功能特性

- **每日热点榜单**：自动聚合 Google News、The Guardian、Yale Environment 360、BBC、Nature、Water Research、ScienceDaily 等 15+ 权威信息源
- **透明热度算法**：基于来源权重、关键词匹配、主题聚合、时间衰减的可解释评分体系
- **智能分析**：每条热点自动生成一句话分析，说明热度驱动因素和关注建议
- **关键词标签云**：直观展示当日热门环境专业概念
- **历史趋势曲线**：近 7 天资讯数量趋势 + 任意关键词 365 天热度追踪
- **历史归档**：按年月浏览历史热点，可回溯任意日期的 Top10 榜单
- **环境知识库**：内置 100+ 环境专业术语解释，支持搜索、分类筛选、推荐词条
- **自动提取新词**：使用 jieba 分词从每日热点中提取候选新词，生成 `pending_terms.json` 供知识库维护
- **个性化过滤**：支持自定义用户关键词，生成专属热点列表
- **我的收藏**：收藏感兴趣的热点，按热度排序展示，数据保存在本地浏览器
- **AI 智能摘要**：基于英伟达 NIM (z-ai/glm-5.2) 批量生成热点摘要，支持原文提取和 Jina Reader 兜底
- **英文内容翻译**：内置环境专业英中词表 + MyMemory 免费翻译 API，英文热点也能生成中文关键词
- **近 7 天热词统计**：从每日快照中统计实际高频词，写入 `weekly_keywords` 字段，趋势图联动展示
- **近 7 天热度总结**：基于实际高频词 AI 生成总结，失败自动降级为规则总结
- **批量 API 调用**：所有 AI 处理合并为批量请求，每天最多 3 次 API 调用，大幅降低 429 限流风险
- **热度明细展示**：点击热度分数查看计算明细（来源权重、关键词匹配、时间衰减等）
- **RSS 源健康度**：实时监控每个 RSS 源的抓取状态，连续失败自动标记并邮件通知
- **个人知识库自动记录**：每日热点自动追加到 `personal_knowledge.md`，积累个人学习笔记
- **今日焦点模块**：醒目展示当天最重要的 1-2 条热点
- **30 天热点时间线**：展示过去 30 天每天热度最高的关键词变化
- **"为什么是热点"一键生成**：基于热度构成生成自然语言解释
- **快速分享网站**：支持系统分享或复制链接，一键分享给同学
- **知识库词条关联热点**：查看词条释义时同时展示相关热点条目
- **主题定制增强**：支持文字颜色、字体选择、圆角、密度、字号等全面定制
- **移动端底部导航**：移动端固定底部 Tab 栏，快速切换热点、知识库、趋势、收藏
- **微交互动画**：按钮缩放、卡片悬停、模态框淡入淡出、收藏弹跳等流畅动画
- **骨架屏加载**：数据加载期间显示骨架屏占位，提升用户体验
- **回到顶部按钮**：页面滚动超过 300px 时显示，一键回到顶部
- **SEO 优化**：完整的 meta 标签、Open Graph 标签、sitemap.xml，提升搜索引擎收录
- **热点详情展开**：点击标题展开完整摘要和分析，支持"阅读原文"和"代理访问"（Google 翻译代理）
- **主题定制 UI**：主色、背景色、圆角、密度、字体大小自由调节，实时预览
- **暗黑模式**：一键切换，护眼舒适
- **一键分享**：支持系统分享面板 / 复制链接，快速转发热点
- **用户反馈**：通过 GitHub Issues 提交反馈，无需后端服务器
- **邮件推送**：每日报告自动发送至站长个人邮箱（可选）
- **赞赏支持**：集成爱发电按钮，支持作者持续维护
- **GitHub Pages 部署**：纯静态站点 + GitHub Actions 自动更新，零成本运行

### v5.0 新增功能

- **主题定制增强**：新增文字颜色选择器和字体选择（系统默认/无衬线/衬线/等宽），所有设置实时生效并保存到 localStorage
- **今日焦点模块**：今日热点列表上方醒目展示热度最高的 1-2 条热点，大标题+强调色边框
- **卡片信息密度分层**：标题加大加粗、摘要默认2行省略、热度分数彩色标签（高/中/低）、次要信息弱化
- **关键词详情模态框**：点击关键词标签弹出详情，包含今日相关热点、知识库解释、365天热度趋势图
- **关注关键词**：可关注感兴趣的关键词，在今日热点顶部显示关注标签，点击快速过滤
- **RSS 源健康度面板**：实时监控所有 RSS 源状态（成功/失败/耗时/条数），连续失败标记为 critical，邮件通知站长
- **30天热点时间线**：支持7/14/30天时间范围切换，展示每日热门关键词变化，点击日期查看相关热点
- **"为什么是热点"一键生成**：每条热点可生成自然语言解释，说明热度驱动因素（来源/关键词/时间）
- **知识库词条关联热点**：查看词条释义时同时显示相关热点列表，桌面端左右布局，移动端上下布局

### v6.0 新增功能

- **热度分数明细**：点击热点卡片的热度分数，弹出明细弹窗，展示基础分、来源权重分、关键词匹配分、时间新鲜度分、主题聚合加分和总分
- **基于原文的 AI 摘要生成**：当条目摘要为空或不完整时，自动提取原文正文（readability-lxml + html2text 本地提取，Jina Reader 兜底），调用英伟达 NIM (z-ai/glm-5.2) 生成不超过50字的中文摘要
- **近7天热度总结**：AI 生成近7天热点趋势总结，展示在左侧悬浮卡片，API 不可用时自动降级为规则总结
- **AI 热门关键词提取**：调用英伟达 NIM 从热点条目中提取环境领域相关的具体关键词，避免泛化标签，合并到关键词统计和标签云
- **话题标签 topic_tags**：为每条热点生成1-3个具体话题标签，用于优化 analysis 分析字段，让分析更贴近内容
- **个人知识库自动记录**：每次运行自动将当天热点数据（高频关键词、Top10热点、候选新词）追加到 `personal_knowledge.md`，重复运行自动替换当天内容
- **RSS 源更新优化**：删除失效源，新增验证通过的稳定源（Science、PNAS环境科学、Environmental Research Letters、IISD SDG、Berkeley Earth、Adaptation Fund等），最终22个源
- **快速分享网站**：导航栏增加分享网站按钮，移动端调起系统分享，桌面端复制链接
- **移动端底部导航栏**：宽度小于640px时显示固定底部Tab（热点/知识库/历史/收藏）
- **回到顶部按钮**：滚动超过300px时显示，点击平滑回到顶部
- **骨架屏加载**：数据加载期间显示3个骨架屏占位卡片，提升感知性能
- **微交互动画**：按钮点击缩放、卡片悬停上浮、模态框缩放淡入、收藏按钮弹跳、关键词标签脉冲、卡片依次渐入
- **减弱动态效果支持**：尊重系统 `prefers-reduced-motion` 设置，自动禁用大部分动画
- **favicon**：新增绿色叶子雷达图标，解决浏览器 favicon 404
- **百度统计集成**：预留百度统计脚本位置，替换 ID 即可启用网站访问统计
- **自动备份与失败通知**：每日自动备份关键数据到 GitHub Release，工作流失败时通过 ntfy.sh 推送通知
- **代码模块化重构**：后端函数职责单一，便于维护和扩展
- **单元测试**：25个测试用例覆盖摘要清洗、关键词匹配、热度计算、JSON生成等核心功能

---

## 🚀 快速开始（5 分钟部署到 GitHub Pages）

### 第一步：Fork 本仓库

点击右上角的 **Fork** 按钮，将项目复制到你的 GitHub 账号下。

### 第二步：启用 GitHub Pages

1. 进入你 Fork 的仓库 → **Settings** → **Pages**
2. 在 **Build and deployment** 中，Source 选择 **Deploy from a branch**
3. Branch 选择 **main**，文件夹选择 **/docs**，点击 **Save**
4. 等待几分钟，你的站点将在 `https://<你的用户名>.github.io/hotspot-radar/` 上线

### 第三步：触发首次数据生成

1. 进入仓库的 **Actions** 标签页
2. 找到 **Daily Hotspot Report** 工作流
3. 点击 **Run workflow** 手动触发一次，生成初始数据

完成！你的环境学子雷达已经上线 🎉

---

## ⚙️ 配置说明

### `config.yaml` 详细说明

项目根目录下的 `config.yaml` 是唯一需要修改的配置文件。

#### 最小配置模板

```yaml
# 只需填写 rss_feeds 即可运行，其余字段均有默认值
site_name: "环境学子雷达"

rss_feeds:
  "Google News 环境保护": "https://news.google.com/rss/search?q=环境保护&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
  # ... 更多源
```

#### 可选字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `site_name` | string | "环境学子雷达" | 站点名称 |
| `keywords` | list | 内置 33 个环境关键词 | 用于热度计算和标签云的关键词列表 |
| `user_keywords` | list | 空 | 用户个性化关键词，填写后生成 `personal_latest.json` |
| `weights.source_weights` | dict | Nature 2.0 / Google News 1.5 / 其他 1.0 | 各来源的权重 |
| `weights.time_decay` | float | 0.8 | 时间衰减系数 |
| `weights.keyword_bonus` | float | 2.0 | 每个匹配关键词的加分 |
| `email_config.smtp_server` | string | 空 | SMTP 服务器地址（如 smtp.qq.com） |
| `email_config.smtp_port` | int | 465 | SMTP 端口 |
| `email_config.sender` | string | 空 | 发件人邮箱 |
| `email_config.password` | string | 空 | 发件人授权码 |
| `email_config.receiver` | string | 空 | 收件人邮箱（站长个人），为空则不发送 |
| `summary_api.enabled` | bool | false | 是否启用 AI 摘要生成和关键词提取 |
| `summary_api.api_key` | string | 空 | 英伟达 NIM API Key（也可通过环境变量 NVIDIA_API_KEY 设置，在 https://build.nvidia.com 注册获取） |
| `summary_api.model` | string | z-ai/glm-5.2 | 英伟达 NIM 模型名称 |
| `summary_api.base_url` | string | https://integrate.api.nvidia.com/v1/ | API 基础地址 |
| `summary_api.max_tokens` | int | 150 | 生成摘要的最大 token 数 |
| `reader_api.enabled` | bool | true | 是否启用原文提取 |
| `reader_api.local_extraction` | bool | true | 是否使用 readability-lxml + html2text 本地提取 |
| `reader_api.jina_api_key` | string | 空 | Jina Reader API Key（也可通过环境变量 JINA_API_KEY 设置） |
| `reader_api.jina_base_url` | string | https://r.jina.ai/ | Jina Reader 基础地址 |
| `max_items_per_source` | int | 5 | 每个源最大抓取条数（冷启动自动设为 10） |
| `max_total_items` | int | 50 | 总条目上限 |

#### 添加自定义 RSS 源

在 `rss_feeds` 中添加一行即可：

```yaml
rss_feeds:
  "我的自定义源": "https://example.com/rss.xml"
```

#### 维护环境知识库

项目内置 100+ 环境专业术语，存储在 `docs/data/glossary.json` 中。

**自动提取新词**：脚本每日运行时会使用 jieba 分词从热点标题中提取候选新词，生成 `docs/data/pending_terms.json`，格式如下：

```json
[
  {"term": "碳关税", "count": 3, "contexts": ["欧盟碳关税正式通过", "碳关税影响出口"]},
  {"term": "无废城市", "count": 2, "contexts": ["多地推进无废城市建设"]}
]
```

**手动收录新词**：
1. 查看 `pending_terms.json` 中的候选词
2. 将合适的词条添加到 `glossary.json`，格式为 `{"term": "xxx", "definition": "xxx", "category": "xxx"}`
3. 提交并推送，前端会自动加载更新后的知识库

---

## 📐 热度算法说明

### 计算公式

```
热度 = 5 + 来源权重 × 3 + 关键词匹配数 × 关键词加分 + 主题聚合加分 + 10 × e^(-小时数/24)
```

### 各项详解

1. **基础分（5 分）**：保证每条资讯有基础热度，避免零分。

2. **来源权重加分**：
   - Nature 系列（Nature / Nature Sustainability / Nature 环境科学）：权重 2.0 → 加 6 分
   - Google News 系列：权重 1.5 → 加 4.5 分
   - 其他来源：权重 1.0 → 加 3 分

3. **关键词匹配加分**：每匹配一个环境专业关键词加 `keyword_bonus`（默认 2.0）分。

4. **主题聚合加分**：同一关键词在多条资讯的标题/摘要中出现时，每条包含该关键词的资讯额外加 `2 × 包含该关键词的条目数` 分。这使得真正的热点话题能获得更高热度。

5. **时间衰减加分**：`10 × e^(-小时数/24)`，越新的资讯加分越高。1 小时前约 9.6 分，24 小时前约 3.7 分，48 小时前约 1.4 分。

### 数据范围

- 仅保留最近 **48 小时**内发布的资讯
- 发布时间缺失的条目按当前时间减 24 小时处理
- 每天 UTC 00:00（北京时间 08:00）自动更新

---

## 💬 配置反馈功能

本项目使用 **GitHub Issues** 处理用户反馈，无需第三方服务，无需自建后端。

### 配置步骤

1. **打开 `docs/index.html`**，找到反馈按钮的链接：

   ```html
   <a href="https://github.com/你的用户名/你的仓库名/issues/new?title=网站反馈&body=请描述你的建议或问题：" target="_blank">💬 反馈</a>
   ```

2. **替换占位符**：将 `你的用户名` 和 `你的仓库名` 替换为你的 GitHub 用户名和仓库名。

3. **提交并推送**：将修改推送到 GitHub，反馈功能即可生效。

用户点击反馈按钮后，会在新标签页打开 GitHub Issues 创建页面，标题和正文已预填，用户只需补充具体内容即可提交。

---

## ☕ 赞助说明

本项目完全免费开源，采用 MIT 协议。如果你觉得这个项目对你有帮助，欢迎通过以下方式支持作者：

- **爱发电**：[https://afdian.com/](https://afdian.com/)（站点底部"支持作者"按钮）
- **GitHub Star**：给本仓库点个 Star ⭐
- **分享传播**：推荐给身边的环境专业同学和老师

你的支持是我持续维护的动力！

---

## 🛠️ 本地开发指南

### 环境要求

- Python 3.10+
- pip

### 安装依赖

```bash
pip install feedparser pyyaml jieba readability-lxml html2text requests
```

> jieba、readability-lxml、html2text 为可选依赖，未安装时对应功能会自动跳过，不影响其他功能。

### GitHub Secrets 配置（启用 AI 功能）

如果需要启用 AI 摘要生成和关键词提取功能，需要在 GitHub 仓库中配置以下 Secrets：

1. 进入仓库 Settings → Secrets and variables → Actions
2. 点击 "New repository secret"
3. 添加以下 Secrets：
   - `NVIDIA_API_KEY`：英伟达 NIM API Key（在 https://build.nvidia.com 注册获取，免费层有 40 RPM 额度）
   - `JINA_API_KEY`：Jina Reader API Key（在 https://jina.ai 注册获取，可选，用于原文提取兜底）

配置后，GitHub Actions 运行时会自动注入这些环境变量。也可以在本地通过环境变量设置：

```bash
# Windows PowerShell
$env:NVIDIA_API_KEY="your_api_key"
$env:JINA_API_KEY="your_api_key"
python daily_report.py
```

> 未配置 API Key 时，AI 功能自动禁用，系统使用规则生成摘要和关键词，不影响正常运行。

### 本地运行数据生成

```bash
python daily_report.py
```

运行后会在 `data/` 目录下生成：
- `latest.json` — 今日热点完整数据
- `daily_report.md` — Top 10 可读报告
- `history.json` — 历史记录
- `history.csv` — 历史记录 CSV
- `personal_latest.json` — 个性化热点（配置了 `user_keywords` 时）

### 本地预览网站

由于前端使用 `fetch` 加载本地 JSON 文件，直接用浏览器打开 `docs/index.html` 会遇到跨域问题。建议使用本地 HTTP 服务器：

```bash
# Python 内置服务器
cd docs
python -m http.server 8000
```

然后访问 `http://localhost:8000` 即可预览。

### 运行单元测试

项目包含 25 个单元测试用例，覆盖摘要清洗、关键词匹配、热度计算、JSON 生成等核心功能。

```bash
# 运行所有测试（详细输出）
python -m unittest test_daily_report.py -v

# 或直接运行
python test_daily_report.py
```

测试文件：`test_daily_report.py`，使用 Python 标准库 `unittest`，无需额外依赖。

### 自动备份功能说明

GitHub Actions 工作流每日运行时会自动执行以下备份操作：

1. **打包备份文件**：将 `docs/data/history.csv`、`docs/data/glossary.json`、`docs/data/learning_path.json` 打包为 zip
2. **上传到 GitHub Release**：使用 `softprops/action-gh-release@v2` 将 zip 上传到名为 `backup` 的 Release（tag 为 `backup`），每次运行覆盖最新备份
3. **失败通知**：如果工作流失败，会通过 ntfy.sh 发送推送通知（需将 `your-topic` 替换为你自己的 ntfy 主题）

备份文件可在仓库的 **Releases** 页面下载，tag 为 `backup`。

### 百度统计配置

项目已预留百度统计脚本位置，在 `docs/index.html` 的 `</head>` 之前。配置步骤：

1. 登录 [百度统计](https://tongji.baidu.com)，添加网站获取统计 ID
2. 打开 `docs/index.html`，找到 `BAIDU_TONGJI_ID` 占位符
3. 替换为你的真实统计 ID
4. 提交并推送，部署后即可在百度统计后台查看访问数据

本地测试：打开浏览器控制台 → Network 标签，刷新页面，查看是否有 `hm.baidu.com` 的请求。

### 项目结构

```
hotspot-radar/
├── config.yaml                  # 配置文件（唯一需修改）
├── daily_report.py              # 每日报告生成脚本
├── test_daily_report.py         # 单元测试（25个测试用例）
├── .github/
│   └── workflows/
│       └── main.yml             # GitHub Actions 自动更新 + 备份 + 通知
├── docs/
│   ├── index.html               # 主页面
│   ├── style.css                # 样式表
│   ├── script.js                # 前端脚本
│   ├── favicon.svg              # 网站图标
│   └── data/                    # 生成的数据（自动更新）
│       ├── latest.json          # 今日热点完整数据
│       ├── daily_report.md      # Top10 可读报告
│       ├── history.json         # 历史记录（含关键词计数）
│       ├── history.csv          # 历史记录 CSV
│       ├── source_health.json   # RSS 源健康度
│       ├── personal_latest.json # 个性化热点（可选）
│       ├── pending_terms.json   # 候选新词
│       ├── glossary.json        # 环境知识库（100+ 术语）
│       ├── learning_path.json   # 学习路径数据
│       ├── daily/               # 每日 Top10 快照
│       │   └── YYYY-MM-DD.json
│       └── archive/             # 月度归档
│           └── YYYY-MM.json
└── README.md
```

---

## 📝 更新日志

### v7.1（最新）

- 🔄 **AI 模型切换为英伟达 NIM**：从智谱 GLM 切换为英伟达 NIM (`z-ai/glm-5.2`)，API 地址为 `https://integrate.api.nvidia.com/v1/`
- 🚀 **调用次数放宽**：英伟达免费层有 40 RPM 额度，每天调用 20-30 次完全没问题，不再限制为每天 3 次
- ✨ **话题标签改为逐条生成**：对 Top 10 条热点逐条调用 AI 生成话题标签，标签更准确、更贴合内容（串行执行，不并发）
- 🔧 **环境变量更新**：从 `ZHIPU_API_KEY` 改为 `NVIDIA_API_KEY`，GitHub Secrets 同步更新
- 🔧 **重试退避策略保留**：429/超时重试 3 次，等待 5/10/15 秒，失败自动降级为规则生成
- 📚 **所有功能保持不变**：RSS 抓取、热度计算、源健康度、个人知识库、英文翻译、近7天总结、批量摘要、关键词提取等功能完整保留

### v7.0

- ✨ 新增**英文内容翻译功能**：内置 70+ 环境专业英中词表 + MyMemory 免费翻译 API，英文热点也能生成中文关键词
- ✨ 新增**近 7 天热词统计**：从每日快照中统计实际高频词，写入 `weekly_keywords` 字段，前端趋势图联动展示
- ✨ 优化**近 7 天热度总结**：基于实际高频词 AI 生成总结，失败自动降级为规则总结，不再使用预设宽泛词
- 🔧 修复**AI 模型切换为英伟达 NIM**：从智谱 GLM 切换为英伟达 NIM (z-ai/glm-5.2)，免费层 40 RPM 额度充足，调用次数已放宽（逐条生成话题标签 + 批量摘要 + 关键词提取），不再有 429 限流困扰
- 🔧 优化**批量话题标签生成**：英文内容先翻译为中文再提取，禁止返回宽泛词，优先提取具体事件、地点、物质、技术、政策名称
- 🔧 优化**原文提取**：更真实的请求头、特定反爬域名自动跳过、失败域名去重日志，减少 403 错误和日志刷屏
- 🔧 优化**话题标签降级**：AI 失败时从标题提取具体关键词，兜底为"环境动态"而非"环境领域"
- 📊 前端趋势图升级：从单条"资讯条数"改为展示前 3 个高频词的近 7 天热度变化曲线

### v6.0

- ✨ 新增**热度分数明细**：点击热度分数弹出明细弹窗，展示各项得分和总分
- ✨ 新增**基于原文的 AI 摘要生成**：readability-lxml + html2text 本地提取，Jina Reader 兜底，英伟达 NIM 生成摘要
- ✨ 新增**近7天热度总结**：AI 生成趋势总结，左侧悬浮卡片展示，自动降级为规则总结
- ✨ 新增**AI 热门关键词提取**：英伟达 NIM 提取环境领域具体关键词，避免泛化标签
- ✨ 新增**话题标签 topic_tags**：每条热点生成1-3个具体标签，优化 analysis 分析
- ✨ 新增**个人知识库自动记录**：每日热点自动追加到 personal_knowledge.md
- 🔧 优化**RSS 源**：删除失效源，新增 Science、PNAS、ERL、IISD、Berkeley Earth、Adaptation Fund 等稳定源
- 🔧 优化**GitHub Actions**：增加 readability-lxml、html2text、requests 依赖，注入 NVIDIA_API_KEY、JINA_API_KEY 环境变量，提交 personal_knowledge.md

### v5.0

- ✨ 新增**主题定制增强**：文字颜色选择器、字体选择（系统默认/无衬线/衬线/等宽）
- ✨ 新增**今日焦点模块**：醒目展示热度最高的 1-2 条热点
- ✨ 新增**卡片信息密度分层**：标题加大、摘要2行省略、热度彩色标签、次要信息弱化
- ✨ 新增**关键词详情模态框**：今日相关热点 + 知识库解释 + 365天趋势图
- ✨ 新增**关注关键词**功能，关注标签显示在热点顶部，点击快速过滤
- ✨ 新增**RSS 源健康度面板**，实时监控源状态，连续失败标记 critical 并邮件通知
- ✨ 新增**30天热点时间线**，支持7/14/30天切换，点击日期查看相关热点
- ✨ 新增**"为什么是热点"一键生成**，自然语言解释热度驱动因素
- ✨ 新增**知识库词条关联热点**，查看释义时同时显示相关热点
- ✨ 新增**快速分享网站**按钮，移动端系统分享，桌面端复制链接
- ✨ 新增**移动端底部导航栏**（热点/知识库/历史/收藏）
- ✨ 新增**回到顶部按钮**、**骨架屏加载**、**favicon 图标**
- ✨ 新增**微交互动画**：按钮缩放、卡片上浮、模态框动画、收藏弹跳、卡片渐入
- ✨ 新增**减弱动态效果支持**，尊重系统 `prefers-reduced-motion`
- ✨ 新增**百度统计集成**（预留位置，替换 ID 即可启用）
- ✨ 新增**自动备份**（GitHub Release）和**失败通知**（ntfy.sh）
- ✨ 新增**单元测试**（25个测试用例）和**代码模块化重构**
- 🔧 关键词标签点击改为打开关键词详情模态框（原趋势图功能保留在详情内）
- 🔧 后端增加源健康度记录 `source_health.json`，邮件通知附加 critical 源警告
- 📱 全面优化移动端体验：工具栏堆叠、底部导航、按钮≥44px、图表自适应

### v4.1

- ✨ 新增**我的收藏**功能，收藏感兴趣的热点，按热度排序展示，数据本地保存
- ✨ 新增**环境知识库**，内置 100+ 环境专业术语解释，支持搜索、分类筛选、推荐词条
- ✨ 新增**自动提取新词**，使用 jieba 分词从每日热点中提取候选新词，生成 `pending_terms.json`
- ✨ 新增**历史归档**功能，按年月浏览历史热点，可回溯任意日期的 Top10 榜单
- ✨ 新增**热点详情展开**，点击标题展开完整摘要和分析，支持"阅读原文"和"代理访问"
- ✨ 新增**智能分析**，每条热点自动生成一句话分析，说明热度驱动因素
- ✨ 新增**代理访问**按钮，通过 Google 翻译代理访问外文原文
- ✨ 新增**知识库搜索建议**，输入时实时显示匹配词条下拉列表
- 🔧 反馈功能改为 GitHub Issues，无需第三方服务
- 🔧 修复前端 JS null 引用导致页面一直加载的问题
- 🔧 优化摘要提取逻辑，取消 300 字符截断，优先提取 content 字段
- 🔧 修复关键词统计，只统计配置列表中的关键词，不统计所有英文单词
- 📱 改进暗黑模式和响应式适配

### v3.1

- ✨ 新增**用户反馈**功能，通过 Formspree 发送邮件，无需后端
- ✨ 新增**一键分享**功能，支持系统分享面板 / 复制链接
- 🎨 优化卡片布局，分享按钮小巧不占空间
- 📱 改进移动端响应式体验
- 🐛 修复若干小问题

### v3.0

- ✨ 新增**主题定制面板**：主色、背景色、圆角、密度、字体大小自由调节
- ✨ 新增**暗黑模式**，一键切换并保存偏好
- ✨ 新增**关键词历史曲线**：点击任意标签查看 365 天热度趋势
- 📊 优化热度算法，引入主题聚合加分
- 🔧 改进冷启动逻辑，首次运行自动回填 7 天历史

### v2.0

- ✨ 新增个性化关键词过滤（`user_keywords`）
- ✨ 新增邮件推送功能（仅站长个人）
- 📊 新增近 7 天趋势图
- 🏷️ 新增关键词标签云

### v1.0

- 🎉 初始版本发布
- ✨ 每日热点 TOP 榜单
- ✨ 15+ 权威 RSS 源聚合
- ✨ 透明热度算法
- ✨ GitHub Pages 部署 + GitHub Actions 自动更新

---

## 🖼️ 效果展示

<!-- 效果展示占位符 -->
<!-- 部署后可在此处替换为实际截图 -->

![首页预览](https://placehold.co/800x450?text=环境学子雷达+首页预览)

*上图为占位符，部署后请替换为实际截图。*

---

## 📄 License

[MIT License](LICENSE)

Copyright (c) 2026 环境学子雷达

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
