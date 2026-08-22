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
- **热点详情展开**：点击标题展开完整摘要和分析，支持"阅读原文"和"代理访问"（Google 翻译代理）
- **主题定制 UI**：主色、背景色、圆角、密度、字体大小自由调节，实时预览
- **暗黑模式**：一键切换，护眼舒适
- **一键分享**：支持系统分享面板 / 复制链接，快速转发热点
- **用户反馈**：通过 GitHub Issues 提交反馈，无需后端服务器
- **邮件推送**：每日报告自动发送至站长个人邮箱（可选）
- **赞赏支持**：集成爱发电按钮，支持作者持续维护
- **GitHub Pages 部署**：纯静态站点 + GitHub Actions 自动更新，零成本运行

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
pip install feedparser pyyaml jieba
```

> jieba 为可选依赖，未安装时新词提取功能会自动跳过，不影响其他功能。

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

### 项目结构

```
hotspot-radar/
├── config.yaml                  # 配置文件（唯一需修改）
├── daily_report.py              # 每日报告生成脚本
├── .github/
│   └── workflows/
│       └── main.yml             # GitHub Actions 自动更新
├── docs/
│   ├── index.html               # 主页面
│   ├── style.css                # 样式表
│   └── script.js                # 前端脚本
├── data/                        # 生成的数据（自动更新）
│   ├── latest.json
│   ├── daily_report.md
│   ├── history.json
│   └── history.csv
└── README.md
```

---

## 📝 更新日志

### v4.0（最新）

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

Copyright (c) 2024 环境学子雷达

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
