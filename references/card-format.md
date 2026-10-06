# v3 数据规范与兼容

JSON 为内容唯一来源，UTF-8，纯文本字段不放 HTML。新产物使用 schema_version: 3；省略时按 v1 处理，v1/v2 仍可读取。旧数据没有 Survey 时不显示概览，不能凭目录自动补成已读背景；旧题缺少答案时兼容回退为 reconstruction。

## 最小完整例子

这是自编演示，不是书籍或研究事实：

```json
{
  "schema_version": 3,
  "title": "自编方法示例",
  "coverage": "只读取了提供的示例段落。",
  "sources": [{"id": "S1", "title": "示例文本", "locator": "用户提供文本"}],
  "coverage_map": [{"source_id": "S1", "section": "第 1 段", "status": "read", "card_ids": ["KC-001"]}],
  "cards": [{
    "id": "KC-001",
    "module": "阅读范围",
    "title": "按实际已读范围声明产物",
    "definition": "片段阅读只能支持片段卡片。",
    "survey": "片段方法说明：产物范围以实际已读材料为准。",
    "original_language": "zh",
    "question": "只有某章正文时，能否声明完成整本书的拆解？",
    "original": "只读一章，不声称已读全书。",
    "original_kind": "逐字引用",
    "reconstruction": "产物范围受实际材料限制，不能用目录替代正文。",
    "answer": "不能。只应声明该章节范围，目录不等于阅读正文。",
    "answer_points": ["限定到实际章节", "区分目录与正文"],
    "boundaries": ["其他章节未提供时，不能断言它们没有相关知识。"],
    "source_status": "excerpt",
    "validation": "示例短引文已核对；范围提醒为方法归纳。",
    "review": "",
    "learning_state": "new",
    "tags": ["来源范围"],
    "sources": [
      {"source_id": "S1", "location": "第 1 段", "basis": "逐字引用", "support": "direct", "supports": ["original"]},
      {"source_id": "S1", "location": "第 1 段", "basis": "原文转述", "support": "partial", "supports": ["survey", "reconstruction", "answer"], "note": "目录与正文的区别为明确的方法归纳，不是该短句的逐字内容。"}
    ],
    "related_ids": []
  }]
}
```

## 字段规则

顶层 title、coverage、sources、cards 必填；sources 中 id/title/locator 必填，author/year/edition 可选且不编造。schema_version 为整数 1、2 或 3。book_title 可选，用于卡面书名。JSON 重复字段拒绝，以免不同解析器读出不同结果。

单卡必填：id、module、title、definition、question、original、original_kind、reconstruction、boundaries、validation、review、tags、sources。v2/v3 另必填 answer、answer_points、source_status。v3 另必填 survey（局部概览）、original_language（原文语言，如 en/zh）；original_translation 可选，英文新卡应提供精要中文译文并注明来源支持；精读区直接显示译文，不显示“中文转译”标签。ID 在集合内唯一，已存在卡片修订保持 ID，学习目标改变才换 ID。

- original_kind：逐字引用 / 原文转述。未逐字核对只用转述；引用短且受环境的累计引用限制。
- answer：直接回答单一问题；answer_points 为同一目标的可核对要点，推荐 1–3 项。
- boundaries：至少一条真实范围限制或明确标注的模型误用提醒，不能凑数。
- source_status：fulltext（已读全文）/ excerpt（片段）/ abstract（仅摘要）/ secondary（二手资料）。这是读取范围，不是证据强度。
- validation：核对说明，不填“科学证明/必然有效”等无依据承诺。
- review 默认空字符串，专供用户自己的记录。
- learning_state 可省略，默认为 new（未自评）；needs-review（需巩固）/ mastered（已掌握）仅为旧版用户记录；新版不提供自评 UI，不清除历史字段。
- related_ids 指向存在且非自身的 ID；application 可选，明确标模型延伸或教学示例。

每条来源依据的 source_id/location/basis 必填；v2 另含 support 与 supports：

- basis：原文转述、逐字引用、原文案例、模型推断、延伸应用。
- support：direct 直接支持 / partial 部分支持 / background 背景 / inference 推断；推断须与模型推断或延伸应用标识一致。background 只能提供背景，不能单独满足原文、重构或答案的来源要求。
- supports：该依据支持的字段数组，可用 survey、definition、question、original、original_translation、reconstruction、answer、answer_points、boundaries、application。
- v2 每张卡必须分别为 original、reconstruction、answer 指定支持关系；逐字引用须对应 basis=逐字引用 的 original 依据。v3 还需说明 survey，以及可选 original_translation 存在时的支持来源。note 写支持范围与未证实部分。

coverage_map 用于长材料，短文可省略。每项 source_id/section/status，card_ids 可空；status 为 read/partial/unread/unavailable/excluded。非 read 需 note；未读、无法读取、排除章节不能挂其正文卡片；已读但未选卡也应说明理由。覆盖表检查的是声明一致性，不能证明实际阅读。

## 复习记录的往返

网页修改 review 后导出 JSON 保存。旧版 learning_state 原样保留，但不显示。再次打开同一套网页可用“恢复复习记录”导入这份 JSON；只恢复用户记录，不覆写卡片内容。标题、ID 集和概览/问题/原文/转译/重构/答案需匹配，否则报告内容已改变。改变卡片内容后需重新渲染，判断旧记录是否仍适用于新目标。

## 原文核对

运行 audit_cards.py --source S1=/path/source.md 只读取显式提供的本地文本。比对前先做 NFC 归一，把破折号变体（—／——／－／– 等）折叠为 `-`，并删除中文、中文标点、引号与数字之间的换行空白（如 `维度——\n财富`、`有\n10`、`”\n的`），因此换行与 OCR 破折号差异不会造成假性不匹配；英文词间空格保留，以免把英文词边界揉在一起。但不改数字内容与错字——引文里若混入 OCR 形近字错误（竞/竟、己/已 等）会直接报 quote-not-found，必须回查原文并换用干净的引文，而不是放宽比对。跨页引文会被页眉、页码标记打断，因此引文优先控制在同一页内。转述、推断及语境仍需人工/模型逐条核对。没有原文文件时 quote_checks 为 not-checked，不能称完成机器引文核对。

## 卡面与 HTML 的分工

SQ3R 是五步阅读流程；Survey 数据保留，在 HTML 网页导览展示。卡面只保留 Question、Read、Recite、Review 四个完整英文名称与中文，不显示独立字母简写，Read 区按实际来源语言显示原文，英文源下方保留中文译文但不加“中文转译”前缀，Review 默认留白。参考答案、检查要点、边界和核对说明只在 HTML 单卡外展开，PNG 不包含这些字段，也不显示自评状态。

## 可选视觉元数据

单卡 `presentation.title_lines` 为一至两项非空字符串数组；拼接后必须与 title 完全相同。这是历史杂志版的视觉换行元数据，不改变内容或引用；当前初版分栏布局忽略该字段，以原卡名显示单行标题。JSON 可保留该字段，Markdown 和 CSV 仍使用原卡名。


## 可选作者头像与内容图标

左下角优先放书中作者头像；素材身份与来源不明确时，使用与知识点相关的图标。作者信息是视觉署名，不是正文证据；必须区别作者/编者/书中人物。照片不改变 sources 或支持关系。

顶层可选 `author_badge` 对象，必填非空 `name`、`role`、`portrait_file`、`source`、`credit`。portrait_file 是本地 PNG/JPEG/WebP，相对 data.json 所在目录解析，最大 8 MB；路径不存在或文件无效会报错，不能默默换一张人物图。source 记录真实图片来源（链接或用户提供），credit 记录实际署名/授权说明，不编造许可。渲染前先准备合法、身份明确的素材；没有素材就省略整个对象，使用图标。

```json
{"author_badge":{"name":"已核对姓名","role":"作者","portrait_file":"assets/author.png","source":"实际来源","credit":"实际署名"}}
```

每张卡的 `presentation.icon` 可选 `growth`（成长、专长）、`book`（阅读、知识，默认）、`compass`（选择、方向）或 `none`（无图标）。作者头像存在时优先于图标。示例：`"presentation":{"icon":"growth"}`。图标不需加入正文引用支持；选图必须贴合当前知识点。阶段图标固定在模板：question/read/recite/review，survey 仅网页。

HTML 内嵌本地头像，导出 JSON 仍保留原文件路径；移动数据须一并带图片。PNG 和 HTML 没有 author_badge 时都正常显示内容图标，无需等待用户提供照片。


## 语言与缺译文提示

HTML 与 PNG 共用 original_language 判定：en/en-* 为英文，其余明确语言按该语言处理；仅旧数据没有语言字段时回退为 ASCII 或英文字母检测，允许弯引号、长破折号等排版符号。中文句子中的 DNA、RNA 等术语不改变整段的语言身份。英文转述的“原文转述”标签单独使用中文字体，正文无逐字引号。

保留 v1–v3 兼容。英文卡缺少 original_translation 时 audit_cards.py 给出 missing-translation 警告，指出需补译或有用户明确省略要求；不将所有旧数据升级为硬错误。
