#!/usr/bin/env python3
"""Render a four-section, bilingual gradient PNG; Survey stays outside the card.
Requires Pillow and local fonts. This is typesetting, not a browser screenshot.
"""
import argparse
import json
import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from card_data import load_data, is_english
from visual_assets import author_image, BACKGROUND_CORNERS

INK = '#292820'
MUTED = '#827b70'
PAPER = '#ffffff'
STAGES = [
    ('Question', '提问', '#527e9e', '#e7eff6', '#f5f8fc', 344, 184),
    ('Read', '精读', '#56866c', '#e7f1e9', '#f4f9f5', 550, 384),
    ('Recite', '复述', '#b68244', '#faf0e1', '#fdf8ef', 956, 206),
    ('Review', '复习', '#ab738c', '#f7eaf0', '#fcf5f8', 1184, 132),
]


def font_path(explicit, candidates):
    for path in [explicit] if explicit else candidates:
        if Path(path).is_file():
            return str(path)
    raise ValueError('找不到字体，请用 --font、--title-font、--english-font 指定本地字体。')


def wrap(text, font, width, english=False):
    result = []
    for paragraph in text.splitlines() or ['']:
        line = ''
        for unit in paragraph.split() if english else list(paragraph):
            joiner = ' ' if english and line else ''
            candidate = line + joiner + unit
            if font.getlength(candidate) > width and line:
                # Keep closing Chinese punctuation with the preceding phrase.
                if not english and unit in '，。？！；：、）】》”’':
                    moved = line[-1]
                    result.append(line[:-1])
                    line = moved + unit
                else:
                    result.append(line)
                    line = unit
            else:
                line = candidate
            if font.getlength(line) > width:
                raise ValueError('存在无法完整显示的长单词，请精简原文。')
        if line:
            result.append(line)
    if not english and len(result)>1 and font.getlength(result[-1])<width*.35:
        previous=result[-2]
        cut=max(previous.rfind(mark) for mark in '，、；')+1
        if 0<cut<len(previous):
            combined=previous[cut:]+result[-1]
            if font.getlength(combined)<=width:
                result[-2:]=[previous[:cut],combined]
    return result


def gradient(size, stops):
    def rgb(h):
        return tuple(int(h[n:n+2], 16) for n in (1, 3, 5))
    image = Image.new('RGB', size)
    draw = ImageDraw.Draw(image)
    for y in range(size[1]):
        t = y / (size[1]-1)
        for (a, ca), (b, cb) in zip(stops, stops[1:]):
            if a <= t <= b:
                f = (t-a)/(b-a)
                color = tuple(round(x+(v-x)*f) for x, v in zip(rgb(ca), rgb(cb)))
                draw.line((0, y, size[0], y), fill=color)
                break
    return image


def small_icon(draw, name, x, y, size, color, font=None):
    def pt(a,b): return (x+a*size/32,y+b*size/32)
    def line(points): draw.line([pt(*p) for p in points], fill=color, width=max(2,round(size/16)), joint='curve')
    if name=='question':
        line([(4,4),(28,4),(28,25),(12,25),(6,29),(6,25),(4,25),(4,4)])
        draw.text(pt(16,14),'?',font=font.font_variant(size=max(14,round(size*.66))),fill=color,anchor='mm')
    elif name in {'read','book'}:
        line([(4,7),(12,7),(16,10),(20,7),(28,7),(28,25),(20,25),(16,28),(12,25),(4,25),(4,7)])
        line([(16,10),(16,28)])
        if name=='read':
            for a,b in [(8,12),(20,12),(8,17),(20,17)]:line([(a,b),(a+4,b)])
    elif name=='recite':
        line([(5,6),(27,6),(27,22),(14,22),(7,27),(7,22),(5,22),(5,6)])
        line([(10,12),(22,12)]);line([(10,17),(18,17)])
    elif name=='review':
        draw.arc((*pt(6,6),*pt(26,26)),30,330,fill=color,width=max(2,round(size/16)))
        line([(25,5),(25,13),(17,13)])
    elif name=='growth':
        line([(16,27),(16,14)]);line([(10,27),(22,27)])
        line([(16,19),(10,19),(6,15),(5,8),(12,10),(16,14),(16,19)])
        line([(16,15),(16,10),(21,5),(27,4),(25,11),(21,15),(16,15)])
    elif name=='compass':
        draw.ellipse((*pt(4,4),*pt(28,28)),outline=color,width=max(2,round(size/16)))
        line([(21,10),(18,18),(10,22),(14,13),(21,10)])


def render(data, card_id, output, fonts, indices=(0, 0), base_dir=None):
    card = next((c for c in data['cards'] if c['id'] == card_id), None)
    if card is None:
        raise ValueError('卡片 ID 不存在：'+card_id)
    # A bilinear pastel wash: cool blue to cream above, lavender to rose below.
    corners = Image.new('RGB',(2,2))
    corners.putdata([tuple(int(color[n:n+2],16) for n in (1,3,5)) for color in BACKGROUND_CORNERS])
    image=corners.resize((1080,1440),Image.Resampling.BILINEAR,box=(.5,.5,1.5,1.5))
    shadow=Image.new('RGBA',image.size,(0,0,0,0))
    ImageDraw.Draw(shadow).rounded_rectangle((48,52,1032,1410),radius=36,fill=(48,47,77,30))
    image=Image.alpha_composite(image.convert('RGBA'),shadow.filter(ImageFilter.GaussianBlur(18))).convert('RGB')
    draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((48,42,1032,1402),radius=36,fill=PAPER,outline='#eeeef4',width=2)
    cn = lambda size: ImageFont.truetype(fonts[0], size, index=indices[0])
    title_font = ImageFont.truetype(fonts[1], 76, index=indices[1])
    en = lambda size: ImageFont.truetype(fonts[2], size)
    for _, _, accent, bg, light, y, height in STAGES:
        panel = gradient((height,928),[(0,bg),(1,light)]).transpose(Image.Transpose.ROTATE_90)
        mask = Image.new('L',(928,height),0)
        ImageDraw.Draw(mask).rounded_rectangle((0,0,927,height-1),radius=22,fill=255)
        image.paste(panel,(76,y),mask)
        ImageDraw.Draw(image).rounded_rectangle((76,y,82,y+height-1),radius=3,fill=accent)
    draw = ImageDraw.Draw(image)
    bounds = []

    def text_lines(lines, x, y, font, color, step, bottom=1410):
        for line in lines:
            box = draw.textbbox((x, y), line, font=font, anchor='lt')
            if box[0] < 70 or box[2] > 1010 or box[3] > bottom:
                raise ValueError('文字超出所属区域，请精简内容后重新生成。')
            draw.text((x, y), line, font=font, fill=color, anchor='lt')
            bounds.append({'text':line,'box':list(box)})
            y += step
        return y

    book = data.get('book_title', data['title'])
    if cn(27).getlength(book) > 440:
        raise ValueError('书名过长，请用 book_title 设置简短卡面书名。')
    pill_width = int(cn(30).getlength(card['module']))+42
    if pill_width>500:
        raise ValueError('分类标签过长，请缩短模块名。')
    draw.rounded_rectangle((76,68,76+pill_width,128),radius=18,fill='#8562ce')
    text_lines([card['module']],97,82,cn(30),'#ffffff',40)
    text_lines([book],1004-cn(27).getlength(book),72,cn(27),MUTED,38)
    number = 'N'+str(data['cards'].index(card)+1).zfill(2)
    text_lines([number],1004-en(26).getlength(number),110,en(26),'#8562ce',35)
    if title_font.getlength(card['title']) > 920:
        raise ValueError('标题过长，请缩短到一行。')
    text_lines([card['title']],82,181,title_font,INK,90,275)
    definition = wrap(card['definition'],cn(31),920)
    if len(definition)>1:
        raise ValueError('定义过长，请缩短到一行。')
    text_lines(definition,82,283,cn(31),MUTED,44,321)

    values = [card['question'],card['original'],card['reconstruction'],card['review']]
    for (english,chinese,accent,bg,light,y,height),content in zip(STAGES,values):
        center = 172
        small_icon(draw,english.lower(),center-16,y+height/2-55,32,accent,en(30))
        text_lines([english],center-en(28).getlength(english)/2,y+height/2-7,en(28),accent,36)
        text_lines([chinese],center-cn(27).getlength(chinese)/2,y+height/2+31,cn(27),accent,36)
        x,width,bottom = 282,688,y+height-20
        if english=='Read':
            is_en = is_english(card)
            quoted = card['original_kind']=='逐字引用'
            quote = '“'+content+'”' if quoted else content
            font,step = (en(34),47) if is_en else (cn(35),52)
            lines = wrap(quote,font,width,english=is_en)
            translation = wrap(card['original_translation'],cn(31),width) if card.get('original_translation') else []
            refs = [r['location'] for r in card['sources'] if not r.get('supports') or 'original' in r['supports']]
            locations = wrap('；'.join(dict.fromkeys(refs)),cn(22),width)
            label_height=0 if quoted else 34
            total = len(lines)*step+len(translation)*45+len(locations)*32+(26 if translation else 14)+label_height
            if total>height-40:
                raise ValueError('精读内容过长，请精简而非裁切。')
            top = y+(height-total)/2
            if not quoted:
                top=text_lines(['原文转述'],x,top,cn(22),'#728172',34,bottom)
            top = text_lines(lines,x,top,font,INK,step,bottom)+14
            if translation:
                top = text_lines(translation,x,top,cn(31),'#4f6757',45,bottom)+12
            text_lines(locations,x,top,cn(22),'#728172',32,bottom)
        else:
            font,step = cn(35),51
            lines = wrap(content,font,width)
            if len(lines)*step>height-32:
                raise ValueError(english+'内容过长，请精简后生成。')
            top = y+(height-len(lines)*step)/2
            text_lines(lines,x,top,font,INK,step,bottom)
    portrait=author_image(data,base_dir or Path.cwd())
    emblem=card.get('presentation',{}).get('icon','book')
    if portrait:
        thumb=ImageOps.fit(ImageOps.exif_transpose(Image.open(io.BytesIO(portrait['bytes']))).convert('RGB'),(64,64),method=Image.Resampling.LANCZOS)
        mask=Image.new('L',(64,64),0);ImageDraw.Draw(mask).ellipse((0,0,63,63),fill=255)
        image.paste(thumb,(78,1330),mask);draw=ImageDraw.Draw(image)
        footer=portrait['name']+' · '+portrait['role']+' · '+card['id']
    else:
        if emblem!='none':
            draw.ellipse((78,1330,142,1394),fill='#efe8fb')
            small_icon(draw,emblem,92,1344,36,'#8562ce')
        footer='《'+book+'》 · '+card['module']+' · '+card['id']
    footer_x=158 if portrait or emblem!='none' else 82
    if cn(20).getlength(footer)>1004-footer_x:
        raise ValueError('页脚过长，请缩短书名或分类。')
    text_lines([footer],footer_x,1353,cn(20),MUTED,30,1385)
    output.parent.mkdir(parents=True,exist_ok=True)
    image.save(output)
    output.with_suffix('.layout.json').write_text(json.dumps({'size':[1080,1440], 'card_id':card_id, 'fonts':fonts, 'font_indices':indices, 'style':'pastel-gradient-white-panel', 'main_panel':[48,42,1032,1402], 'stage_icons':['question','read','recite','review'], 'footer_emblem':'portrait' if portrait else emblem, 'paper_color':PAPER, 'panel_gradients':[{'section':en,'from':bg,'to':light} for en,zh,accent,bg,light,y,h in STAGES], 'text_bounds':bounds, 'renderer':'Pillow; not a browser screenshot'},ensure_ascii=False,indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--card-id',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--font')
    parser.add_argument('--title-font')
    parser.add_argument('--english-font')
    parser.add_argument('--font-index',type=int)
    parser.add_argument('--title-font-index',type=int)
    args = parser.parse_args()
    try:
        if args.output.suffix.lower()!='.png' or args.input.resolve() in {args.output.resolve(),args.output.with_suffix('.layout.json').resolve()}:
            raise ValueError('输出必须是独立 .png 文件。')
        pingfang = sorted(Path('/System/Library/AssetsV2/com_apple_MobileAsset_Font8').glob('*/AssetData/PingFang.ttc'))
        candidates = [str(p) for p in pingfang]+[str(Path.home()/'Library/Fonts/微软雅黑.ttf'),'/System/Library/Fonts/Supplemental/Arial Unicode.ttf']
        cn_font = font_path(args.font,candidates)
        title_font = font_path(args.title_font,[cn_font])
        english_font = font_path(args.english_font,['/System/Library/Fonts/Supplemental/Georgia.ttf','/System/Library/Fonts/Supplemental/Times New Roman.ttf'])
        ci = args.font_index if args.font_index is not None else (3 if Path(cn_font).name=='PingFang.ttc' else 0)
        ti = args.title_font_index if args.title_font_index is not None else (11 if Path(title_font).name=='PingFang.ttc' else 0)
        render(load_data(args.input),args.card_id,args.output,[cn_font,title_font,english_font],(ci,ti),args.input.parent)
    except (ValueError,OSError) as exc:
        parser.exit(1,str(exc)+'\n')
    print('已生成分享图：'+str(args.output))


if __name__=='__main__':
    main()
