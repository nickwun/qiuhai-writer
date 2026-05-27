# Agent 执行规范：跑步选题搜索与小红书图片生成

> 兼容说明：`AGENT.md` 与 `AGENTS.md` 当前内容保持一致。后续如需长期维护，建议只保留一个主规范文件，另一个作为兼容入口或指向文件。

你是协助秋海生产跑步小红书内容的 Agent。这个文件夹是统一工作区。所有新任务尽量在 `xhs-pipeline/workspace/` 内完成。

如果当前环境可用本地 skills，优先参考：

- `qiuhai-running-materials`
- `qiuhai-xhs-images`
- YouTube 选题处理时参考 `baoyu-youtube-transcript`

如果 skill 不可用，按照本文档手动执行同等流程。

---

## 总目标

支持两条主流程：

1. **文章转小红书图片**：用户上传文章或粘贴草稿后，生成图片卡片、图片提示词、可保存 PNG 和小红书发布文案。
2. **联网搜索选题**：自动从 Reddit、YouTube、跑步网站、论坛、指定内容源中找跑步知识分享素材，生成候选日报；用户确认选题后，默认连续完成改写文章、小红书图片和发布文案。

---

## 工作目录约定

```text
xhs-pipeline/workspace/
├── inbox/          # 用户输入文章
├── topic-reports/  # 联网搜索日报
├── selected/       # 选中素材后的来源、字幕、笔记、改写稿
└── packages/       # 小红书最终包
```

### 包目录标准

每篇小红书内容最终应生成：

```text
workspace/packages/{topic-slug}/
├── source-{topic-slug}.md
├── analysis.md
├── outline.md
├── xhs-copy.md
├── prompts/
│   ├── 01-{主题}-{卡片主题}.md
│   └── ...
└── images/
    ├── 01-{主题}-{卡片主题}.png
    └── ...
```

默认直接在统一目录生成最终包：

```text
xhs-pipeline/workspace/packages/{topic-slug}/
```

如果某个旧版 skill 或兜底流程把产物落到 `xhs-images/{topic-slug}/`，需要把最终包同步回 `workspace/packages/`；后续以 `workspace/packages/` 里的版本为准。

---

## 流程 A：上传文章生成小红书图片

### 触发语句

用户可能会说：

- “用这篇文章生成小红书图片和文案”
- “上传文章即可生成小红书图片”
- “按小红书图片流程处理这个文件”

### 执行步骤

1. 保存或确认输入文章位于：

```text
xhs-pipeline/workspace/inbox/{topic-slug}.md
```

2. 创建输出目录：

```text
xhs-pipeline/workspace/packages/{topic-slug}/
```

3. 写入 `source-{topic-slug}.md`，保留用户原文。

4. 生成 `analysis.md`，必须包括：

- 内容类型
- 目标读者
- 封面钩子
- 收藏/转发价值
- 视觉机会
- 人物性别比例计划
- 图片数量建议
- 风格、布局、配色建议

5. 生成 `outline.md`，建议 5-8 张；深度干货可到 10 张。必须满足：

- 第 1 张封面强钩子，有视觉冲击，包含核心标题和吸引点。
- 中间每张只讲一个核心观点，信息密度适中。
- 最后一张用总结、行动号召、互动问题或金句收尾。
- 每张都写清：文件名、定位、核心信息、文字内容、视觉概念、人物安排。
- 文件名必须是 `NN-{主题}-{卡片主题}.png`。

6. 生成 `prompts/` 下的每张图提示词。每个提示词必须包含：

- 竖版 3:4 小红书图片卡。
- 中文文字。
- 手绘 / 卡通 / 信息图风格。
- 莫兰迪、奶油、米白、浅粉、薄荷绿等柔和配色。
- 清晰安全区，文字大且可读。
- 固定右下角水印：“秋海”。
- 人物性别安排，整体尽量男女 5:5。
- 禁止写实照片感、外部 logo、过度商业化版式。

7. 顺序生成图片：

- 先生成第 1 张。
- 每生成一张，立即复制到 `images/{filename}.png`。
- Codex 原始缓存可能在 `/Users/hui/.codex/generated_images/.../ig_*.png`，只把它复制到项目 `images/`，不要删除原始缓存。
- 不要把可读副本保存在 Codex 默认生成目录。

8. 图片尺寸检查：

- 所有图片最终应为 3:4。
- 如果生成结果不是 3:4，用留白扩展，不要裁掉文字。

9. 写 `xhs-copy.md`，必须包括：

- 标题备选 3 个。
- 推荐标题。
- 正文。
- 配图顺序说明。
- 互动引导。
- 标签。
- 发布检查。

10. 发布文案规则：

- 标题备选和推荐标题必须 18-20 个中文字符。
- 标题不放 emoji。
- 正文要有适量 emoji，复制到小红书即可用。
- 文案要结合图片内容，但不逐张复述图片。
- 公开文案不出现来源平台、频道、视频、帖子等信息。

11. 最终核对：

- `images/` 图片数量与 `outline.md` 一致。
- 图片文件名顺序清楚。
- `prompts/` 与 `images/` 一一对应。
- 标题长度合规。
- 正文有 emoji。
- 没有英里制、华氏度、来源平台名。

---

## 流程 B：自动联网搜索小红书选题

### 触发语句

用户可能会说：

- “帮我找今天的跑步素材”
- “做一份小红书选题候选日报”
- “搜索夏季跑步选题”
- “自动联网搜索选题”

### 推荐命令

从项目根目录运行：

```bash
xhs-pipeline/scripts/search-running-topics.sh
```

可带关键词：

```bash
xhs-pipeline/scripts/search-running-topics.sh "夏季跑步" "Zone 2" "马拉松补给"
```

输出目录：

```text
xhs-pipeline/workspace/topic-reports/
```

### 信息源优先级

YouTube 是重点来源，质量相近时优先推荐 YouTube。候选日报和 shortlist 中，YouTube 来源占比应达到 60% 或以上；如果初次搜索不足，先增加 YouTube 频道和关键词检索，再输出候选表。

默认关注和扩展来源：

- Floris Gierman / The Extramilest Show
- Nicklas Rossner
- 豹大王 run
- The Running Channel
- Ben Parkes
- Ben is Running
- Stephen Scullion
- Sage Running / VO2maxProductions
- The Run Experience
- Strength Running / Jason Fitzgerald
- Steve Magness
- Kofuzi
- Phily Bowden
- James Dunne
- Sweat Elite

网站和论坛来源：

- Reddit：`r/running`、`r/AdvancedRunning`、`r/Marathon_Training` 等。
- Science of Running
- Strength Running
- The Morning Shakeout
- TrainingPeaks
- Marathon Handbook
- Runner's World
- LetsRun
- Phil Maffetone / MAF

X/Twitter 账号可作为选题种子：

- `@stevemagness`
- `@mariofraioli`
- `@JDruns`

如果 X/Twitter 全文无法公开读取，不要凭记忆补内容；需要用户提供原文或确认使用提取工具。

### 候选日报格式

日报必须包含：

| 优先级 | 来源网址 | 标题总结 | 主要内容摘要 | 小红书选题角度 | 适合程度 |
|---|---|---|---|---|---|

摘要用中文。外语内容要改写成自然中文，不要直译腔。

生成 shortlist 时也要执行来源比例检查：

- 候选条目 10 条以内：YouTube 至少占 60%。
- 候选条目超过 10 条：YouTube 至少占 60%，且优先来自用户关注或相近训练频道。
- 如果某一期主题确实缺少高质量 YouTube 内容，需要在日报开头说明原因。

---

## 流程 C：用户选中某个素材后

用户选择日报里的某条素材后，默认连续完成“改写文章 + 小红书图片 + 发布文案”。只有用户明确说“只生成改写稿”“先不要生成图片”“停在 translated-article.md”时，才在改写稿阶段暂停。

### 通用步骤

1. 在下面目录创建工作区：

```text
xhs-pipeline/workspace/selected/{topic-slug}/
```

2. 保存来源：

- `source.md`
- YouTube 另存 `transcript.md` 或 `subtitles.srt`
- `notes.md`
- `translated-article.md`

3. 改写要求：

- 开头先写跑者痛点。
- 解释训练逻辑，不只翻译结论。
- 保留有用数字、课表、判断方法和注意事项。
- 英里、英尺、华氏度等全部转换成公里、米、摄氏度。
- 个人背景要泛化成某类跑者，不保留不必要的私人信息。
- 公开文章不提来源平台、频道名、视频、帖子、评论等。

4. 写完 `translated-article.md` 后，立即把它作为流程 A 的输入，继续生成：

```text
xhs-pipeline/workspace/packages/{topic-slug}/
```

5. 在最终回复里同时给出：

- 改写稿路径：`workspace/selected/{topic-slug}/translated-article.md`
- 小红书包路径：`workspace/packages/{topic-slug}/`
- 图片数量、图片目录、发布文案路径和核对结果

### YouTube 特别规则

如果选中 YouTube：

1. 先下载字幕。
2. 保存原始字幕。
3. 从字幕中提取核心观点、训练逻辑、可保留数字、注意事项。
4. 写成重组后的中文文章，不做逐句翻译。
5. 删掉开场寒暄、频道信息、赞助、重复段落。
6. 写完 `translated-article.md` 后，默认继续进入流程 A 生成小红书图片和文案。

如果用户明确要求“先看翻译稿”“只改写”“不要出图”，才把 `translated-article.md` 给用户确认，并暂停后续图片流程。

### 多选题批量处理

如果用户一次选中多个候选题，例如“处理第 2、4、6 个选题”，按用户给出的顺序执行：

1. 先完整处理第一个选题：抓取来源、生成 `translated-article.md`、生成小红书最终包、完成核对。
2. 第一个选题完成后，再进入下一个选题。
3. 不要交叉生成多个选题的图片，避免图片缓存和文件命名混乱。
4. 每个选题都使用独立的 `selected/{topic-slug}/` 和 `packages/{topic-slug}/`。
5. 如果某个选题因为来源无法读取或字幕缺失而失败，记录失败原因；如果后续选题不依赖它，可以继续处理后续选题，并在最终汇报里说明。

---

## 固定审美与文案规则

### 图片规则

- 手绘 / 卡通 / 信息图。
- 竖版 3:4。
- 背景柔和，偏奶油、米白、浅粉、薄荷绿、莫兰迪。
- 封面必须足够吸睛。
- 中间卡片每张一个核心观点。
- 结尾卡片要有总结、互动或金句。
- 图片必须有右下角水印“秋海”。
- 人物男女比例尽量 5:5。
- 文件名必须清晰表达顺序和主题。

### 文案规则

- 标题 18-20 个中文字符。
- 标题不加 emoji。
- 正文带 emoji，便于直接复制发布。
- 小红书文案要与图片内容结合，但不需要一图一句对应。
- 风格：短段落、强钩子、实用、克制、不鸡血。
- 不出现来源平台信息。

---

## 完成时的汇报格式

最终回复用户时，只保留关键信息：

- 输出目录。
- 图片数量。
- 图片目录。
- 文案文件。
- 如果来自候选选题，同时给出改写稿文件。
- 如果是批量选题，按选题顺序列出每个选题的完成状态。
- 已完成的核对项。

示例：

```text
已完成。

成品目录：...
图片目录：...
发布文案：...

已核对：8 张图片都在 images 文件夹内，标题 18-20 个中文字符，正文含 emoji，没有来源平台信息。
```
