# 书卡 · Read Cards

将书籍、论文与长文拆成可回查原文的知识卡片。当前版本：**4.8.0**。

## 功能

- 先概览、提取、筛选与整合，再按 SQ3R 组织卡片；一张卡只回答一个学习目标。
- 英文材料保留核对过的短引文和精要中文译文；中文原著按真实语言引用。
- 标题凝练有文韵，提问与复述自然清楚。Survey、参考答案、适用边界与来源说明放在 HTML 卡面之外。
- 输出 Markdown、JSON、可选 CSV、支持搜索和模块筛选的 HTML 卡片墙，以及 1080×1440 PNG 分享图。
- 柔和渐变外底、白色圆角主面板、四区分栏、阶段小图标；中文与英文使用不同字体，Review 默认留白。
- 保留稳定卡片 ID 和用户复习记录，支持导出、恢复复习备注。

## 示例

[《纳瓦尔宝典》前 5 张完整示例](examples/naval-5/README.md)包括双语卡片墙、数据与 PNG 分享图。

![卡片预览](examples/naval-5/N01_资产生财_金钱为媒.png)

## 安装到 Codex

将仓库克隆到技能目录：

```sh
git clone https://github.com/lcj-xiaoluobo/read-cards.git ~/.codex/skills/read-cards
```

已有同名技能时，请先备份后再更新。重新打开 Codex 对话，以 `$read-cards` 调用。

## 使用

提供可读取的原文及输出目录，例如：

> 使用 $read-cards，先规划这本 EPUB 的卡片总数、学习目标与顺序，再制作前 5 张，输出 HTML 和 PNG。

> 使用 $read-cards，将这篇论文做成 10 张中文知识卡片，区分研究发现、作者解释和延伸应用，保留出处。

完整工作流程见 [SKILL.md](SKILL.md)，数据字段见 [card-format.md](references/card-format.md)，视觉规范见 [visual-design.md](references/visual-design.md)。

## 脚本

文字提取、HTML/Markdown/CSV 生成及审计使用 Python 3 标准库。PNG 渲染额外需要 Pillow 和本地中文字体：

```sh
python3 -m pip install Pillow
python3 scripts/extract_text.py book.epub --output outputs/source.md
python3 scripts/render_cards.py outputs/data.json --output outputs/cards.html --csv
python3 scripts/audit_cards.py outputs/data.json --output outputs/audit.json --source S1=outputs/source.md
python3 scripts/render_poster.py outputs/data.json --card-id KC-001 --output outputs/card.png
```

`data.json` 由阅读拆解流程生成，是各产物的唯一内容源；`S1` 和 `KC-001` 应替换为数据中的真实 ID。扫描 PDF 需要可靠的 OCR 文本；DRM 受限材料不由脚本绕过。PNG 默认发现 macOS 苹方及 Georgia，也可使用 `--font`、`--title-font`、`--english-font` 指定本地字体。

## 来源与边界

每条核心内容记录来源与支持关系，区分逐字引文、转述、作者主张和模型应用。审计能检查结构和引文是否出现在提供的文本中，不能证明事实或学习效果。方法与设计参考见 [文章方法来源](references/article-provenance.md) 和 [GitHub 参考记录](references/github-design-notes.md)。

仓库提供技能、参考说明、模板和脚本。实际书籍全文、用户复习记录和读书产物由各自的本地任务保存。
