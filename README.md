# qiuhai-writer

一个以中文写作为核心的 skill 仓库，主题为“秋海风格写作”。仓库默认入口是 [SKILL.md](./SKILL.md)，用于在 AI 协作中稳定调用、约束和复用这一写作方法。

## 这是什么

`qiuhai-writer` 是一个面向中文写作任务的实用型 skill 仓库。它不提供“自动生成爆款文案”的模板，而是提供一套可重复使用的写作约束：如何贴近“秋海风格”，如何与 AI 协作，如何避免失真，如何自检输出质量。

推荐默认使用 [SKILL.md](./SKILL.md) 作为主引用文件。

## 适用场景

- 需要生成带有明确个人写作气质的中文长短文
- 需要在 AI 协作中保持语气、节奏、视角和边界稳定
- 需要把写作要求沉淀成可维护、可复用的 skill 文件
- 需要为团队或个人建立统一的中文写作调用规范

## 不适用场景

- 只追求高频营销转化、口号式文案或情绪煽动内容
- 需要完全复制某位真实作者的私人经历、身份细节或不可公开语料
- 学术论文、法律文件、说明书等以信息精确性为第一目标的正式文本
- 没有风格约束、只想做通用改写或基础润色的场景

## 仓库结构

```text
qiuhai-writer/
├── README.md
├── SKILL.md
├── README-skill-usage.md
├── examples.md
├── LICENSE
└── .gitignore
```

## 文件说明

- [SKILL.md](./SKILL.md)：主 skill 文件，默认使用入口，包含核心原则、风格模仿指南、AI 协作边界、反向约束、四层自检体系、输出标准与 Prompt Template
- [README-skill-usage.md](./README-skill-usage.md)：使用说明，介绍如何引用和落地这个 skill
- [examples.md](./examples.md)：调用示例，帮助快速上手
- [LICENSE](./LICENSE)：开源许可，默认使用 MIT
- [.gitignore](./.gitignore)：仓库忽略规则

## 使用建议

1. 先阅读 [SKILL.md](./SKILL.md)，确认风格边界与输出标准。
2. 再查看 [README-skill-usage.md](./README-skill-usage.md)，按推荐方式组织提示词。
3. 最后参考 [examples.md](./examples.md)，结合你的具体写作任务调用。

如果你只打算读一个文件，请默认读 [SKILL.md](./SKILL.md)。
