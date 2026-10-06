# 《纳瓦尔宝典》前 5 张示例

这份示例展示 read-cards v4.8.0 的完整交付格式：5 张 1080×1440 PNG、HTML 卡片墙、Markdown、CSV 与 JSON。HTML 下载后可在本地打开，支持搜索、筛选、单卡阅读及复习备注导出。

1. 资产生财，金钱为媒
2. 应需而创，规模成势
3. 循趣深耕，磨砺专长
4. 深植根基，学而日新
5. 择伴长行，信任生息

[卡片墙](cards.html) · [Markdown](cards.md) · [数据源](data.json) · [CSV](cards.csv)

## 预览

![第一张](N01_资产生财_金钱为媒.png)

## 来源

材料为 Eric Jorgenson 编著的《The Almanack of Naval Ravikant》官网英文 EPUB（2020；EBOOK_v103）。[官网公开 EPUB](https://navalmanack.s3.amazonaws.com/Eric-Jorgenson_The-Almanack-of-Naval-Ravikant_EBOOK_v103.epub)。示例仅含短引文、中文自译与教学重构，原文完整书籍由官网提供；中文不是出版译本。详细小节和支持关系见 data.json。个别提取行号用于记录制作时的核对位置，生成时已核对原文，仓库不附完整书籍。

## 重新生成

在仓库根目录运行：

```sh
python3 scripts/render_cards.py examples/naval-5/data.json --output examples/naval-5/cards.html --csv
python3 scripts/render_poster.py examples/naval-5/data.json --card-id NAVAL-002 --output examples/naval-5/N01_资产生财_金钱为媒.png
```

JSON 为内容源，PNG 是排版图。稳定 ID 与展示顺序可能不同：例如旧样卡 NAVAL-001 保留在 N03。复习区当前为空，供使用者自行填写。
