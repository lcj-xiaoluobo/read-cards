# 原文获取与定位

拆卡之前必须先拿到可定位的正文。默认只处理用户本地、且有权使用的材料；提取过程不联网，不上传。

## 提取命令

```sh
python3 /absolute/path/to/read-cards/scripts/extract_text.py /absolute/path/to/book.epub --output /absolute/path/to/output/source.md
```

支持 `.txt .md .markdown .text .html .htm .xhtml .epub .docx .pdf`，仅用标准库：

- **EPUB**：按 OPF 的 spine 顺序输出，每段正文前插入 `[EPUB 章节 n｜文件名]` 作为定位锚点；跳过脚本与样式。
- **DOCX**：按段落输出 `word/document.xml` 的文字；文本框与图片内容不会提取，需人工补齐。
- **PDF**：优先用已安装的 `pypdf`，否则调用 poppler 的 `pdftotext -layout`。扫描件没有文字层，必须先 OCR，不能凭文件名猜测内容。
- **HTML/XHTML**：去标签后按块级元素分段。

输出的 `source.md` 同时用于引文核对：`audit_cards.py --source S1=/absolute/path/to/source.md`。

## 扫描版 PDF 与 OCR

`pdftotext` 输出为空或字数明显偏少时，先确认是不是扫描件（无文字层），再做 OCR：

- **macOS**：用 Vision 框架的 `VNRecognizeTextRequest`（`recognitionLevel = .accurate`、`recognitionLanguages = ["zh-Hans", "en-US"]`、`usesLanguageCorrection = true`），配 PDFKit 逐页渲染成位图后识别。300 页左右的书约 1–2 分钟。逐页输出时保留 `[P.n]` 之类的页码标记，便于回查。
- **其他平台**：`tesseract -l chi_sim+eng`。

OCR 文本的已知偏差，取引文时要么避开、要么核对：

- **页眉与页码**：每页开头会混入页码、章节号与书名（例如 `230\n第二天\n金钱进化论`）。跨页引文会被这些内容打断，**引文尽量控制在同一页内**；确实需要跨页时，改用同页内可核对的完整句。
- **形近字混淆**：中文 OCR 常见 竞/竟、己/已、兀/无、溶寞/寂寞 等。引用前逐字核对，宁可换一句干净的引文，也不要把 OCR 错字当成原书用字写进卡片。
- **标点与数字**：破折号可能是 `—` 或 `——`，数字分组空格可能被吞掉（`551 616` → `551616`）。引文核对脚本已统一这些差异，但错字不会被自动放过。

**页码换算**：优先使用 OCR 识别出的印刷页码，并在 `locator` 里写明换算关系（例如「PDF 页码 − 11；第 165 页后因插页改为 − 10」）。印刷页码缺失时退用 PDF 页码并标注清楚。

## 定位约定

`location` 要能让人回到原文，优先用材料自己的结构，不写“前文/某处”：

| 材料 | 推荐写法 |
| --- | --- |
| 书籍 EPUB/纸质 | `第 3 章〈杠杆〉` 或 `[EPUB 章节 7]` |
| PDF 论文 | `p.12 Results`，必要时加表号 `Table 2` |
| DOCX/网页 | `第 2 节` 或小节标题 |
| 用户粘贴片段 | `用户提供片段·第 2 段` |

`locator` 写文件级出处（书名+版本/出版社、DOI、链接或本地路径），与 `location` 分工不同。

## 分批处理

整书一次读不完时，按章节切分成多个 `source.md`，在 `sources` 里登记多个来源 ID（S1、S2…），并在 `coverage_map` 逐条记录状态：读过的标 `read`，只看了部分标 `partial` 并在 `note` 写已读段落。未读部分不能挂卡片，也不能声称已覆盖。

核对引文时对每个来源分别传参：`--source S1=... --source S2=...`。

## 处理不了的缺口

遇到以下情况直接报告缺口，不用记忆或推测补齐：DRM 加密的电子书、纯图片 PDF 且没有 OCR、`.mobi/.azw3` 等未支持格式、提取后字数明显异常偏少（可能漏了正文）。补齐方式由用户决定：转换格式、做 OCR，或只就可读范围出卡。
