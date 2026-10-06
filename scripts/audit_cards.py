#!/usr/bin/env python3
"""Audit structure, duplicates, declared coverage, and optional local quote matches.
Only explicitly supplied --source ID=PATH files are read; no network requests.
A quote match cannot establish factual truth or citation context.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import unicodedata
from card_data import load_data, is_english


# 破折号/连字符的排版变体：— – ― ‐ ‑ ‒ − ﹘ ﹣ －，折叠为 ASCII '-'。
_DASHES = '\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d'
# 「紧凑」字符：汉字、中文标点、全角符号、中英文引号、数字，以及折叠后的连字符。
# 排版换行常落在这些字符之间（如 维度——\n财富、有\n10、”\n的），需删除其间的空白；
# 英文词间空格两侧为拉丁字母、不在此类，故词边界得以保留。
_TIGHT = '\u3400-\u9fff\u3000-\u303f\uff01-\uff60\u2018\u2019\u201c\u201d0-9-'


def normalized(text):
    # 引文核对须对排版差异稳健：统一 Unicode 组合形式、折叠破折号变体、
    # 删除中文/数字/引号之间的换行空白，同时保留英文词间空格。
    text = unicodedata.normalize('NFC', text)
    text = re.sub(f'[{_DASHES}]+', '-', text)
    text = re.sub(rf'(?<=[{_TIGHT}])\s+(?=[{_TIGHT}])', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def quote_in_text(quote, source):
    quote=normalized(quote)
    # Do not verify a truncated Latin word merely because it occurs inside one.
    left=r'(?<![A-Za-z0-9_])' if quote and quote[0].isascii() and quote[0].isalnum() else ''
    right=r'(?![A-Za-z0-9_])' if quote and quote[-1].isascii() and quote[-1].isalnum() else ''
    return re.search(left+re.escape(quote)+right, normalized(source)) is not None


def audit(data, source_texts=None):
    from card_data import validate
    validate(data)
    source_texts = source_texts or {}
    warnings, errors, checks = [], [], []
    known = {s['id'] for s in data['sources']}
    if set(source_texts) - known:
        raise ValueError('原文核对参数包含不存在的来源 ID')
    for field in ('title', 'question'):
        repeated = {text for text, n in Counter(normalized(c[field]).casefold() for c in data['cards']).items() if n > 1}
        for text in sorted(repeated):
            warnings.append({'code': 'duplicate-' + field, 'cards': [c['id'] for c in data['cards'] if normalized(c[field]).casefold() == text]})
    mapping = data.get('coverage_map', [])
    if mapping:
        represented = {cid for row in mapping for cid in row.get('card_ids', [])}
        missing = {c['id'] for c in data['cards']} - represented
        if missing:
            warnings.append({'code': 'unmapped-cards', 'cards': sorted(missing)})
        for row in mapping:
            if row['status'] != 'read':
                warnings.append({'code': 'incomplete-coverage', 'section': row['section'], 'status': row['status']})
            elif not row.get('card_ids') and not row.get('note'):
                warnings.append({'code': 'read-without-selection-note', 'section': row['section']})
    else:
        warnings.append({'code': 'no-coverage-map', 'message': '短文可省略；长材料需记录章节状态。'})
    for c in data['cards']:
        if 'answer' not in c:
            warnings.append({'code': 'legacy-answer-fallback', 'card': c['id']})
        if is_english(c) and not c.get('original_translation'):
            warnings.append({'code':'missing-translation', 'card':c['id'], 'message':'英文卡尚无中文译文；兼容保留旧数据，新卡交付前补齐或按用户明确要求省略。'})
        if c['original_kind'] != '逐字引用':
            continue
        refs = [r for r in c['sources'] if r['basis'] == '逐字引用' and ('supports' not in r or 'original' in r['supports'])]
        available = {r['source_id'] for r in refs} & set(source_texts)
        if not available:
            checks.append({'card': c['id'], 'status': 'not-checked', 'reason': '未提供该引文对应的本地原文'})
        else:
            matched = [sid for sid in sorted(available) if quote_in_text(c['original'],source_texts[sid])]
            checks.append({'card': c['id'], 'status': 'matched' if matched else 'not-found', 'source_ids': matched or sorted(available), 'normalization':'NFC + 破折号变体折叠 + 中文/数字/引号间换行空白删除；保留英文词间边界'})
            if not matched:
                errors.append({'code': 'quote-not-found', 'card': c['id'], 'source_ids': sorted(available)})
    return {'schema_version': data.get('schema_version', 1), 'cards': len(data['cards']), 'structural_validation': 'passed', 'errors': errors, 'warnings': warnings, 'quote_checks': checks, 'limits': '只检查结构、声明的覆盖与提供文本中的引文出现情况；不验证事实、因果、完整语境或用户掌握程度。'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path)
    p.add_argument('--source', action='append', default=[], metavar='ID=PATH')
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    try:
        data = load_data(args.input)
        texts = {}
        for assignment in args.source:
            sid, sep, path = assignment.partition('=')
            if not sep or not sid or not path or sid in texts:
                raise ValueError('--source 需要唯一的 ID=PATH')
            texts[sid] = Path(path).read_text(encoding='utf-8')
        result = audit(data, texts)
        body = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.output:
            if args.output.resolve() in {args.input.resolve(), *(Path(a.partition('=')[2]).resolve() for a in args.source)}:
                raise ValueError('审计输出不能覆盖数据或原文')
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(body, encoding='utf-8')
        print(f'审计 {result["cards"]} 张卡片：{len(result["errors"])} 个错误，{len(result["warnings"])} 条提示；' + ('报告：' + str(args.output.resolve()) if args.output else body))
        return 1 if result['errors'] else 0
    except (ValueError, OSError) as exc:
        print(f'审计失败：{exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
