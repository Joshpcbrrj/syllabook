"""The music diagram types of diagram.py: chord boxes, fretboard and tablature."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagram_draw import BG, INK, PALETTE, SOFT  # noqa: E402


TUNING = ['E', 'A', 'D', 'G', 'B', 'E']
INLAYS = (3, 5, 7, 9, 12, 15, 17, 19, 21, 24)


def tuning_of(spec):
    return [str(t) for t in spec.get('tuning') or TUNING]


def string_names(tuning):
    """Names from the highest string to the lowest; a repeated lowest note is lowercase on top (e ... E)."""
    names = list(reversed(tuning))
    if len(names) > 1 and names[0] == names[-1]:
        names[0] = names[0].lower()
    return names


def positions(value, n):
    """'x02210' or [x, 0, 2, ...], lowest string first -> [None (muted) | fret], or None if malformed."""
    items = list(value) if isinstance(value, str) else list(value or [])
    if len(items) != n:
        return None
    found = []
    for item in items:
        token = str(item).strip().lower()
        if token == 'x':
            found.append(None)
        elif token.isdigit():
            found.append(int(token))
        else:
            return None
    return found


def chord_shape(c, ch, n):
    """Checks one chord and returns (frets, fingers, barre) with problems reported on the canvas."""
    name = ch.get('name', '?')
    frets = positions(ch.get('frets', ''), n)
    if frets is None:
        c.problems.append(f'chord {name}: "frets" needs one position per string ({n}): x, 0 or a fret number')
        frets = [None] * n
    fingers = [None] * n
    if ch.get('fingers') is not None:
        given = positions(ch['fingers'], n)
        if given is None or any(f is not None and not 0 <= f <= 4 for f in given):
            c.problems.append(f'chord {name}: fingers go from 1 to 4, one per string ({n}); 0 or x for none')
        else:
            fingers = [f or None for f in given]
    barre = ch.get('barre')
    if barre:
        ok = (isinstance(barre, dict) and int(barre.get('fret', 0)) > 0 and
              all(1 <= int(barre.get(k, 0)) <= n for k in ('from', 'to')))
        if not ok:
            c.problems.append(f'chord {name}: barre needs a fret above 0 and strings from 1 to {n}')
            barre = None
    return frets, fingers, barre


def chord(c, spec):
    tuning = tuning_of(spec)
    n = len(tuning)
    items = spec['chords']
    if len(items) > 6:
        c.problems.append(f'{len(items)} chords: a diagram holds at most 6 chords')
    per_row = min(len(items), 3 if c.w < 700 else 6)
    cw = (c.w - 2 * c.pad) / max(per_row, 1)
    grid = min(cw * 0.6, c.p['body'] * 7)
    gap = grid / (n - 1)
    fret_h = gap * 1.2
    shown = 4
    for r in range(0, len(items), per_row):
        row = items[r:r + per_row]
        top = c.y
        for k, ch in enumerate(row):
            frets, fingers, barre = chord_shape(c, ch, n)
            pressed = [f for f in frets if f]
            start = 1 if not pressed or max(pressed) <= shown else min(pressed)
            left = c.pad + k * cw + (cw - grid) / 2
            name_y = top + c.p['title']
            c.text(left + grid / 2, name_y, ch.get('name', ''), size=c.p['title'], weight=800,
                   fill=PALETTE['purple'][2])
            mark_y = name_y + c.p['small'] * 1.6
            grid_top = mark_y + c.p['small'] * 0.6
            for i, f in enumerate(frets):
                x = left + i * gap
                if f is None or f == 0:
                    c.text(x, mark_y, 'x' if f is None else 'o', size=c.p['small'], weight=700, fill=SOFT)
            for j in range(shown + 1):
                y = grid_top + j * fret_h
                width = 5 if j == 0 and start == 1 else 1.5
                c.parts.append(f'<line x1="{left}" y1="{y}" x2="{left + grid}" y2="{y}" stroke="{INK}" '
                               f'stroke-width="{width}"/>')
            for i in range(n):
                x = left + i * gap
                c.parts.append(f'<line class="string" x1="{x}" y1="{grid_top}" x2="{x}" '
                               f'y2="{grid_top + shown * fret_h}" stroke="{INK}" stroke-width="1.5"/>')
            if start > 1:
                c.text(left - 6, grid_top + fret_h * 0.62, f'{start}fr', size=c.p['small'] * 0.85, anchor='end',
                       fill=SOFT, weight=600)
            radius = gap * 0.36
            if barre:
                low, high = sorted((n - int(barre['from']), n - int(barre['to'])))
                y = grid_top + (int(barre['fret']) - start + 0.5) * fret_h
                c.parts.append(f'<rect x="{left + low * gap - radius}" y="{y - radius}" '
                               f'width="{(high - low) * gap + 2 * radius}" height="{2 * radius}" rx="{radius}" '
                               f'fill="{PALETTE["purple"][2]}"/>')
            for i, f in enumerate(frets):
                if not f or f - start >= shown:
                    if f and f - start >= shown:
                        c.problems.append(f'chord {ch.get("name", "?")}: fret {f} does not fit in {shown} frets '
                                          f'from {start}')
                    continue
                x, y = left + i * gap, grid_top + (f - start + 0.5) * fret_h
                c.parts.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{PALETTE["purple"][2]}"/>')
                if fingers[i]:
                    c.text(x, y + radius * 0.55, fingers[i], size=radius * 1.45, weight=700, fill='#FFFFFF')
            names_y = grid_top + shown * fret_h + c.p['small'] * 1.4
            for i, name in enumerate(tuning):
                c.text(left + i * gap, names_y, name, size=c.p['small'] * 0.85, fill=SOFT)
        c.y = top + c.p['title'] + c.p['small'] * 2.2 + shown * fret_h + c.p['small'] * 2.6
    c.y += c.pad / 2
    return len(items)


def fretboard(c, spec):
    tuning = tuning_of(spec)
    n = len(tuning)
    first, last = (int(v) for v in (spec.get('frets') or [0, 12])[:2])
    names = string_names(tuning)
    left = c.pad + c.p['body'] * 1.6
    width = c.w - left - c.pad
    count = last - first + 1
    fw = width / count
    sp = min(c.p['body'] * 1.6, fw * 0.9)
    top = c.y + sp * 0.5
    for s in range(n):
        y = top + s * sp
        c.text(left - 10, y + c.p['small'] * 0.35, names[s], size=c.p['small'], anchor='end', weight=700, fill=SOFT)
        c.parts.append(f'<line x1="{left}" y1="{y}" x2="{left + width}" y2="{y}" stroke="{INK}" '
                       f'stroke-width="{1 + (n - 1 - s) * 0.25}"/>')
    bottom = top + (n - 1) * sp
    for j in range(count + 1):
        x = left + j * fw
        heavy = j == 0 and first <= 1
        c.parts.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{bottom}" stroke="{INK}" '
                       f'stroke-width="{5 if heavy else 1.5}"/>')
    for f in range(first, last + 1):
        x = left + (f - first + 0.5) * fw
        c.text(x, bottom + c.p['small'] * 1.6, f, size=c.p['small'] * 0.85, fill=SOFT)
        if f in INLAYS:
            c.parts.append(f'<circle cx="{x}" cy="{bottom + c.p["small"] * 2.4}" r="3" fill="{PALETTE["gray"][1]}"/>')
    radius = min(sp, fw) * 0.38
    for note in spec['notes']:
        s, f = int(note.get('string', 0)), int(note.get('fret', -1))
        if not 1 <= s <= n:
            c.problems.append(f'note {note.get("label", "")}: there is no string {s} ({n} strings)')
            continue
        if not first <= f <= last:
            c.problems.append(f'note {note.get("label", "")} on string {s}, fret {f}: outside frets {first}-{last}')
            continue
        color = 'purple' if note.get('root') else 'blue'
        x, y = left + (f - first + 0.5) * fw, top + (s - 1) * sp
        c.parts.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{PALETTE[color][2]}"/>')
        c.text(x, y + radius * 0.4, str(note.get('label', ''))[:3], size=radius * 1.05, weight=700, fill='#FFFFFF')
    c.y = bottom + c.p['small'] * 3.4 + c.pad / 2
    return len(spec['notes'])


def tab_steps(c, spec, n):
    """[[(string, fret), ...] or '|', ...]; malformed steps are reported."""
    steps = []
    for raw in spec['steps']:
        token = str(raw).strip()
        if token == '|':
            steps.append('|')
            continue
        notes = []
        for part in token.split():
            found = re.fullmatch(r'(\d+):(\d+)', part)
            if not found or not 1 <= int(found.group(1)) <= n:
                c.problems.append(f'tab step "{part}": write string:fret, with strings from 1 to {n} (e.g. 6:0)')
                continue
            notes.append((int(found.group(1)), int(found.group(2))))
        steps.append(notes)
    return steps


def tab(c, spec):
    tuning = tuning_of(spec)
    n = len(tuning)
    names = string_names(tuning)
    steps = tab_steps(c, spec, n)
    left = c.pad + c.p['body'] * 1.6
    width = c.w - left - c.pad
    col = width / (len(steps) + 1)
    sp = c.p['body'] * 1.3
    top = c.y + sp * 0.5
    for s in range(n):
        y = top + s * sp
        c.text(left - 10, y + c.p['small'] * 0.35, names[s], size=c.p['small'], anchor='end', weight=700, fill=SOFT)
        c.parts.append(f'<line x1="{left}" y1="{y}" x2="{left + width}" y2="{y}" stroke="{SOFT}" stroke-width="1.2"/>')
    bottom = top + (n - 1) * sp
    for edge in (left, left + width):
        c.parts.append(f'<line x1="{edge}" y1="{top}" x2="{edge}" y2="{bottom}" stroke="{INK}" stroke-width="2"/>')
    for i, step in enumerate(steps):
        x = left + (i + 1) * col
        if step == '|':
            c.parts.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{bottom}" stroke="{INK}" stroke-width="2"/>')
            continue
        for s, f in step:
            y = top + (s - 1) * sp
            label = str(f)
            w = c.width_of(label, c.p['body'], mono=True) + 8
            c.parts.append(f'<rect x="{x - w / 2}" y="{y - sp * 0.42}" width="{w}" height="{sp * 0.84}" '
                           f'fill="{BG}"/>')
            c.text(x, y + c.p['body'] * 0.36, label, mono=True, weight=700, fill=PALETTE['purple'][2])
    c.y = bottom + sp + c.pad / 2
    return 0  # a tab is read note by note, not taken in at a glance
