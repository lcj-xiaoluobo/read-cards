"""Small, offline SVG icons and optional locally sourced author portraits."""
import base64
from pathlib import Path

BACKGROUND_CORNERS = ('#cfdffd', '#ffebca', '#c7b8e5', '#f2c6d2')


def background_uri():
    """Four-corner sRGB wash, matching the PNG renderer's corner colors."""
    tl,tr,bl,br=BACKGROUND_CORNERS
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1440" preserveAspectRatio="none">
<defs><linearGradient id="top"><stop stop-color="{tl}"/><stop offset="1" stop-color="{tr}"/></linearGradient>
<linearGradient id="bottom"><stop stop-color="{bl}"/><stop offset="1" stop-color="{br}"/></linearGradient>
<linearGradient id="fade" x2="0" y2="1"><stop stop-color="white" stop-opacity="0"/><stop offset="1" stop-color="white" stop-opacity="1"/></linearGradient>
<mask id="mix" maskContentUnits="objectBoundingBox"><rect width="1" height="1" fill="url(#fade)"/></mask></defs>
<rect width="1080" height="1440" fill="url(#top)"/><rect width="1080" height="1440" fill="url(#bottom)" mask="url(#mix)"/></svg>'''
    return 'data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode('ascii')

PATHS = {
    'question': '<path d="M4 4h24v21H12l-6 4v-4H4zM12 10a4 4 0 0 1 8 0c0 3-4 3-4 6"/><circle cx="16" cy="20" r=".8"/>',
    'read': '<path d="M4 7h8l4 3 4-3h8v18h-8l-4 3-4-3H4zM16 10v18M8 12h4M20 12h4M8 17h4M20 17h4"/>',
    'recite': '<path d="M5 6h22v16H14l-7 5v-5H5zM10 12h12M10 17h8"/>',
    'review': '<path d="M25 12a10 10 0 1 0 1 8M25 5v8h-8"/>',
    'survey': '<path d="m4 8 8-3 8 3 8-3v20l-8 3-8-3-8 3zM12 5v20M20 8v20"/>',
    'growth': '<path d="M16 27V15M16 19C6 19 5 12 5 8c7 0 11 3 11 11ZM16 15c0-8 4-11 11-11 0 7-4 11-11 11ZM10 27h12"/>',
    'book': '<path d="M4 7h8l4 3 4-3h8v18h-8l-4 3-4-3H4zM16 10v18"/>',
    'compass': '<circle cx="16" cy="16" r="12"/><path d="m21 10-3 8-8 4 4-9z"/>',
}


def icon_svg(name):
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+PATHS[name]+'</svg>'


def author_image(data, base_dir):
    """Read only a declared local raster portrait; no network calls or guessed identity."""
    badge = data.get('author_badge')
    if not badge:
        return None
    path = Path(badge['portrait_file'])
    if not path.is_absolute():
        path = Path(base_dir)/path
    raw = path.read_bytes()
    if len(raw)>8_000_000:
        raise ValueError('作者头像应小于 8 MB，请使用分享用小图。')
    if raw.startswith(b'\x89PNG\r\n\x1a\n'):
        mime='image/png'
    elif raw.startswith(b'\xff\xd8\xff'):
        mime='image/jpeg'
    elif raw[:4]==b'RIFF' and raw[8:12]==b'WEBP':
        mime='image/webp'
    else:
        raise ValueError('作者头像只接受本地 PNG、JPEG 或 WebP。')
    return {**badge,'bytes':raw,'uri':'data:'+mime+';base64,'+base64.b64encode(raw).decode('ascii')}
