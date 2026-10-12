#!/usr/bin/env python3
"""Convierte un issue "NOTA: ..." en dos notas del blog (es y en), con validaciones y portada."""
import datetime
import json
import os
import pathlib
import re
import sys

BLOG = pathlib.Path('src/content/blog')
SITE = 'https://colombiaforce.com'
CATS = ('operativos', 'incautaciones', 'capturados', 'bajas', 'otros')
FOCOS = ('arriba', 'centro', 'abajo')
SLUG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
URL_RE = re.compile(r'^https://[^\s/]+\.[^\s/]+/\S*$|^https://[^\s/]+\.[^\s/]+$')
PLANTILLA_ARCHIVO, PLANTILLA_SLUG = 'nombre-en-espanol-sin-tildes', 'english-url-slug'

errors, warnings = [], []


def finish(ok, text):
    pathlib.Path('comment.md').write_text(text.strip() + '\n', encoding='utf-8')
    out = os.environ.get('GITHUB_OUTPUT')
    if out:
        with open(out, 'a', encoding='utf-8') as f:
            f.write('ok=%s\n' % ('true' if ok else 'false'))
    sys.exit(0)


def read_body():
    with open(os.environ['GITHUB_EVENT_PATH'], encoding='utf-8') as f:
        ev = json.load(f)
    body = ev['issue'].get('body') or ''
    return body.replace('\r\n', '\n').replace('\r', '\n')


def kv(text):
    d = {}
    for m in re.finditer(r'^([A-Z_]+):[ \t]*(.*)$', text, re.M):
        d.setdefault(m.group(1), m.group(2).strip())
    return d


def section(sec, name):
    m = re.search(r'^CUERPO:[ \t]*\n', sec, re.M)
    if not m:
        errors.append('Sección %s: falta la línea `CUERPO:`.' % name)
        return {}, ''
    return kv(sec[:m.start()]), sec[m.end():].strip()


def effective_slugs(lang):
    res = {}
    for p in sorted((BLOG / lang).glob('*.md*')):
        txt = p.read_text(encoding='utf-8')
        m = re.search(r'^urlSlug:\s*["\']?([^"\'\n]+)', txt, re.M)
        res[(m.group(1).strip() if m else p.stem)] = p.name
    return res


def nums(text):
    found = re.findall(r'\d[\d.,]*\d|\d', text)
    return {re.sub(r'[.,]', '', x) for x in found}


def front(title, desc, date, cat, depts, image, alt, url_slug=None):
    q = lambda v: json.dumps(v, ensure_ascii=False)
    lines = ['---', 'title: ' + q(title), 'description: ' + q(desc),
             'pubDate: ' + date.isoformat(), 'category: ' + cat]
    if depts:
        lines.append('departments: ' + q(depts))
    if image:
        lines.append('heroImage: ' + q(image))
        if alt:
            lines.append('imageAlt: ' + q(alt))
    if url_slug:
        lines.append('urlSlug: ' + q(url_slug))
    lines.append('---')
    return '\n'.join(lines) + '\n\n'


try:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import portada

    body = read_body()
    me = re.search(r'^=== ES ===[ \t]*$', body, re.M)
    mn = re.search(r'^=== EN ===[ \t]*$', body, re.M)
    if not me or not mn or me.start() > mn.start():
        finish(False, '❌ No publiqué nada. Faltan los separadores `=== ES ===` y `=== EN ===` (en ese orden).')

    head = kv(body[:me.start()])
    es_h, es_b = section(body[me.end():mn.start()], 'ES')
    en_h, en_b = section(body[mn.end():], 'EN')

    archivo = head.get('ARCHIVO', '')
    slug_en = head.get('SLUG_EN', '')
    cat = head.get('CATEGORIA', '').lower()
    url = head.get('FUENTE_URL', '')
    imagen = head.get('IMAGEN', '')
    foto = head.get('FOTO', '')
    credito = head.get('FOTO_CREDITO', '')
    foco = (head.get('FOTO_ENFOQUE', '') or 'centro').lower()
    need_cover = not imagen and head.get('PORTADA', '').lower() != 'no'
    presuntos = head.get('PRESUNTOS', '').lower() in ('si', 'sí', 'yes')
    depts = [d.strip() for d in head.get('DEPARTAMENTOS', '').split(',') if d.strip()]

    for label, val in (('ARCHIVO', archivo), ('SLUG_EN', slug_en)):
        if not SLUG_RE.match(val):
            errors.append('`%s` debe tener solo minúsculas, números y guiones (ej: `mi-nota`).' % label)
    if cat not in CATS:
        errors.append('`CATEGORIA` debe ser una de: %s.' % ', '.join(CATS))
    if not URL_RE.match(url):
        errors.append('`FUENTE_URL` debe ser el enlace completo de la fuente (ej: `https://www.presidencia.gov.co/...`).')
    if archivo == PLANTILLA_ARCHIVO or slug_en == PLANTILLA_SLUG:
        errors.append('`ARCHIVO` o `SLUG_EN` siguen con el valor de ejemplo de la plantilla. ¿Pegaste tu paquete encima del texto de ejemplo?')

    date = None
    try:
        date = datetime.date.fromisoformat(head.get('FECHA', ''))
        if date > datetime.date.today() + datetime.timedelta(days=1):
            errors.append('`FECHA` está en el futuro (%s).' % date)
    except ValueError:
        errors.append('`FECHA` debe tener el formato AAAA-MM-DD (ej: 2026-10-12).')

    valid = set()
    dep_file = pathlib.Path('src/departments.ts')
    if dep_file.exists():
        valid = set(re.findall(r'value: "([^"]+)"', dep_file.read_text(encoding='utf-8')))
    bad = [d for d in depts if d not in valid]
    if bad:
        errors.append('Departamentos no reconocidos: %s. Deben escribirse como en el panel (ej: `ANTIOQUIA`, `NARIÑO`).' % ', '.join(bad))

    if SLUG_RE.match(archivo):
        if (BLOG / 'es' / (archivo + '.md')).exists() or (BLOG / 'en' / (archivo + '.md')).exists():
            errors.append('Ya existe una nota con el archivo `%s`. Elige otro nombre.' % archivo)
        if archivo in effective_slugs('es'):
            errors.append('La dirección en español `%s` ya está en uso.' % archivo)
    if SLUG_RE.match(slug_en) and slug_en in effective_slugs('en'):
        errors.append('La dirección en inglés `%s` ya está en uso.' % slug_en)

    if imagen and not (imagen.startswith('/images/') and pathlib.Path('public' + imagen).is_file()):
        errors.append('`IMAGEN` debe ser una ruta que exista en el sitio (ej: `/images/foto.png`). Déjala vacía para usar la portada automática.')
    if foto and not (foto.startswith('referencias/') or URL_RE.match(foto)):
        errors.append('`FOTO` debe ser un archivo de la carpeta `referencias/` (ej: `referencias/renacer.jpg`) o un enlace `https://` directo a la imagen.')
    if foco not in FOCOS:
        errors.append('`FOTO_ENFOQUE` debe ser: %s.' % ', '.join(FOCOS))

    for name, h, b in (('ES', es_h, es_b), ('EN', en_h, en_b)):
        t, d = h.get('TITULO', ''), h.get('DESCRIPCION', '')
        if not t or len(t) > 120:
            errors.append('%s: `TITULO` es obligatorio y debe tener máximo 120 caracteres.' % name)
        if not d or len(d) > 200:
            errors.append('%s: `DESCRIPCION` es obligatoria y debe tener máximo 200 caracteres.' % name)
        if len(b) < 200:
            errors.append('%s: el cuerpo es demasiado corto (mínimo 200 caracteres).' % name)
        if need_cover:
            ct = portada.plain(h.get('PORTADA_TITULO', ''))
            if not ct or len(ct) > 40 or len(ct.split()) > 6:
                errors.append('%s: `PORTADA_TITULO` es obligatorio (máx. 6 palabras y 40 caracteres). Resalta una palabra entre asteriscos, ej: `Fuerza de Tarea *URANO*`.' % name)
            if len(portada.plain(h.get('PORTADA_SUB', ''))) > 70:
                errors.append('%s: `PORTADA_SUB` debe tener máximo 70 caracteres.' % name)
            stats = portada.parse_stats(h.get('PORTADA_DATOS', ''))
            if len(stats) > 3:
                errors.append('%s: `PORTADA_DATOS` admite máximo 3 cifras.' % name)
            for val, label in stats:
                if not val or not label or len(val) > 10 or len(label) > 22:
                    errors.append('%s: cada cifra de `PORTADA_DATOS` va como `valor|etiqueta` (valor máx. 10 caracteres, etiqueta máx. 22). Revisa `%s|%s`.' % (name, val, label))
                elif not nums(val) <= nums(b):
                    warnings.append('%s: la cifra `%s` de la portada no aparece en el texto de la nota.' % (name, val))

    if errors:
        finish(False, '❌ **No publiqué nada.** Corrige esto y crea un issue nuevo:\n\n' + '\n'.join('- ' + e for e in errors))

    diff = sorted(nums(es_b) ^ nums(en_b))
    if diff:
        warnings.append('Estas cifras aparecen en un solo idioma: %s. Puede ser por conversiones (millones/billion); revísalas.' % ', '.join(diff))

    es_tail = ['*Las cifras y afirmaciones son las reportadas por las fuentes oficiales y no han sido verificadas de forma independiente.']
    en_tail = ['*Figures and claims are those reported by official sources and have not been independently verified.']
    if presuntos:
        es_tail.append('Las personas capturadas o señaladas se consideran presuntas responsables hasta que un juez decida lo contrario.')
        en_tail.append('People who have been arrested or named are presumed innocent until a judge rules otherwise.')
    es_tail = ' '.join(es_tail) + '*'
    en_tail = ' '.join(en_tail) + '*'

    es_src = '**Fuente:** [%s](%s).' % (es_h.get('FUENTE', 'Fuente oficial'), url)
    en_src = '**Source:** [%s](%s).' % (en_h.get('FUENTE', 'Official source'), url)

    img_es = img_en = imagen
    alt_es, alt_en = head.get('ALT_ES', ''), head.get('ALT_EN', '')
    auto_cover = False
    if need_cover:
        try:
            photo = portada.load_photo(foto) if foto else None
        except Exception as exc:
            finish(False, '❌ **No publiqué nada.** No pude usar la foto de referencia: %s.' % exc)
        img_es = portada.make_cover(es_h['PORTADA_TITULO'], es_h.get('PORTADA_SUB', ''), es_h.get('PORTADA_DATOS', ''), photo, foco, archivo + '-es')
        img_en = portada.make_cover(en_h['PORTADA_TITULO'], en_h.get('PORTADA_SUB', ''), en_h.get('PORTADA_DATOS', ''), photo, foco, archivo + '-en')
        alt_es = alt_es or 'Portada: ' + portada.plain(es_h['PORTADA_TITULO'])
        alt_en = alt_en or 'Cover: ' + portada.plain(en_h['PORTADA_TITULO'])
        auto_cover = True
        if foto and credito:
            es_src += '\n\n**Imagen:** %s.' % credito
            en_src += '\n\n**Image:** %s.' % credito
        elif foto:
            warnings.append('Usaste una foto de referencia sin `FOTO_CREDITO`. Agrégale el crédito (quién la tomó o publicó) y confirma que puedes usarla.')
        if foto and foto.startswith('https://'):
            warnings.append('La foto vino de un enlace externo: confirma que tienes derecho a usarla.')

    es_doc = front(es_h['TITULO'], es_h['DESCRIPCION'], date, cat, depts, img_es, alt_es) \
        + es_b + '\n\n' + es_tail + '\n\n' + es_src + '\n'
    en_doc = front(en_h['TITULO'], en_h['DESCRIPCION'], date, cat, depts, img_en, alt_en, slug_en) \
        + en_b + '\n\n' + en_tail + '\n\n' + en_src + '\n'

    (BLOG / 'es').mkdir(parents=True, exist_ok=True)
    (BLOG / 'en').mkdir(parents=True, exist_ok=True)
    (BLOG / 'es' / (archivo + '.md')).write_text(es_doc, encoding='utf-8')
    (BLOG / 'en' / (archivo + '.md')).write_text(en_doc, encoding='utf-8')

    msg = [
        '✅ **Nota creada y enviada a publicación.** Estará en línea en 1 o 2 minutos.',
        '',
        '- ES: %s/es/blog/%s/' % (SITE, archivo),
        '- EN: %s/en/blog/%s/' % (SITE, slug_en),
        '',
        '**Después de publicar:** purga la caché de Cloudflare y pide la indexación de las dos direcciones en Search Console.',
    ]
    if auto_cover:
        msg.append('Se generó la **portada** de cada idioma%s. Si quieres cambiarla, reemplázala desde `colombiaforce.com/admin/` (campo "Imagen principal").' % (' a partir de tu foto de referencia' if foto else ' (sin foto, solo con el estilo de marca)'))
    elif not imagen:
        msg.append('Esta nota no tiene imagen: agrégala desde `colombiaforce.com/admin/` (campo "Imagen principal", en cada idioma).')
    if warnings:
        msg += ['', '⚠️ **Avisos (no bloquean la publicación):**'] + ['- ' + w for w in warnings]
    finish(True, '\n'.join(msg))

except SystemExit:
    raise
except Exception as exc:  # cualquier fallo inesperado: no publicar y avisar
    finish(False, '❌ Error inesperado, no publiqué nada: `%s`' % exc)
