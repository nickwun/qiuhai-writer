# 小红书成品包结构

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

## 必查项

- [ ] 图片数量与 `outline.md` 一致。
- [ ] `prompts/` 与 `images/` 一一对应。
- [ ] 图片命名为 `NN-{主题}-{卡片主题}.png`。
- [ ] 图片比例为 3:4。
- [ ] 水印“秋海”位于右下角。
- [ ] 标题备选和推荐标题都是 18-20 个中文字符。
- [ ] 正文包含 emoji。
- [ ] 没有来源平台信息。
- [ ] 没有英里制、华氏度等未转换单位。
