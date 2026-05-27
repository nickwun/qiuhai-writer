# xhs-pipeline 项目交接说明

更新时间：2026-05-27

## 当前项目定位

`xhs-pipeline/` 是 `qiuhai-writer` 仓库内的小红书跑步内容生产流水线，用于统一管理跑步选题搜索、素材整理、改写稿、小红书图片提示词、发布文案和本地成品输出。

当前暂停内容生成，先整理项目结构和版本管理边界。后续继续开发或生成内容前，应先阅读：

- `xhs-pipeline/README.md`
- `xhs-pipeline/AGENT.md`
- `xhs-pipeline/AGENTS.md`

`AGENT.md` 与 `AGENTS.md` 当前内容保持一致，后续建议明确一个主维护文件，另一个仅作为兼容入口。

## 目录结构

```text
xhs-pipeline/
├── AGENT.md
├── AGENTS.md
├── PROJECT_HANDOFF.md
├── README.md
├── scripts/
│   └── search-running-topics.sh
├── templates/
│   ├── article-input.md
│   ├── batch-topic-queue.md
│   ├── selected-topic-brief.md
│   └── xhs-package-layout.md
└── workspace/
    ├── inbox/
    ├── topic-reports/
    ├── selected/
    └── packages/
```

仓库根目录还有：

```text
scripts/
└── discover_running_materials.py
```

`xhs-pipeline/scripts/search-running-topics.sh` 会调用根目录下的搜索脚本，并将报告输出到 `xhs-pipeline/workspace/topic-reports/`。

## 运行方式

从仓库根目录运行默认选题搜索：

```bash
xhs-pipeline/scripts/search-running-topics.sh
```

带关键词运行：

```bash
xhs-pipeline/scripts/search-running-topics.sh "夏季跑步" "Zone 2" "马拉松补给"
```

脚本当前通过自身位置自动识别仓库根目录，避免依赖固定绝对路径。

## Git 管理边界

纳入 Git 的内容：

- `xhs-pipeline/` 的规范、说明、模板和脚本。
- `xhs-pipeline/workspace/selected/` 中的草稿、来源说明、笔记、改写稿等文本文件。
- `xhs-pipeline/workspace/topic-reports/` 中需要复盘的 Markdown、CSV、JSON 报告。
- `xhs-pipeline/workspace/packages/` 中可复用、可追踪的文本资产，例如 `source-*.md`、`analysis.md`、`outline.md`、`xhs-copy.md`、`prompts/*.md`。
- 根目录 `scripts/discover_running_materials.py`。

不纳入 Git 的内容：

- `xhs-pipeline/workspace/packages/**/images/`
- `xhs-pipeline/workspace/packages/**/*.png`
- `youtube-transcript/`
- `__pycache__/`
- `*.pyc`
- `.DS_Store`

PNG 成品图和 YouTube 字幕下载目录目前视为本地输出或缓存。后续如有高价值文本材料需要长期保存，应整理到正式素材目录后再纳入版本管理。

## 当前已完成内容

当前已有 5 个小红书成品包，文本资产和本地图片均保留在 `workspace/packages/`：

- `easy-runs-summer`
- `summer-heat-illness`
- `summer-running-cramps`
- `summer-slow-fall-fast`
- `summer-wbgt-running`

这些包的 PNG 图片暂时只保留本地，不纳入 Git。

## 当前草稿

以下选题在 `workspace/selected/` 中已有改写稿或笔记，但暂不继续生成图片包：

- `heat-acclimation-not-heroics`
- `summer-heat-heart-rate`
- `summer-long-run-hydration`
- `heat-humidity-training`

这些草稿不要擅自废弃，也不要自动继续出图。后续等待逐个确认。

## 当前风险

- 选题搜索依赖网络、DuckDuckGo、Reddit 和 YouTube 公开可访问状态，可能出现超时或请求失败。
- 生成图片属于大体积输出，应持续排除在 Git 外。
- `workspace/` 同时包含草稿、报告和成品文本，后续如果规模扩大，建议补充索引文件或状态清单。
- `AGENT.md` 与 `AGENTS.md` 双文件并存会带来维护风险，后续应明确主文件。

## 后续建议

1. 先确认本次整理后的 Git 边界。
2. 再决定是否提交 `xhs-pipeline/`、根目录 `scripts/discover_running_materials.py` 和 README 更新。
3. 为 `workspace/packages/` 增加轻量索引，记录每个包的来源、状态、文本文件和本地图片数量。
4. 逐个确认草稿选题是否继续生成小红书图片包。
