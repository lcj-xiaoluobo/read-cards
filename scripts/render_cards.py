#!/usr/bin/env python3
"""Render SQ3R JSON into an offline HTML card wall and matching Markdown.
Usage: python3 render_cards.py data.json --output cards.html
Requires only Python's standard library. Does not verify factual accuracy.
"""
import argparse
import csv
import html
import io
import json
from pathlib import Path
import sys
from card_data import validate, load_data, is_english
from visual_assets import author_image, icon_svg, background_uri

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "cards.html"
CSV_COLUMNS = ['id', 'module', 'title', 'definition', 'survey', 'question', 'original_kind', 'original', 'original_language', 'original_translation',
               'reconstruction', 'answer', 'answer_points', 'boundaries', 'source_status',
               'validation', 'review', 'learning_state', 'tags', 'sources', 'related_ids']


def render_html(data, base_dir=None):
    validate(data)
    portrait = author_image(data, base_dir or Path.cwd())
    payload = json.dumps(data, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    template=TEMPLATE.read_text(encoding='utf-8')
    template=template.replace('__BACKGROUND__', background_uri())
    template=template.replace('__ICONS__', json.dumps({name:icon_svg(name) for name in ('question','read','recite','review','survey','growth','book','compass')}))
    template=template.replace('__PORTRAIT__', json.dumps(portrait['uri'] if portrait else None))
    template=template.replace('__ENGLISH_IDS__', json.dumps([c['id'] for c in data['cards'] if is_english(c)],ensure_ascii=True).replace('<','\\u003c'))
    before, rest = template.split('__TITLE__', 1)
    middle, after = rest.split('__DATA__', 1)
    return before + html.escape(data['title']) + middle + payload + after


def render_markdown(data):
    validate(data)
    sources = {s['id']: s for s in data['sources']}
    rows = ['# ' + data['title'], '', '## 覆盖范围', '', data['coverage'], '', '## 模块索引', '']
    if data.get('author_badge'):
        badge=data['author_badge']
        rows[6:6]=['## 作者头像说明', '', badge['name']+'｜'+badge['role']+'｜图片来源：'+badge['source']+'｜署名：'+badge['credit'], '']
    modules = list(dict.fromkeys(c['module'] for c in data['cards']))
    for module in modules:
        rows.append('- ' + module + '：' + '、'.join(c['id'] for c in data['cards'] if c['module'] == module))
    for module in modules:
        rows.extend(['', '## ' + module])
        for c in (c for c in data['cards'] if c['module'] == module):
            points = [p for p in c.get('answer_points', []) if p.strip()]
            rows.extend(['', '### ' + c['id'] + '｜' + c['title'], '', '**一句话定义：** ' + c['definition'], '', '**Survey｜概览（网页导览）**', '', c.get('survey', '旧数据未设置概览；请核对原文补充。'), '', '**Question｜提问**', '', c['question'], '', '**Read｜精读（' + c['original_kind'] + '）**', '', c['original'], *(['', c['original_translation']] if c.get('original_translation') else []), '', '**Recite｜复述**', '', c['reconstruction'], '', '**参考答案**', '', c.get('answer', c['reconstruction'])])
            if points:
                rows.extend(['', '**检查要点**', '', '\n'.join('- ' + p for p in points)])
            elif 'answer' not in c:
                rows.extend(['', '**检查要点**', '', '- 旧格式数据未设置检查要点；参考答案沿用重构内容，不代表题目已重新设计。'])
            review = c['review'].strip()
            rows.extend(['', '**Review｜复习**', '', review or '（留白，待填写）', '', '**适用边界**', ''])
            rows.extend('- ' + b for b in c['boundaries'])
            rows.extend(['', '**来源范围：** ' + c.get('source_status', '旧格式未单独记录'), '**核对说明：** ' + c['validation'], '', '**来源**', ''])
            for ref in c['sources']:
                s = sources[ref['source_id']]
                rows.append(f'- {s["title"]}｜{ref["location"]}｜{ref["basis"]}｜{s["locator"]}' + ('｜支持字段：' + '、'.join(ref['supports']) if ref.get('supports') else '') + ('｜支持程度：' + ref['support'] if ref.get('support') else '') + ('｜' + ref['note'] if ref.get('note') else ''))
            if c.get('application'):
                rows.extend(['', c['application']])
            if c.get('related_ids'):
                rows.extend(['', '**关联卡片：** ' + '、'.join(c['related_ids'])])
            if c['tags']:
                rows.extend(['', '**标签：** ' + '、'.join(c['tags'])])
    if data.get('coverage_map'):
        rows.extend(['', '## 章节覆盖', ''])
        for entry in data['coverage_map']:
            rows.append('- ' + entry['source_id'] + '｜' + entry['section'] + '｜' + entry['status'] + '｜' + '、'.join(entry.get('card_ids', [])) + ('｜' + entry['note'] if entry.get('note') else ''))
    return '\n'.join(rows) + '\n'


def render_csv(data):
    validate(data)
    sources = {s['id']: s for s in data['sources']}
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)
    for c in data['cards']:
        refs = '；'.join(
            f'{sources[r["source_id"]]["title"]}｜{r["location"]}｜{r["basis"]}'
            + (f'｜{r["support"]}' if r.get('support') else '')
            for r in c['sources'] if r['source_id'] in sources
        )
        writer.writerow([
            c['id'], c['module'], c['title'], c['definition'], c.get('survey', ''), c['question'],
            c['original_kind'], c['original'], c.get('original_language', ''), c.get('original_translation', ''), c['reconstruction'],
            c.get('answer', ''), ' | '.join(c.get('answer_points', [])),
            ' | '.join(c['boundaries']), c.get('source_status', ''), c['validation'],
            c['review'], c.get('learning_state', 'new'), '、'.join(c['tags']), refs,
            '、'.join(c.get('related_ids', [])),
        ])
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--csv', action='store_true', help='同时导出 UTF-8 BOM 的 cards.csv（表格复盘用）')
    args = parser.parse_args()
    output = args.output or args.input.with_suffix('.html')
    markdown = output.with_suffix('.md')
    table = output.with_suffix('.csv')
    try:
        if output.suffix.lower() != '.html':
            raise ValueError('输出文件扩展名必须为 .html')
        outputs = {output.resolve(), markdown.resolve()}
        if args.csv:
            outputs.add(table.resolve())
        if args.input.resolve() in outputs or len(outputs) != (3 if args.csv else 2):
            raise ValueError('输出路径不能覆盖输入数据，也不能让多个输出写入同一文件')
        data = load_data(args.input)
        page, md = render_html(data, args.input.parent), render_markdown(data)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(page, encoding='utf-8')
        markdown.write_text(md, encoding='utf-8')
        written = [output, markdown]
        if args.csv:
            table.write_text('\ufeff' + render_csv(data), encoding='utf-8', newline='')
            written.append(table)
    except (OSError, ValueError) as exc:
        print(f'无法生成卡片：{exc}', file=sys.stderr)
        return 1
    print(f'已生成 {len(data["cards"])} 张 SQ3R 卡片：' + '、'.join(str(p.resolve()) for p in written))
    return 0


if __name__ == '__main__':
    sys.exit(main())
