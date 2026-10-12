"""Genera una portada de marca (1200x630) a partir del título de la nota."""
import pathlib

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BG, YELLOW, RED, WHITE, GRAY = '#0a1230', '#ffd21a', '#d6182f', '#ffffff', '#8fa0c8'
MARGIN = 64

CATEGORIES = {
    'es': {'operativos': 'Operativos', 'incautaciones': 'Incautaciones',
           'sometimientos': 'Sometimientos', 'bajas': 'Bajas'},
    'en': {'operativos': 'Operations', 'incautaciones': 'Seizures',
           'sometimientos': 'Surrenders', 'bajas': 'Casualties'},
}
MONTHS = {
    'es': ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'],
    'en': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
}
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


def wrap(draw, text, fnt, max_w):
    lines, cur = [], ''
    for word in text.split():
        trial = (cur + ' ' + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def make_cover(title, category, date, lang, name, out_dir='public/images'):
    """Crea public/images/<name>.jpg y devuelve su ruta pública (/images/<name>.jpg)."""
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)

    # Marca: barra amarilla + nombre
    d.rectangle([MARGIN, 58, MARGIN + 14, 94], fill=YELLOW)
    d.text((MARGIN + 34, 76), 'COLOMBIA FORCE', font=font(32), fill=WHITE, anchor='lm')

    # Categoría
    label = CATEGORIES[lang].get(category, category).upper()
    d.text((MARGIN, 150), label, font=font(30), fill=YELLOW, anchor='lm')

    # Título: el tamaño más grande que quepa en el área disponible
    max_w, top, bottom = W - 2 * MARGIN, 190, 540
    chosen = None
    for size in range(84, 43, -4):
        fnt = font(size)
        lines = wrap(d, title, fnt, max_w)
        line_h = int(size * 1.2)
        if len(lines) * line_h <= bottom - top and all(d.textlength(l, font=fnt) <= max_w for l in lines):
            chosen = (fnt, lines, line_h)
            break
    if chosen is None:
        fnt = font(44)
        chosen = (fnt, wrap(d, title, fnt, max_w), int(44 * 1.2))
    fnt, lines, line_h = chosen
    y = top
    for line in lines:
        d.text((MARGIN, y), line, font=fnt, fill=WHITE, anchor='lt')
        y += line_h

    # Pie: fecha y dominio, y franja roja
    month = MONTHS[lang][date.month - 1]
    txt = f'{date.day} {month} {date.year}' if lang == 'es' else f'{month} {date.day}, {date.year}'
    d.text((MARGIN, 578), txt.upper(), font=font(26), fill=GRAY, anchor='lm')
    d.text((W - MARGIN, 578), 'colombiaforce.com', font=font(26), fill=GRAY, anchor='rm')
    d.rectangle([0, H - 14, W, H], fill=RED)

    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    img.save(out / (name + '.jpg'), 'JPEG', quality=86, optimize=True, progressive=True)
    return '/images/%s.jpg' % name
