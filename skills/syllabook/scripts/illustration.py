#!/usr/bin/env python3
"""Checks an SVG illustration drawn by hand (references/VISUALS.md §4b): an analogy or an imagined scene.

Usage:
  python scripts/illustration.py img/c03-caixa-de-envio.svg [--book B]

Errors (fix them): not valid SVG, no viewBox, no <title> (the one sentence the reader must understand),
embedded images, scripts, foreignObject, event handlers, external links or styles, wider than the
reading profile (large 960, small 480). Warnings (simplify): colors outside the book palette, more than
~60 shapes, more than 5 labels, labels over 5 words. audit.py runs the same checks on every SVG in a
chapter that has no spec in img/_source/.
"""
import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import fail, find_book, load_yaml, out
from diagram import BG, INK, PALETTE, PROFILES, SOFT

FORBIDDEN = {'image', 'script', 'foreignObject', 'iframe', 'video', 'audio', 'object', 'embed'}
SHAPES = {'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'path', 'use'}
COLORS = {c.upper() for c in (BG, INK, SOFT, '#FFFFFF', '#000000')} | {c.upper() for v in PALETTE.values() for c in v}
HEX = re.compile(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b')
MAX_SHAPES, MAX_LABELS, MAX_WORDS = 60, 5, 5


def local(tag):
    return tag.rsplit('}', 1)[-1]


def check(path, width):
    """Returns (errors, warnings) for one illustration."""
    errors, warnings = [], []
    text = open(path, encoding='utf-8').read()
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        return [f'not valid SVG ({e})'], []
    if local(root.tag) != 'svg':
        return ['not valid SVG (the root element must be <svg>)'], []
    box = (root.get('viewBox') or '').replace(',', ' ').split()
    if len(box) != 4:
        errors.append('no viewBox: give the drawing a viewBox so it scales on every screen')
    elif float(box[2]) > width:
        errors.append(f'wider than {width} (viewBox width {box[2]}): fit the reading profile')
    if not any(local(e.tag) == 'title' and (e.text or '').strip() for e in root):
        errors.append('no <title>: write the sentence the reader must understand from it')
    shapes, labels = 0, []
    for e in root.iter():
        tag = local(e.tag)
        if tag in FORBIDDEN:
            errors.append(f'<{tag}> is not allowed: an illustration is drawn with shapes and text only')
        for name, value in e.attrib.items():
            name = local(name)
            if name.lower().startswith('on'):
                errors.append(f'{name} (an event handler) is not allowed')
            if name == 'href' and not value.startswith('#'):
                errors.append(f'external link not allowed ({value})')
        if tag == 'style' and re.search(r'url\(\s*["\']?(https?:|//)|@import', e.text or ''):
            errors.append('external style not allowed (@import or url to another site)')
        shapes += tag in SHAPES
        if tag == 'text':
            labels.append(' '.join(''.join(e.itertext()).split()))
    other = sorted({c.upper() for c in HEX.findall(text)} - COLORS)
    if other:
        warnings.append(f'colors outside the book palette: {", ".join(other)} (use the diagram colors)')
    if shapes > MAX_SHAPES:
        warnings.append(f'{shapes} shapes: keep it simple (about {MAX_SHAPES} at most)')
    if len(labels) > MAX_LABELS:
        warnings.append(f'{len(labels)} labels: at most {MAX_LABELS}; the chapter text explains the rest')
    for label in labels:
        if len(label.split()) > MAX_WORDS:
            warnings.append(f'label "{label}" has more than {MAX_WORDS} words')
    return list(dict.fromkeys(errors)), warnings


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('file')
    p.add_argument('--book')
    args = p.parse_args()
    if not os.path.exists(args.file):
        fail(f'file not found: {args.file}')
    _, path = find_book(args.book)
    reading = (load_yaml(path).get('choices') or {}).get('reading', 'large')
    errors, warnings = check(args.file, PROFILES[reading]['width'])
    out({'ok': not errors, 'errors': errors, 'warnings': warnings}, 0 if not errors else 1)


if __name__ == '__main__':
    main()
