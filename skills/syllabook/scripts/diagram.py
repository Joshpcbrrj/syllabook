#!/usr/bin/env python3
"""Draws an SVG diagram from a short YAML spec, in the books' visual theme.

Usage:
  python scripts/diagram.py <spec.yaml> [--reading large|small] [--out FILE]
  python scripts/diagram.py --sheet <chapter> [--book B]    one contact sheet with the chapter's images
  python scripts/diagram.py --icons    lists the icon names for the "icon" fields
  python scripts/diagram.py --help

Every spec has: type, title (the idea in one sentence), and optionally subtitle (a short line under the
title) and caption (a closing line in italics). The width follows the book's reading profile (large 960,
small 480). A spec in img/_source/<name>.yaml is drawn to img/<name>.svg.

Boxes take `text` (bold) and an optional `note` (a smaller line below) and `icon` (a name from --icons):
the icon anchors each idea at a glance and still reads on a grayscale screen.

Types and their fields:
  flow      steps: [{text, note, icon, kind: start|step|decision|end, color, label,
                     side, side_note, side_icon, side_color, side_label}]
            a decision's `side` is drawn as a box to the right (the other way out; red unless side_color);
            `label` names the arrow to the next step (e.g. "não")
  timeline  events: [{when, text, icon, highlight}]
  compare   left: {title, icon, color}, right: {title, icon, color}, rows: [[left, right], ...]
            style: wrong-right marks the left column with a red x icon and the right one with a green check
  boxes     cells: [{value, label, highlight}], name (above the boxes, e.g. a variable)
  layers    layers: [{text, note, icon, color}]   (top to bottom)
  tree      root: {text, note, icon, color, children: [...]}
  sequence  participants: [name or {name, icon}, at most 4], messages: [{from, to, text, dashed}]
  bars      bars: [{label, value, highlight}], unit
  cards     cards: [{icon, title, items: [text or {text, icon}], code: [...], scene, number}]   (the cheat
            sheet, up to 12; icon = a name from --icons, or up to 4 characters such as "for"; number replaces
            the automatic one, e.g. "1-2" for a card that covers two chapters)
  scene     steps: [[icon, ...], ...] (up to 4 steps of 1-3 icons), ops: [→ + = ↔], label
            a scene shows a relation with icons (folder → files, A + B = C); in a card, `scene` is
            {steps, ops, label} or just the list of steps, and goes under the items. It demonstrates the
            idea, never decorates.
  chord     chords: [{name, frets: "x02210", fingers: "x02310", barre: {fret, from, to}}] (up to 6),
            tuning (default E A D G B E; 4 strings for bass or ukulele). Frets from the lowest string.
  fretboard frets: [first, last], notes: [{string, fret, label, root}] (string 1 = the highest)
  tab       steps: ["6:0", "4:2 3:0", "|"]: string:fret per beat, notes together, | for a bar line
            chord, fretboard and tab also print "text": the same content as copyable text, which
            goes right under the image (whatever the reader plays stays as text).

Colors: blue (input, structure), green (right, output, end), orange (decision, attention),
red (error), purple (central idea), teal, gray (neutral). Prints JSON with the file written,
its size and any text that does not fit or icon name that does not exist; exit code 1 then.
"""
import argparse
import base64
import os
import re
import shutil
import subprocess
import sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import icons
from common import chapter_path, fail, find_book, load_yaml, out
from diagram_draw import (BG, INK, MAX_ELEMENTS, PALETTE, PROFILES, SOFT, TYPES, Canvas,  # noqa: E402,F401
                          footer, header)
from diagram_layouts import bars, boxes, cards, compare, flow, layers, scene, sequence, timeline, tree  # noqa: E402
from diagram_music import chord, chord_shape, fretboard, string_names, tab, tab_steps, tuning_of  # noqa: E402


def text_version(spec):
    """The same content as copyable text (chords string by string, the fretboard notes, an ASCII tab),
    in a form that needs no translation; None for the other types."""
    kind = spec.get('type')
    if kind not in ('chord', 'fretboard', 'tab'):
        return None
    scratch = Canvas('large')
    tuning = tuning_of(spec)
    n = len(tuning)
    names = string_names(tuning)
    if kind == 'chord':
        blocks = []
        for ch in spec['chords']:
            frets, fingers, _ = chord_shape(scratch, ch, n)
            lines = [str(ch.get('name', ''))]
            for s in range(n):
                i = n - 1 - s
                mark = 'x' if frets[i] is None else str(frets[i])
                lines.append(f'{names[s]} |--{mark}--|' + (f'  {fingers[i]}' if fingers[i] else ''))
            blocks.append('\n'.join(lines))
        return '\n\n'.join(blocks)
    if kind == 'fretboard':
        notes = sorted(spec['notes'], key=lambda m: (-int(m.get('string', 0)), int(m.get('fret', 0))))
        return ', '.join(f'{m.get("string")}:{m.get("fret")} {m.get("label", "")}{"*" if m.get("root") else ""}'
                         for m in notes)
    rows = [f'{names[s]}|' for s in range(n)]
    for step in tab_steps(scratch, spec, n):
        if step == '|':
            rows = [r + '|' for r in rows]
            continue
        played = {s: str(f) for s, f in step}
        width = max([len(v) for v in played.values()] + [1]) + 2
        rows = [r + played.get(s + 1, '').center(width, '-').replace(' ', '-') for s, r in enumerate(rows)]
    return '\n'.join(r + '|' for r in rows)


LAYOUTS = {'flow': flow, 'timeline': timeline, 'compare': compare, 'boxes': boxes, 'layers': layers,
           'tree': tree, 'sequence': sequence, 'bars': bars, 'scene': scene,
           'chord': chord, 'fretboard': fretboard, 'tab': tab}
REQUIRED = {'flow': 'steps', 'timeline': 'events', 'compare': 'rows', 'boxes': 'cells', 'layers': 'layers',
            'tree': 'root', 'sequence': 'messages', 'bars': 'bars', 'cards': 'cards', 'scene': 'steps',
            'chord': 'chords', 'fretboard': 'notes', 'tab': 'steps'}


def boolean_keys(value, path='spec'):
    """YAML reads keys such as no, yes, on and off as booleans: the field would vanish silently."""
    if isinstance(value, dict):
        for k, v in value.items():
            if isinstance(k, bool):
                raise ValueError(f'{path} has a key read as {k} (a key named yes/no/on/off): rename it or quote it')
            boolean_keys(v, f'{path}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            boolean_keys(v, f'{path}[{i}]')


def render(spec, profile='large'):
    """Returns (svg text, height, problems, warnings)."""
    boolean_keys(spec)
    kind = spec.get('type')
    if kind not in TYPES:
        raise ValueError(f'type must be one of {", ".join(TYPES)}')
    for key in ('title', REQUIRED[kind]):
        if not spec.get(key):
            raise ValueError(f'a {kind} spec needs "{key}"')
    c = Canvas(profile)
    header(c, spec)
    elements = cards(c, spec, profile) if kind == 'cards' else LAYOUTS[kind](c, spec)
    footer(c, spec)
    text, height = c.svg(spec['title'], spec.get('caption', ''), spec.get('alt', ''))
    warnings = []
    if elements > MAX_ELEMENTS:
        warnings.append(f'{elements} elements: more than ~{MAX_ELEMENTS} overloads the reader; split in two')
    if profile == 'small' and kind != 'cards' and height > 640:
        warnings.append(f'{height} px tall: on a 6-inch screen it will be split across pages; split it')
    return text, height, c.problems, warnings


def book_profile(path):
    """The reading profile of the book a spec belongs to, or None."""
    d = os.path.dirname(os.path.abspath(path))
    for _ in range(4):
        if os.path.exists(os.path.join(d, 'book.yaml')):
            return (load_yaml(os.path.join(d, 'book.yaml')).get('choices') or {}).get('reading')
        d = os.path.dirname(d)
    return None


def target_for(spec_path):
    folder, name = os.path.split(os.path.abspath(spec_path))
    stem = os.path.splitext(name)[0]
    if os.path.basename(folder) == '_source':
        folder = os.path.dirname(folder)
    return os.path.join(folder, stem + '.svg')


def contact_sheet(book_dir, n):
    path = chapter_path(book_dir, n)
    if not path:
        fail(f'chapter {n} has no file yet')
    names = re.findall(r'\]\(\.\./img/([^)\s]+\.svg)\)', open(path, encoding='utf-8').read())
    if not names:
        out({'chapter': n, 'images': 0, 'note': 'the chapter has no SVG images'})
    tile, gap, cols = 480, 24, 2
    rows = (len(names) + cols - 1) // cols
    parts = []
    for i, name in enumerate(names):
        data = base64.b64encode(open(os.path.join(book_dir, 'img', name), 'rb').read()).decode()
        x, y = gap + (i % cols) * (tile + gap), gap + (i // cols) * (tile + 2 * gap)
        parts.append(f'<image x="{x}" y="{y}" width="{tile}" height="{tile}" href="data:image/svg+xml;base64,{data}"/>'
                     f'<text x="{x}" y="{y + tile + 18}" font-family="sans-serif" font-size="14">{escape(name)}</text>')
    w, h = cols * (tile + gap) + gap, rows * (tile + 2 * gap) + gap
    sheet = os.path.join(book_dir, 'img', '_source', f'_sheet-c{n:02d}.svg')
    os.makedirs(os.path.dirname(sheet), exist_ok=True)
    with open(sheet, 'w', encoding='utf-8') as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
                f'<rect width="100%" height="100%" fill="white"/>{"".join(parts)}</svg>')
    result = {'chapter': n, 'images': len(names), 'sheet': sheet}
    png = sheet[:-4] + '.png'
    if to_png(sheet, png):
        result['png'] = png
    else:
        result['note'] = 'no SVG to PNG converter available: open the SVG sheet instead'
    out(result)


def to_png(svg, png):
    """Renders an SVG to PNG so Claude can look at it; resvg works on every system, without native libraries."""
    try:
        import resvg_py
    except ImportError:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', 'resvg-py'], check=True,
                           capture_output=True)
            import resvg_py
        except (subprocess.CalledProcessError, ImportError):
            resvg_py = None
    if resvg_py:
        with open(png, 'wb') as f:
            f.write(bytes(resvg_py.svg_to_bytes(svg_path=svg)))
        return True
    if shutil.which('rsvg-convert'):
        subprocess.run(['rsvg-convert', '-o', png, svg], check=True)
        return True
    return False


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('spec', nargs='?')
    p.add_argument('--reading', choices=sorted(PROFILES))
    p.add_argument('--out')
    p.add_argument('--sheet', type=int, metavar='CHAPTER')
    p.add_argument('--book')
    p.add_argument('--icons', action='store_true')
    p.add_argument('--png', metavar='SVG', help='render an SVG (the cover, an illustration) to a PNG next to it')
    args = p.parse_args()
    if args.icons:
        out({'icons': icons.names()})
    if args.png:
        if not os.path.exists(args.png):
            fail(f'file not found: {args.png}')
        png = os.path.splitext(args.png)[0] + '.png'
        if not to_png(args.png, png):
            fail('no SVG to PNG converter available (pip install resvg-py, or rsvg-convert)')
        out({'png': png})
    if args.sheet:
        book_dir, _ = find_book(args.book)
        contact_sheet(book_dir, args.sheet)
    if not args.spec:
        p.error('give a spec file, or --sheet <chapter>')
    if not os.path.exists(args.spec):
        fail(f'spec not found: {args.spec}')
    profile = args.reading or book_profile(args.spec) or 'large'
    try:
        spec = load_yaml(args.spec)
        text, height, problems, warnings = render(spec, profile)
    except (ValueError, KeyError, TypeError) as e:
        fail(f'invalid spec: {e}')
    target = args.out or target_for(args.spec)
    os.makedirs(os.path.dirname(target) or '.', exist_ok=True)
    with open(target, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    result = {'svg': target, 'profile': profile, 'width': PROFILES[profile]['width'], 'height': height,
              'fits': not problems, 'problems': problems, 'warnings': warnings}
    text = text_version(spec)
    if text:
        # music diagrams: the same content as copyable text, to put right under the image
        result['text'] = text
    out(result, 1 if problems else 0)


if __name__ == '__main__':
    main()
