"""Drawing base of diagram.py: colors, reading profiles, the SVG canvas and boxes with text."""
import os
import sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import icons  # noqa: E402


BG = '#FAF9F6'
INK, SOFT = '#2B2B33', '#55555F'
# fill (inner boxes), border, strong (text, icons and arrows on that color), tint (the box itself, stronger)
PALETTE = {
    'blue': ('#EAF1FF', '#7FA8F0', '#1F4E9C', '#D3E2FF'),
    'green': ('#E4F6EC', '#6FC39C', '#17694A', '#C9ECD9'),
    'orange': ('#FFF5D9', '#E2B84A', '#6E4D00', '#FFE7A6'),
    'red': ('#FFEBE4', '#EE9478', '#963019', '#FFD3C5'),
    'purple': ('#F2EBFC', '#A989E6', '#4F2F8C', '#E0D1F8'),
    'teal': ('#E2F5F5', '#74C2C2', '#125B5B', '#C6E9E9'),
    'gray': ('#F4F2ED', '#B9B2A5', '#45454F', '#E4E0D6'),
}
# the title underline: the theme colors left to right
GRADIENT = ('blue', 'purple', 'red', 'orange')
KIND_COLOR = {'start': 'gray', 'step': 'blue', 'decision': 'orange', 'end': 'green'}
# sizes per reading profile: width, body, title, small text; a 6" screen needs bigger letters
PROFILES = {'large': {'width': 960, 'body': 20, 'title': 26, 'small': 16},
            'small': {'width': 480, 'body': 14, 'title': 17, 'small': 12.5}}
MAX_ELEMENTS = 7  # references/VISUALS.md: more than ~7 main elements overloads the reader
TYPES = ('flow', 'timeline', 'compare', 'boxes', 'layers', 'tree', 'sequence', 'bars', 'cards', 'scene', 'chord',
         'fretboard', 'tab')
SCENE_OPS = ('→', '+', '=', '↔')


class Canvas:
    def __init__(self, profile):
        self.p = PROFILES[profile]
        self.w = self.p['width']
        self.pad = round(self.w * 0.04)
        self.parts, self.problems, self.y = [], [], 0

    # text measures: an average sans-serif letter is ~0.56 em wide, a monospace one 0.6 em
    def width_of(self, text, size, mono=False):
        return len(text) * size * (0.6 if mono else 0.56)

    def wrap(self, text, size, width, mono=False, report=True):
        """Splits text into lines that fit the width; reports a word that cannot fit at all (unless report=False,
        for measuring before drawing)."""
        text = str(text)
        limit = max(1, int(width / (size * (0.6 if mono else 0.56))))
        lines, line = [], ''
        for word in text.split():
            if len(word) > limit and report:
                self.problems.append(f'"{word}" does not fit in {round(width)} px: shorten it or widen the box')
            candidate = f'{line} {word}'.strip()
            if len(candidate) <= limit or not line:
                line = candidate
            else:
                lines.append(line)
                line = word
        return lines + [line] if line or not lines else lines

    def rect(self, x, y, w, h, color='gray', rx=12, dashed=False, shadow=True, tint=False):
        fill, border, _, strong_fill = PALETTE[color]
        fill = strong_fill if tint else fill
        if shadow:
            self.parts.append(f'<rect x="{x}" y="{y + 4}" width="{w}" height="{h}" rx="{rx}" '
                              f'fill="#3A3226" opacity="0.07"/>')
        dash = ' stroke-dasharray="9 6"' if dashed else ''
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
                          f'stroke="{border}" stroke-width="2"{dash}/>')

    def diamond(self, cx, y, w, h, color='orange'):
        _, border, _, fill = PALETTE[color]
        pts = f'{cx},{y} {cx + w / 2},{y + h / 2} {cx},{y + h} {cx - w / 2},{y + h / 2}'
        self.parts.append(f'<polygon points="{pts}" fill="{fill}" stroke="{border}" stroke-width="2"/>')

    def text(self, x, y, value, size=None, weight=400, anchor='middle', fill=INK, mono=False, italic=False):
        size = size or self.p['body']
        family = "'Courier New', Menlo, monospace" if mono else 'system-ui, -apple-system, sans-serif'
        style = ' font-style="italic"' if italic else ''
        self.parts.append(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
                          f'font-weight="{weight}" text-anchor="{anchor}" fill="{fill}"{style}>'
                          f'{escape(str(value))}</text>')

    def lines(self, x, y, lines, size=None, **kw):
        size = size or self.p['body']
        for i, line in enumerate(lines):
            self.text(x, y + size + i * size * 1.3, line, size=size, **kw)
        return len(lines) * size * 1.3

    def shift(self, start, dy):
        """Moves everything drawn since parts[start] down by dy (up when negative)."""
        if dy:
            self.parts[start:] = [f'<g transform="translate(0,{dy:g})">' + ''.join(self.parts[start:]) + '</g>']

    def unknown_icon(self, name):
        near = icons.suggest(name)
        self.problems.append(f'unknown icon "{name}"' + (f' (did you mean {", ".join(near)}?)' if near else ''))

    def icon(self, name, x, y, size, color):
        """Draws a named icon in the color's strong tone; an unknown name is reported, with suggestions."""
        if not icons.known(name):
            self.unknown_icon(name)
            return False
        self.parts.append(icons.draw(name, x, y, size, PALETTE[color][2]))
        return True

    def arrow(self, x1, y1, x2, y2, label='', color='gray', dashed=False, both=False):
        strong = PALETTE[color][2]
        dash = ' stroke-dasharray="9 6"' if dashed else ''
        start = f' marker-start="url(#arrow-{color})"' if both else ''
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{strong}" stroke-width="2.5"'
                          f'{dash}{start} marker-end="url(#arrow-{color})"/>')
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            side = 10 if x1 == x2 else 0
            self.text(mx + side, my - (6 if y1 == y2 else -5), label, size=self.p['small'],
                      anchor='start' if x1 == x2 else 'middle', fill=strong, weight=600)

    def svg(self, title, caption, alt):
        height = round(self.y + self.pad)
        markers = ''.join(f'<marker id="arrow-{c}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
                          f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
                          f'fill="{v[2]}"/></marker>' for c, v in PALETTE.items())
        stops = ''.join(f'<stop offset="{i / (len(GRADIENT) - 1):g}" stop-color="{PALETTE[c][1]}"/>'
                        for i, c in enumerate(GRADIENT))
        gradient = f'<linearGradient id="underline" x1="0" y1="0" x2="1" y2="0">{stops}</linearGradient>'
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{height}" '
                f'viewBox="0 0 {self.w} {height}" role="img">'
                f'<title>{escape(title)}</title><desc>{escape(alt or caption or title)}</desc>'
                f'<defs>{markers}{gradient}</defs><rect width="100%" height="100%" fill="{BG}"/>'
                + ''.join(self.parts) + '</svg>\n'), height


# ---------- layouts ----------

def header(c, spec):
    lines = c.wrap(spec['title'], c.p['title'], c.w - 2 * c.pad)
    c.y = c.pad
    c.y += c.lines(c.w / 2, c.y, lines, size=c.p['title'], weight=800)
    if spec.get('subtitle'):
        sub = c.wrap(spec['subtitle'], c.p['small'], c.w - 2 * c.pad)
        c.y += c.p['small'] * 0.3 + c.lines(c.w / 2, c.y, sub, size=c.p['small'], fill=SOFT)
    # the underline in the theme's gradient colors marks the title
    c.parts.append(f'<rect x="{c.w / 2 - c.w * 0.12}" y="{c.y + 8}" width="{c.w * 0.24}" height="5" rx="2.5" '
                   f'fill="url(#underline)"/>')
    c.y += c.pad


def footer(c, spec):
    if spec.get('caption'):
        lines = c.wrap(spec['caption'], c.p['small'], c.w - 2 * c.pad)
        c.y += c.lines(c.w / 2, c.y, lines, size=c.p['small'], fill=SOFT, italic=True)


def box_with_text(c, x, y, w, text, color, size=None, weight=500, dashed=False, note=None, icon=None):
    """A box with its text in bold tone, an optional smaller note below and an optional icon on the left.
    Returns the height. With an icon the text is left-aligned after it; otherwise it is centered."""
    size = size or c.p['body']
    small = c.p['small']
    icon_w = size * 1.3 + 10 if icon else 0
    inner = w - 2 * 14 - icon_w
    lines = c.wrap(text, size, inner)
    notes = c.wrap(note, small, inner) if note else []
    text_h = len(lines) * size * 1.3 + (len(notes) * small * 1.3 + small * 0.2 if notes else 0)
    h = max(text_h, size * 1.3 if icon else 0) + 2 * 14
    c.rect(x, y, w, h, color, dashed=dashed, tint=True)
    ink = PALETTE[color][2] if color != 'gray' else INK
    if icon:
        c.icon(icon, x + 14, y + h / 2 - size * 0.65, size * 1.3, color)
        tx, anchor = x + 14 + icon_w, 'start'
    else:
        tx, anchor = x + w / 2, 'middle'
    top = y + h / 2 - text_h / 2 - size * 0.2
    used = c.lines(tx, top, lines, size=size, weight=weight, fill=ink, anchor=anchor)
    if notes:
        c.lines(tx, top + used + small * 0.2, notes, size=small, fill=SOFT, anchor=anchor)
    return h
