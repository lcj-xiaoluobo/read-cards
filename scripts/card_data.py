"""Shared, dependency-free data validation for SQ3R knowledge cards."""
import json
from pathlib import Path

BASIS = {'原文转述', '逐字引用', '原文案例', '模型推断', '延伸应用'}
SUPPORT = {'direct', 'partial', 'background', 'inference'}
FIELDS = {'survey', 'definition', 'question', 'original', 'original_translation', 'reconstruction', 'answer', 'answer_points', 'boundaries', 'application'}
STATES = {'new', 'needs-review', 'mastered'}
SOURCE_STATUS = {'fulltext', 'excerpt', 'abstract', 'secondary'}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'JSON 字段重复：{key}')
        result[key] = value
    return result


def load_data(path):
    return validate(json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique_object))


def text_field(obj, key, context, blank=False):
    value = obj.get(key)
    if not isinstance(value, str) or (not blank and not value.strip()):
        raise ValueError(f'{context}.{key} 必须是' + ('字符串' if blank else '非空字符串'))


def string_list(value, context, minimum=0):
    if not isinstance(value, list) or len(value) < minimum or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError(f'{context} 必须是至少 {minimum} 项的非空字符串数组')


def is_english(card):
    """Declared source language wins; only legacy data use content detection."""
    language=card.get('original_language', '').strip().lower().replace('_','-')
    if language:
        return language=='en' or language.startswith('en-')
    text=card['original']
    letters=[char for char in text if char.isalpha()]
    return text.isascii() or bool(letters) and all(char.isascii() for char in letters)


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('顶层必须是对象')
    version = data.get('schema_version', 1)
    if type(version) is not int or version not in (1, 2, 3):
        raise ValueError('schema_version 只支持整数 1、2 或 3')
    for key in ('title', 'coverage'):
        text_field(data, key, 'root')
    if 'author_badge' in data:
        badge = data['author_badge']
        if not isinstance(badge, dict):
            raise ValueError('author_badge 必须是对象')
        for key in ('name', 'role', 'portrait_file', 'source', 'credit'):
            text_field(badge, key, 'author_badge')
    for key in ('sources', 'cards'):
        if not isinstance(data.get(key), list) or not data[key]:
            raise ValueError(f'root.{key} 必须是非空数组')
    source_ids = set()
    for i, source in enumerate(data['sources']):
        ctx = f'sources[{i}]'
        if not isinstance(source, dict):
            raise ValueError(f'{ctx} 必须是对象')
        for key in ('id', 'title', 'locator'):
            text_field(source, key, ctx)
        if source['id'] in source_ids:
            raise ValueError(f'重复来源 ID：{source["id"]}')
        source_ids.add(source['id'])
    card_ids = set()
    for i, card in enumerate(data['cards']):
        ctx = f'cards[{i}]'
        if not isinstance(card, dict):
            raise ValueError(f'{ctx} 必须是对象')
        for key in ('id', 'module', 'title', 'definition', 'question', 'original', 'original_kind', 'reconstruction', 'validation'):
            text_field(card, key, ctx)
        text_field(card, 'review', ctx, blank=True)
        if card['original_kind'] not in {'逐字引用', '原文转述'}:
            raise ValueError(f'{ctx}.original_kind 必须说明引用或转述')
        if 'presentation' in card:
            presentation = card['presentation']
            if not isinstance(presentation, dict):
                raise ValueError(f'{ctx}.presentation 必须是对象')
            icon = presentation.get('icon', 'book')
            if not isinstance(icon, str) or icon not in {'growth', 'book', 'compass', 'none'}:
                raise ValueError(f'{ctx}.presentation.icon 支持 growth、book、compass、none')
            title_lines = presentation.get('title_lines')
            if title_lines is not None:
                string_list(title_lines, f'{ctx}.presentation.title_lines', minimum=1)
                if len(title_lines)>2 or ''.join(title_lines)!=card['title']:
                    raise ValueError(f'{ctx}.presentation.title_lines 限一至两行，拼接后须等于原卡名')
        if card['id'] in card_ids:
            raise ValueError(f'重复卡片 ID：{card["id"]}')
        card_ids.add(card['id'])
        string_list(card.get('boundaries'), f'{ctx}.boundaries', minimum=1)
        string_list(card.get('tags'), f'{ctx}.tags')
        string_list(card.get('related_ids', []), f'{ctx}.related_ids')
        for key in ('application', 'answer', 'survey', 'original_translation', 'original_language'):
            if key in card:
                text_field(card, key, ctx)
        if 'answer_points' in card:
            string_list(card['answer_points'], f'{ctx}.answer_points', minimum=1)
        if 'learning_state' in card:
            text_field(card, 'learning_state', ctx)
        if card.get('learning_state', 'new') not in STATES:
            raise ValueError(f'{ctx}.learning_state 无效')
        if 'source_status' in card:
            text_field(card, 'source_status', ctx)
        if 'source_status' in card and card['source_status'] not in SOURCE_STATUS:
            raise ValueError(f'{ctx}.source_status 无效')
        if version >= 2:
            text_field(card, 'answer', ctx)
            string_list(card.get('answer_points'), f'{ctx}.answer_points', minimum=1)
            if not isinstance(card.get('source_status'), str) or card['source_status'] not in SOURCE_STATUS:
                raise ValueError(f'{ctx}.source_status 必须表明实际已读范围')
        if version >= 3:
            text_field(card, 'survey', ctx)
            text_field(card, 'original_language', ctx)
        if not isinstance(card.get('sources'), list) or not card['sources']:
            raise ValueError(f'{ctx}.sources 至少需要一个依据')
        supported = set()
        for j, ref in enumerate(card['sources']):
            rctx = f'{ctx}.sources[{j}]'
            if not isinstance(ref, dict):
                raise ValueError(f'{rctx} 必须是对象')
            for key in ('source_id', 'location', 'basis'):
                text_field(ref, key, rctx)
            if ref['source_id'] not in source_ids:
                raise ValueError(f'{rctx} 指向不存在的来源')
            if ref['basis'] not in BASIS:
                raise ValueError(f'{rctx}.basis 不在支持的类型中')
            if 'note' in ref:
                text_field(ref, 'note', rctx)
            if 'support' in ref or version >= 2:
                text_field(ref, 'support', rctx)
                if ref.get('support') not in SUPPORT:
                    raise ValueError(f'{rctx}.support 无效')
            if 'supports' in ref or version >= 2:
                string_list(ref.get('supports'), f'{rctx}.supports', minimum=1)
                if set(ref['supports']) - FIELDS:
                    raise ValueError(f'{rctx}.supports 包含未知卡片字段')
                if ref.get('support') != 'background':
                    supported.update(ref['supports'])
            if ref.get('support') == 'inference' and ref['basis'] not in {'模型推断', '延伸应用'}:
                raise ValueError(f'{rctx} 的推断支持需要显式标记模型推断或延伸应用')
        if version >= 2 and {'original', 'reconstruction', 'answer'} - supported:
            raise ValueError(f'{ctx} 需要分别说明 original、reconstruction、answer 的支持来源；背景资料不能单独充当支持')
        if version >= 3 and ({'survey'} | ({'original_translation'} if card.get('original_translation') else set())) - supported:
            raise ValueError(f'{ctx} 的概览或中文转译需要分别指定来源支持')
        if version >= 2 and card['original_kind'] == '逐字引用' and not any(
            r['basis'] == '逐字引用' and 'original' in r.get('supports', []) for r in card['sources']
        ):
            raise ValueError(f'{ctx} 的逐字引用缺少对应的引用依据')
    for card in data['cards']:
        missing = set(card.get('related_ids', [])) - card_ids
        if missing or card['id'] in card.get('related_ids', []):
            raise ValueError(f'{card["id"]} 的关联卡片不存在或指向自身')
    if 'coverage_map' in data:
        if not isinstance(data['coverage_map'], list):
            raise ValueError('coverage_map 必须是数组')
        seen = set()
        for i, item in enumerate(data['coverage_map']):
            ctx = f'coverage_map[{i}]'
            if not isinstance(item, dict):
                raise ValueError(f'{ctx} 必须是对象')
            for key in ('source_id', 'section', 'status'):
                text_field(item, key, ctx)
            if item['source_id'] not in source_ids:
                raise ValueError(f'{ctx} 来源不存在')
            if item['status'] not in {'read', 'partial', 'unread', 'unavailable', 'excluded'}:
                raise ValueError(f'{ctx}.status 无效')
            identity = (item['source_id'], item['section'])
            if identity in seen:
                raise ValueError(f'{ctx} 重复章节条目')
            seen.add(identity)
            string_list(item.get('card_ids', []), f'{ctx}.card_ids')
            if set(item.get('card_ids', [])) - card_ids:
                raise ValueError(f'{ctx} 指向不存在的卡片')
            if item['status'] in {'partial', 'unread', 'unavailable', 'excluded'}:
                text_field(item, 'note', ctx)
            if item['status'] in {'unread', 'unavailable', 'excluded'} and item.get('card_ids'):
                raise ValueError(f'{ctx} 未读或排除章节不能声称已生成其正文卡片')
            if 'note' in item:
                text_field(item, 'note', ctx)
            for cid in item.get('card_ids', []):
                card = next(c for c in data['cards'] if c['id'] == cid)
                if item['source_id'] not in {r['source_id'] for r in card['sources']}:
                    raise ValueError(f'{ctx} 卡片不引用该来源')
    return data
