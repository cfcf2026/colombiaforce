"""Portada de una nota (1200x630): foto de referencia oscurecida, titular corto en blanco
con una palabra resaltada en amarillo, subtítulo y hasta 3 cifras clave."""
import io
import ipaddress
import pathlib
import socket
import urllib.request
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageChops

W, H = 1200, 630
NAVY, NAVY2, YELLOW, RED, WHITE, GRAY, SHADOW = '#0a1230', '#1b2963', '#ffd21a', '#d6182f', '#ffffff', '#c4cde6', '#04081a'
MARGIN = 64
MAX_BYTES = 15 * 1024 * 1024
FOCOS = {'arriba': 0.0, 'centro': 0.5, 'abajo': 1.0}
FONTS = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
]


def font(size):
    for path in FONTS:
        if pathlib.Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def plain(text):
    return text.replace('*', '').strip()


def parse_marked(text):
    """'Fuerza de Tarea *URANO*' -> [('Fuerza', False), ..., ('URANO', True)]"""
    words, hl, cur = [], False, ''
    for ch in text:
        if ch == '*':
            if cur:
                words.append((cur, hl))
                cur = ''
            hl = not hl
        elif ch.isspace():
            if cur:
                words.append((cur, hl))
                cur = ''
        else:
            cur += ch
    if cur:
        words.append((cur, hl))
    return words


def parse_stats(text):
    """'86 %|de avance; 60.000 m²|de obra' -> [('86 %', 'de avance'), ...]"""
    out = []
    for part in text.split(';'):
        part = part.strip()
        if part:
            val, _, label = part.partition('|')
            out.append((val.strip(), label.strip()))
    return out


def _check_host(host):
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except OSError:
        raise ValueError('no pude encontrar el sitio de la foto (%s)' % host)
    for info in infos:
        if not ipaddress.ip_address(info[4][0]).is_global:
            raise ValueError('la dirección de la foto no es pública')


def load_photo(ref):
    """Carga la foto de referencia desde `referencias/...` (en el repositorio) o un enlace https."""
    if ref.startswith('https://'):
        _check_host(urlparse(ref).hostname or '')
        req = urllib.request.Request(ref, headers={'User-Agent': 'Mozilla/5.0 (ColombiaForce)'})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                _check_host(urlparse(r.geturl()).hostname or '')
                ctype = r.headers.get('Content-Type', '')
                if not ctype.startswith('image/'):
                    raise ValueError('el enlace no devuelve una imagen (tipo: %s). Si es un adjunto de GitHub o una página web, sube la foto a la carpeta `referencias/`' % (ctype or 'desconocido'))
                data = r.read(MAX_BYTES + 1)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError('no pude descargar la foto (%s). Sube la foto a la carpeta `referencias/` y usa esa ruta' % exc)
        if len(data) > MAX_BYTES:
            raise ValueError('la foto pesa más de 15 MB')
        img = Image.open(io.BytesIO(data))
    else:
        path = pathlib.Path(ref)
        if not ref.startswith('referencias/') or '..' in path.parts or not path.is_file():
            raise ValueError('no encontré el archivo `%s` (debe estar en la carpeta `referencias/` del proyecto)' % ref)
        img = Image.open(path)
    # Se re-codifica desde cero: la portada final no conserva metadatos (GPS, cámara, etc.).
    return ImageOps.exif_transpose(img).convert('RGB')


def _fill(img, focus):
    scale = max(W / img.width, H / img.height)
    nw, nh = round(img.width * scale), round(img.height * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - W) // 2, round((nh - H) * focus)
    return img.crop((left, top, left + W, top + H))


def _background(photo, focus):
    if photo is None:
        mask = Image.linear_gradient('L').resize((W, H)).point(lambda p: int(p * 0.5))
        return Image.composite(Image.new('RGB', (W, H), NAVY2), Image.new('RGB', (W, H), NAVY), mask)
    img = _fill(photo, focus)
    vert = Image.linear_gradient('L').resize((W, H)).point(lambda p: int(70 + p * 0.55))
    side = ImageOps.invert(Image.linear_gradient('L').transpose(Image.ROTATE_90)).resize((W, H)).point(lambda p: int(p * 0.62))
    return Image.composite(Image.new('RGB', (W, H), NAVY), img, ImageChops.lighter(vert, side))


def _wrap(draw, words, fnt, max_w):
    space = draw.textlength(' ', font=fnt)
    lines, cur, cur_w = [], [], 0
    for w, hl in words:
        ww = draw.textlength(w, font=fnt)
        add = ww if not cur else space + ww
        if cur and cur_w + add > max_w:
            lines.append(cur)
            cur, cur_w = [(w, hl)], ww
        else:
            cur.append((w, hl))
            cur_w += add
    if cur:
        lines.append(cur)
    return lines


def _line_w(draw, line, fnt):
    space = draw.textlength(' ', font=fnt)
    return sum(draw.textlength(w, font=fnt) for w, _ in line) + space * (len(line) - 1)


def _draw_line(draw, x, y, line, fnt, base, shadow=True):
    space = draw.textlength(' ', font=fnt)
    for w, hl in line:
        if shadow:
            draw.text((x + 3, y + 3), w, font=fnt, fill=SHADOW, anchor='ls')
        draw.text((x, y), w, font=fnt, fill=YELLOW if hl else base, anchor='ls')
        x += draw.textlength(w, font=fnt) + space


def make_cover(headline, subtitle, stats_text, photo, focus, name, out_dir='public/images'):
    """Crea public/images/<name>.jpg y devuelve su ruta pública (/images/<name>.jpg)."""
    img = _background(photo, FOCOS.get(focus, 0.5))
    d = ImageDraw.Draw(img)

    # Marca arriba
    d.rectangle([MARGIN, 52, MARGIN + 12, 86], fill=YELLOW)
    d.text((MARGIN + 30, 69), 'COLOMBIA FORCE', font=font(30), fill=WHITE, anchor='lm')
    d.text((W - MARGIN, 69), 'colombiaforce.com', font=font(24), fill=GRAY, anchor='rm')

    # De abajo hacia arriba: cifras, subtítulo, línea amarilla, titular
    y = H - 50
    stats = parse_stats(stats_text)[:3]
    if stats:
        vf, lf = font(58), font(24)
        x, top = MARGIN, y - 92
        for i, (val, label) in enumerate(stats):
            w = max(d.textlength(val, font=vf), d.textlength(label, font=lf))
            d.text((x, top + 52), val, font=vf, fill=YELLOW, anchor='ls')
            d.text((x, top + 86), label, font=lf, fill=WHITE, anchor='ls')
            x += w + 28
            if i < len(stats) - 1:
                d.rectangle([x, top + 8, x + 2, top + 86], fill=GRAY)
                x += 30
        y = top - 28

    sub = parse_marked(plain(subtitle)) if subtitle else []
    if sub:
        sf = font(34)
        lines = _wrap(d, sub, sf, 820)[:2]
        y -= 44 * len(lines) - 10
        for i, line in enumerate(lines):
            _draw_line(d, MARGIN, y + 44 * i + 34, line, sf, WHITE)
        y -= 20
    else:
        y += 6

    d.rectangle([MARGIN, y - 8, MARGIN + 150, y], fill=YELLOW)
    y -= 8 + 24

    words = parse_marked(headline.upper())
    max_w, top_limit = W - 2 * MARGIN, 118
    chosen = None
    for size in range(112, 51, -4):
        fnt = font(size)
        lines = _wrap(d, words, fnt, max_w)
        line_h = int(size * 1.06)
        if len(lines) * line_h <= y - top_limit and all(_line_w(d, l, fnt) <= max_w for l in lines):
            chosen = (fnt, lines, line_h)
            break
    if chosen is None:
        fnt = font(52)
        chosen = (fnt, _wrap(d, words, fnt, max_w), int(52 * 1.06))
    fnt, lines, line_h = chosen
    first = y - line_h * (len(lines) - 1)
    for i, line in enumerate(lines):
        _draw_line(d, MARGIN, first + i * line_h, line, fnt, WHITE)

    d.rectangle([0, H - 14, W, H], fill=RED)

    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    img.save(out / (name + '.jpg'), 'JPEG', quality=86, optimize=True, progressive=True)
    return '/images/%s.jpg' % name
