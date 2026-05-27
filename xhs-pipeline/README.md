# 小红书跑步内容生产流水线

这个文件夹把两个原本分散的能力合在一起：

1. 上传或粘贴文章，生成小红书图片卡片和发布文案。
2. 自动联网搜索跑步选题，生成小红书候选选题日报。

后续给其他 Agent 使用时，优先让它阅读：

```text
xhs-pipeline/AGENT.md
```

那份文件是执行规范；本文件是给人看的快速说明。

---

## 当前项目文档现状

项目根目录原本主要是 `qiuhai-writer` 写作 skill：

- `README.md`：秋海风格写作项目说明。
- `SKILL.md`：公众号长文写作 skill 主规则。
- `README-skill-usage.md`：写作 skill 的人工说明。
- `corpus/`：秋海文风语料和写作约束。

小红书相关能力此前分散在两个位置：

- `running-materials/`：联网搜索跑步素材、候选日报、已选题改写稿。
- `xhs-images/`：每篇文章的小红书图片、提示词、文案和成品图片。

真正的执行规则主要来自两个本地 skill：

- `/Users/hui/.codex/skills/qiuhai-running-materials/SKILL.md`
- `/Users/hui/.codex/skills/qiuhai-xhs-images/SKILL.md`

现在的 `xhs-pipeline/` 是统一入口。后续新任务都在这个文件夹内完成和归档；如果旧的分散目录仍存在，只作为历史产物或兜底参考，不再作为默认工作区。

---

## 统一目录结构

```text
xhs-pipeline/
├── README.md
├── AGENT.md
├── scripts/
│   └── search-running-topics.sh
├── templates/
│   ├── article-input.md
│   ├── selected-topic-brief.md
│   └── xhs-package-layout.md
└── workspace/
    ├── inbox/          # 用户上传或粘贴的原始文章
    ├── topic-reports/  # 联网搜索生成的候选选题日报
    ├── selected/       # 选题确认后的改写稿、字幕、来源说明
    └── packages/       # 小红书图片与文案最终包
```

---

## 功能一：上传文章生成小红书图片

把文章保存到：

```text
xhs-pipeline/workspace/inbox/{topic-slug}.md
```

然后让 Agent 执行：

```text
请按 xhs-pipeline/AGENT.md，把 workspace/inbox/{topic-slug}.md 生成小红书图片和发布文案。
```

最终产物应放到：

```text
xhs-pipeline/workspace/packages/{topic-slug}/
```

标准产物包括：

- `source-{topic-slug}.md`
- `analysis.md`
- `outline.md`
- `prompts/`
- `images/`
- `xhs-copy.md`

图片文件必须按顺序和主题命名，例如：

```text
01-热适应-封面警报.png
02-热适应-硬扛后果.png
03-热适应-身体变化.png
```

---

## 功能二：自动联网搜索选题

直接运行：

```bash
xhs-pipeline/scripts/search-running-topics.sh
```

默认会搜索 Reddit、YouTube、跑步网站、论坛和指定跑步内容源，输出到：

```text
xhs-pipeline/workspace/topic-reports/
```

如果要搜索指定方向：

```bash
xhs-pipeline/scripts/search-running-topics.sh "夏季跑步" "Zone 2" "马拉松补给"
```

选中某个题目后，默认让 Agent 连续完成“改写文章 + 小红书图片 + 发布文案”：

```text
请按 xhs-pipeline/AGENT.md，处理候选日报里的第 N 个选题，连续完成改写文章、小红书图片和发布文案。
```

执行完成后，改写稿会保存到：

```text
xhs-pipeline/workspace/selected/{topic-slug}/translated-article.md
```

小红书最终包会保存到：

```text
xhs-pipeline/workspace/packages/{topic-slug}/
```

如果只想先看改写稿，需要明确说明：

```text
只生成改写稿，先不要生成图片。
```

多个选题可以一次性指定，Agent 应按顺序处理；每个选题完整生成改写稿、图片和文案后，再进入下一个选题。

后续选题日报会提高 YouTube 来源占比：候选表和 shortlist 中，YouTube 来源默认应达到 60% 或以上。

---

## 关键规则

- YouTube 选题必须先下载字幕，再提取核心观点并重写，不做逐句翻译。
- 外语内容要改写成自然中文，英里制、华氏度等要转换成公里制、摄氏度。
- 公开文章和小红书文案不出现来源平台名、频道名、Reddit、YouTube、X/Twitter 等信息。
- 标题备选和推荐标题必须为 18-20 个中文字符，不加 emoji。
- 小红书正文需要直接带 emoji，方便复制发布。
- 图片只保存一份最终可读文件到 `images/`，不要再把可读副本存到 Codex 默认生成目录。
- 图片人物性别比例尽量 5:5，避免连续默认生成女性卡通跑者。

---

## 推荐调用语句

### 文章转图片

```text
请读取 xhs-pipeline/AGENT.md，并处理 xhs-pipeline/workspace/inbox/{topic-slug}.md：
生成小红书图片卡片和发布文案，最终包放到 xhs-pipeline/workspace/packages/{topic-slug}/。
```

### 搜索选题日报

```text
请读取 xhs-pipeline/AGENT.md，联网搜索今天适合小红书的跑步选题，重点加强 YouTube 信息源，输出候选日报。
```

### 处理候选选题

```text
请读取 xhs-pipeline/AGENT.md，处理候选日报里的第 N 个选题。
如果是 YouTube，先下载字幕并提取核心观点，生成改写后的中文文章，然后继续生成小红书图片和发布文案。
```

### 批量处理候选选题

```text
请读取 xhs-pipeline/AGENT.md，按顺序处理候选日报里的第 2、4、6 个选题。
每个选题都连续完成改写文章、小红书图片和发布文案，一个完成后再做下一个。
```

### 只生成改写稿

```text
请读取 xhs-pipeline/AGENT.md，处理候选日报里的第 N 个选题。
只生成改写稿，先不要生成图片。
```
