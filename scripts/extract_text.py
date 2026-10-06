#!/usr/bin/env python3
"""Extract plain text from local txt/md/html/epub/docx/pdf files for card making.

Standard library only. PDF needs `pdftotext` (poppler) or an installed `pypdf`;
scanned PDFs need OCR first and are reported, never guessed. Nothing is uploaded.
Usage: python3 extract_text.py INPUT [--output OUT]
"""
import argparse
import html
import posixpath
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from html.parser import HTMLParser
from pathlib import Path

BLOCK_TAGS = {'p', 'div', 'br', 'li', 'tr', 'section', 'article', 'blockquote', 'pre',
              'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'ul', 'ol', 'hr'}
W_NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
READABLE = {'.txt', '.md', '.markdown', '.text', '.html', '.htm', '.xhtml', '.epub', '.docx', '.pdf'}


class _HTMLText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
        if tag in BLOCK_TAGS:
            self.parts.append('\n')

    def handle_startendtag(self, tag, attrs):
        if tag in BLOCK_TAGS:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skip:
            self.skip -= 1
        if tag in BLOCK_TAGS:
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def tidy(text):
    text = text.replace('\u00a0', ' ').replace('\ufeff', '')
    text = re.sub(r'[ \t\r\f\v]+', ' ', text)
    text = re.sub(r' *\n *', '\n', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def from_html(raw):
    parser = _HTMLText()
    parser.feed(raw)
    parser.close()
    return tidy(''.join(parser.parts))


def from_epub(path):
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        rootfile = 'OEBPS/content.opf'
        if 'META-INF/container.xml' in names:
            container = ET.fromstring(archive.read('META-INF/container.xml'))
            found = container.find('.//{*}rootfile')
            if found is not None and found.get('full-path'):
                rootfile = found.get('full-path')
        if rootfile not in names:
            candidates = [n for n in names if n.endswith('.opf')]
            if not candidates:
                raise ValueError('EPUB 缺少可识别的 OPF 清单')
            rootfile = sorted(candidates)[0]
        base = posixpath.dirname(rootfile)
        opf = ET.fromstring(archive.read(rootfile))
        manifest = {}
        for item in opf.findall('.//{*}manifest/{*}item'):
            if item.get('id') and item.get('href'):
                manifest[item.get('id')] = (item.get('href'), item.get('media-type', ''))
        order = [s.get('idref') for s in opf.findall('.//{*}spine/{*}itemref')]
        order = [i for i in order if i in manifest] or list(manifest)
        chunks = []
        for index, ident in enumerate(order, 1):
            href, media = manifest[ident]
            if media and 'html' not in media and 'xml' not in media:
                continue
            target = posixpath.normpath(posixpath.join(base, href)) if base else href
            if target not in names:
                continue
            body = from_html(archive.read(target).decode('utf-8', 'replace'))
            if body:
                chunks.append(f'[EPUB 章节 {index}｜{href}]\n{body}')
        if not chunks:
            raise ValueError('EPUB 未提取到正文，可能是图片版或 DRM 受限')
        return '\n\n'.join(chunks)


def from_docx(path):
    with zipfile.ZipFile(path) as archive:
        if 'word/document.xml' not in archive.namelist():
            raise ValueError('DOCX 缺少 word/document.xml')
        root = ET.fromstring(archive.read('word/document.xml'))
    lines = []
    for para in root.iter(W_NS + 'p'):
        parts = []
        for node in para.iter():
            if node.tag == W_NS + 't':
                parts.append(node.text or '')
            elif node.tag == W_NS + 'tab':
                parts.append('\t')
            elif node.tag in (W_NS + 'br', W_NS + 'cr'):
                parts.append('\n')
        line = ''.join(parts).strip()
        if line:
            lines.append(line)
    if not lines:
        raise ValueError('DOCX 未提取到文字，内容可能在文本框或图片中')
    return tidy('\n\n'.join(lines))


def from_pdf(path):
    try:
        import pypdf  # noqa: F401
    except ImportError:
        pypdf = None
    if pypdf is not None:
        reader = pypdf.PdfReader(str(path))
        pages = [f'[PDF 第 {i} 页]\n{page.extract_text() or ""}' for i, page in enumerate(reader.pages, 1)]
        text = tidy('\n\n'.join(pages))
        if text:
            return text
        raise ValueError('PDF 没有可用文字层，可能是扫描件，需要先 OCR')
    tool = shutil.which('pdftotext')
    if not tool:
        raise ValueError('PDF 需要安装 poppler 的 pdftotext 或 Python 包 pypdf；扫描件还需先做 OCR')
    done = subprocess.run([tool, '-enc', 'UTF-8', '-layout', str(path), '-'],
                          capture_output=True, text=True)
    if done.returncode != 0 or not done.stdout.strip():
        raise ValueError('pdftotext 未输出文字，可能是扫描件或受保护 PDF，需要先 OCR')
    return tidy(done.stdout)


def extract(path):
    suffix = path.suffix.lower()
    if suffix not in READABLE:
        raise ValueError(f'不支持的格式：{suffix or "无扩展名"}（支持 {", ".join(sorted(READABLE))}）')
    if suffix == '.pdf':
        return from_pdf(path)
    if suffix == '.epub':
        return from_epub(path)
    if suffix == '.docx':
        return from_docx(path)
    raw = path.read_text(encoding='utf-8', errors='replace')
    return from_html(raw) if suffix in ('.html', '.htm', '.xhtml') else tidy(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        if not args.input.is_file():
            raise ValueError(f'找不到文件：{args.input}')
        text = extract(args.input)
        if args.output:
            if args.output.resolve() == args.input.resolve():
                raise ValueError('输出不能覆盖原文件')
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding='utf-8')
            print(f'已提取 {len(text)} 字 → {args.output.resolve()}')
        else:
            print(text)
        print(f'来源：{args.input.name}｜字数：{len(text)}｜说明：提取的是文字层，扫描件需先 OCR。', file=sys.stderr)
        return 0
    except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f'提取失败：{exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
