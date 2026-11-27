"""The general diagram types of diagram.py: flow, timeline, compare, boxes, layers, tree,
sequence, bars, scenes and cards."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagram_draw import INK, KIND_COLOR, PALETTE, SCENE_OPS, SOFT, box_with_text  # noqa: E402
import icons  # noqa: E402


def flow(c, spec):
    steps = spec['steps']
    has_side = any(s.get('side') for s in steps)
    col = c.w * (0.56 if has_side else 0.8)
    x = c.pad if has_side else (c.w - col) / 2
    side_x = x + col + c.pad * 1.5
    side_w = c.w - side_x - c.pad
    gap = c.p['body'] * 2.4
    for i, s in enumerate(steps):
        kind = s.get('kind', 'step')
        color = s.get('color') or KIND_COLOR.get(kind, 'blue')
        top = c.y
        if kind == 'decision':
            # a diamond narrower than the boxes, so the decision stands out without dominating
            dw = col * 0.78
            size = c.p['body']
            # the question on one line when it fits, at the body size or a little smaller, before wrapping
            if c.width_of(s['text'], size) > dw * 0.75 and c.width_of(s['text'], c.p['small']) <= dw * 0.75:
                size = c.p['small']
            one_line = c.width_of(s['text'], size) <= dw * 0.75
            lines = c.wrap(s['text'], size, dw * 0.75 if one_line else dw * 0.6)
            notes = c.wrap(s['note'], c.p['small'], dw * 0.72) if s.get('note') else []
            text_h = len(lines) * size * 1.3 + len(notes) * c.p['small'] * 1.3
            h = text_h + c.p['body'] * 2.6
            c.diamond(x + col / 2, top, dw, h, color)
            y0 = top + h / 2 - text_h / 2 - size * 0.2
            used = c.lines(x + col / 2, y0, lines, size=size, weight=700, fill=PALETTE[color][2])
            if notes:
                c.lines(x + col / 2, y0 + used, notes, size=c.p['small'], fill=SOFT)
            right_edge = x + col / 2 + dw / 2
        else:
            h = box_with_text(c, x, top, col, s['text'], color, weight=700 if kind != 'step' else 600,
                              note=s.get('note'), icon=s.get('icon'))
            right_edge = x + col
        if s.get('side'):
            side_color = s.get('side_color', 'red')
            start = len(c.parts)
            side_h = box_with_text(c, side_x, top, side_w, s['side'], side_color, weight=700,
                                   note=s.get('side_note'), icon=s.get('side_icon'))
            # drawn at the top, then moved so it is centered on the decision
            c.shift(start, h / 2 - side_h / 2)
            c.arrow(right_edge, top + h / 2, side_x, top + h / 2, s.get('side_label', ''), side_color)
            h = max(h, side_h)
        c.y = top + h
        if i + 1 < len(steps):
            c.arrow(x + col / 2, c.y, x + col / 2, c.y + gap, s.get('label', ''), 'gray')
            c.y += gap
    c.y += c.pad
    return len(steps)


def timeline(c, spec):
    events = spec['events']
    line_x = c.pad + c.p['body'] * 0.6
    text_x = line_x + c.p['body'] * 1.6
    start = c.y
    for e in events:
        color = 'purple' if e.get('highlight') else 'blue'
        r = c.p['body'] * (0.75 if e.get('icon') else 0.45)
        cy = c.y + c.p['body'] * 0.7
        c.parts.append(f'<circle cx="{line_x}" cy="{cy}" r="{r}" '
                       f'fill="{PALETTE[color][3]}" stroke="{PALETTE[color][2]}" stroke-width="2.5"/>')
        if e.get('icon'):
            c.icon(e['icon'], line_x - r * 0.65, cy - r * 0.65, r * 1.3, color)
        # the date on its own line, the event below it
        c.text(text_x, c.y + c.p['body'], e['when'], weight=800, anchor='start', fill=PALETTE[color][2])
        lines = c.wrap(e['text'], c.p['body'], c.w - text_x - c.pad)
        c.y += c.p['body'] * 1.45
        c.y += c.lines(text_x, c.y, lines, anchor='start') + c.p['body'] * 1.1
    c.parts.insert(0, f'<line x1="{line_x}" y1="{start}" x2="{line_x}" y2="{c.y - c.p["body"]}" '
                      f'stroke="{PALETTE["gray"][1]}" stroke-width="3"/>')
    c.y += c.pad / 2
    return len(events)


def compare(c, spec):
    wrong_right = spec.get('style') == 'wrong-right'
    sides = []
    for key, mark, default in (('left', 'circle-x', 'red'), ('right', 'circle-check', 'green')):
        side = spec.get(key) or {}
        color = side.get('color') or (default if wrong_right else ('blue' if key == 'left' else 'purple'))
        # wrong-right marks each side with a drawn icon (an emoji depends on the reader's fonts)
        sides.append((str(side.get('title', '')), color, side.get('icon') or (mark if wrong_right else None)))
    col = (c.w - 3 * c.pad) / 2
    xs = (c.pad, 2 * c.pad + col)
    for i, row in enumerate(spec['rows'], 1):
        if not isinstance(row, list) or len(row) != 2:
            raise ValueError(f'compare row {i} must have exactly 2 values, left and right')
    heights = []
    for (title, color, icon), x in zip(sides, xs, strict=True):
        heights.append(box_with_text(c, x, c.y, col, title, color, weight=800, icon=icon))
    c.y += max(heights) + c.p['body'] * 0.6
    for row in spec['rows']:
        h = max(len(c.wrap(value, c.p['body'], col - 28)) * c.p['body'] * 1.3 + 22 for value in row)
        for (_, color, _), x, value in zip(sides, xs, row, strict=True):
            c.rect(x, c.y, col, h, color, rx=10, shadow=False)
            c.lines(x + col / 2, c.y + 11 - c.p['body'] * 0.2, c.wrap(value, c.p['body'], col - 28))
        c.y += h + c.p['body'] * 0.5
    c.y += c.pad / 2
    return len(spec['rows'])


def boxes(c, spec):
    cells = spec['cells']
    size = min((c.w - 2 * c.pad) / max(len(cells), 1), c.p['body'] * 5)
    x0 = (c.w - size * len(cells)) / 2
    if spec.get('name'):
        c.text(x0, c.y + c.p['body'], spec['name'], weight=700, anchor='start', mono=True, fill=PALETTE['blue'][2])
        c.y += c.p['body'] * 1.8
    for i, cell in enumerate(cells):
        color = 'purple' if cell.get('highlight') else 'blue'
        c.rect(x0 + i * size, c.y, size, size, color, rx=6, shadow=False, tint=True)
        if cell.get('highlight'):
            # the focus: a thicker border in the strong tone
            c.parts.append(f'<rect x="{x0 + i * size + 1.5}" y="{c.y + 1.5}" width="{size - 3}" height="{size - 3}" '
                           f'rx="5" fill="none" stroke="{PALETTE[color][2]}" stroke-width="3"/>')
        value = str(cell['value'])
        if c.width_of(value, c.p['body'], mono=True) > size - 8:
            c.problems.append(f'value "{value}" does not fit in its box ({round(size)} px)')
        c.text(x0 + i * size + size / 2, c.y + size / 2 + c.p['body'] * 0.35, value, mono=True, weight=700)
        if 'label' in cell:
            # the index in a small gray badge under its box
            label = str(cell['label'])
            bw = max(c.width_of(label, c.p['small']) + 14, c.p['small'] * 1.8)
            cx = x0 + i * size + size / 2
            c.parts.append(f'<rect x="{cx - bw / 2}" y="{c.y + size + 6}" width="{bw}" height="{c.p["small"] * 1.5}" '
                           f'rx="{c.p["small"] * 0.75}" fill="{PALETTE["gray"][3]}"/>')
            c.text(cx, c.y + size + 6 + c.p['small'] * 1.1, label, size=c.p['small'], fill=INK, weight=600)
    c.y += size + c.p['small'] * 2.4 + c.pad / 2
    return 1


def layers(c, spec):
    for i, layer in enumerate(spec['layers']):
        color = layer.get('color') or ('purple', 'blue', 'teal', 'green', 'orange', 'gray')[i % 6]
        c.y += box_with_text(c, c.pad, c.y, c.w - 2 * c.pad, layer['text'], color, weight=700,
                             note=layer.get('note'), icon=layer.get('icon')) + c.p['body'] * 0.5
    c.y += c.pad / 2
    return len(spec['layers'])


def tree(c, spec):
    count = [0]
    indent = c.p['body'] * 1.8

    def node(n, depth, parent_mid):
        count[0] += 1
        x = c.pad + depth * indent
        w = c.w - x - c.pad
        top = c.y
        color = n.get('color') or ('purple' if depth == 0 else ('blue', 'teal', 'green', 'orange')[(depth - 1) % 4])
        h = box_with_text(c, x, top, w, n['text'], color, weight=700 if depth == 0 else 600, note=n.get('note'),
                          icon=n.get('icon'))
        if parent_mid is not None:
            px = x - indent / 2
            c.parts.append(f'<path d="M{px},{parent_mid} V{top + h / 2} H{x}" fill="none" '
                           f'stroke="{PALETTE["gray"][1]}" stroke-width="2"/>')
        c.y = top + h + c.p['body'] * 0.5
        for child in n.get('children') or []:
            node(child, depth + 1, top + h)
    node(spec['root'], 0, None)
    c.y += c.pad / 2
    return count[0]


def sequence(c, spec):
    # a participant is a name, or {name, icon}
    people = [p if isinstance(p, dict) else {'name': p} for p in spec['participants']]
    names = [p['name'] for p in people]
    if len(names) > 4:
        c.problems.append(f'{len(names)} participants: at most 4 fit side by side')
    col = (c.w - 2 * c.pad) / len(names)
    centers = {name: c.pad + col * i + col / 2 for i, name in enumerate(names)}
    head_h = max(box_with_text(c, c.pad + col * i + 6, c.y, col - 12, p['name'], 'purple', weight=700,
                               icon=p.get('icon')) for i, p in enumerate(people))
    c.y += head_h
    top = c.y
    c.y += c.p['body'] * 1.6
    for i, m in enumerate(spec['messages'], 1):
        x1, x2 = centers[m['from']], centers[m['to']]
        label = f'{i}. {m["text"]}'
        if c.width_of(label, c.p['small']) > abs(x2 - x1) + col * 0.8:
            c.problems.append(f'message "{m["text"]}" is longer than the space between {m["from"]} and {m["to"]}')
        c.text((x1 + x2) / 2, c.y - 8, label, size=c.p['small'], fill=INK, weight=600)
        c.arrow(x1, c.y, x2, c.y, '', 'gray', dashed=m.get('dashed', False))
        c.y += c.p['body'] * 2.2
    for x in centers.values():
        c.parts.insert(0, f'<line x1="{x}" y1="{top}" x2="{x}" y2="{c.y}" stroke="{PALETTE["gray"][1]}" '
                          f'stroke-width="2" stroke-dasharray="6 6"/>')
    c.y += c.pad / 2
    return len(spec['messages'])


def bars(c, spec):
    items = spec['bars']
    top = max(float(b['value']) for b in items) or 1
    label_w = (c.w - 2 * c.pad) * 0.3
    bar_w = c.w - 2 * c.pad - label_w - c.p['body'] * 4
    for b in items:
        color = 'purple' if b.get('highlight') else 'blue'
        h = c.p['body'] * 1.6
        c.text(c.pad + label_w - 10, c.y + h * 0.7, b['label'], anchor='end')
        if c.width_of(str(b['label']), c.p['body']) > label_w - 10:
            c.problems.append(f'bar label "{b["label"]}" is too long')
        length = max(2, bar_w * float(b['value']) / top)
        c.rect(c.pad + label_w, c.y, length, h, color, rx=6, shadow=False)
        c.text(c.pad + label_w + length + 8, c.y + h * 0.7, f'{b["value"]}{spec.get("unit", "")}', anchor='start',
               weight=700, fill=PALETTE[color][2])
        c.y += h + c.p['body'] * 0.6
    c.y += c.pad / 2
    return len(items)


def scene_size(c, w, scene):
    """(tile size, gap between tiles, total height) of a scene drawn in width w."""
    n = max(len(scene.get('steps') or []), 1)
    tile = min(w / (n + (n - 1) * 0.7), c.p['body'] * 4)
    label = 0
    if scene.get('label'):
        label = len(c.wrap(scene['label'], c.p['small'], w, report=False)) * c.p['small'] * 1.3 + c.p['small'] * 0.7
    return tile, tile * 0.7, tile + label


def scene_block(c, x, y, w, scene, color=None):
    """A short row of icons joined by arrows or by + and =, which shows an idea (folder -> files, A + B = C).
    Each step is a list of 1 to 3 icons stacked in one tile. Returns the height."""
    steps = scene.get('steps') or []
    ops = scene.get('ops') or ['→'] * (len(steps) - 1)
    if len(steps) > 4:
        c.problems.append(f'{len(steps)} steps: a scene holds at most 4 steps')
    for op in ops:
        if op not in SCENE_OPS:
            c.problems.append(f'scene op "{op}" must be one of {" ".join(SCENE_OPS)}')
    tile, gap, height = scene_size(c, w, scene)
    x0 = x + (w - (len(steps) * tile + (len(steps) - 1) * gap)) / 2
    cycle = ('blue', 'purple', 'teal', 'green')
    for i, step in enumerate(steps):
        names = step if isinstance(step, list) else [step]
        if not 1 <= len(names) <= 3:
            c.problems.append(f'step {i + 1} has {len(names)} icons: a scene step holds 1 to 3 icons')
        tone = color or cycle[i % len(cycle)]
        tx = x0 + i * (tile + gap)
        c.rect(tx, y, tile, tile, tone, rx=tile * 0.18, shadow=False, tint=color is None)
        shown = names[:3]
        size = min(tile * 0.58, tile * 0.84 / max(len(shown), 1))
        top = y + tile / 2 - size * len(shown) / 2
        for k, name in enumerate(shown):
            c.icon(name, tx + tile / 2 - size * 0.46, top + k * size + size * 0.04, size * 0.92, tone)
        if i + 1 < len(steps):
            op = ops[i] if i < len(ops) else '→'
            mid, left, right = y + tile / 2, tx + tile + gap * 0.18, tx + tile + gap * 0.82
            if op in ('+', '='):
                c.text((left + right) / 2, mid + c.p['title'] * 0.36, op, size=c.p['title'] * 1.1, weight=800,
                       fill=PALETTE[color or 'gray'][2])
            else:
                c.arrow(left, mid, right, mid, color=color or 'gray', both=op == '↔')
    if scene.get('label'):
        c.lines(x + w / 2, y + tile + c.p['small'] * 0.4, c.wrap(scene['label'], c.p['small'], w), size=c.p['small'],
                fill=SOFT, weight=600)
    return height


def scene(c, spec):
    c.y += scene_block(c, c.pad, c.y, c.w - 2 * c.pad, spec) + c.pad / 2
    return len(spec['steps'])


def card_layout(c, card, number, w, size, small):
    """Measures one cheat-sheet card once (wrapping reports problems, so it must run only once).
    A scene goes below the items, across the card: beside them it squeezes the text in a 3-column sheet."""
    icon = str(card.get('icon', '') or '')
    if len(icon) > 4 and not icons.known(icon):
        # up to 4 characters is a text mark ("for", "[ ]"); longer is meant as an icon name, so a typo is reported
        c.unknown_icon(icon)
    scene = card.get('scene')
    if isinstance(scene, list):
        scene = {'steps': scene}
    elif scene is not None and not isinstance(scene, dict):
        raise ValueError(f'card {number} scene must be {{steps, ops, label}} or a list of steps')
    badge = size * 2.1 if icon else 0
    inner = w - 2 * 14
    # `number` replaces the automatic one: "1-2" for a card that sums up two chapters
    if re.match(r'\d+(-\d+)?\.\s', str(card['title'])):
        c.problems.append(f'card {number}: the title starts with a number, which diagram.py already writes '
                          '(drop it; for a card of several chapters, give number: "1-2")')
    title =c.wrap(f'{card.get("number", number)}. {card["title"]}', size, inner - (badge + 10 if badge else 0))
    items = []
    for item in card.get('items', []):
        text, mark = (item.get('text', ''), item.get('icon')) if isinstance(item, dict) else (item, None)
        items.append((mark or 'circle-check', c.wrap(text, small, inner - small * 1.7)))
    code = list(card.get('code', []))
    for line in code:
        if c.width_of(line, small, mono=True) > inner - 12:
            c.problems.append(f'code "{line}" does not fit in a card')
    head = max(badge, len(title) * size * 1.3)
    body = sum(len(lines) for _, lines in items) * small * 1.45 + (len(code) * small * 1.3 + 14 if code else 0)
    scene_h = scene_size(c, inner, scene)[2] + small if scene else 0
    h = 14 + head + small * 0.6 + body + scene_h + 14
    return {'icon': icon, 'badge': badge, 'inner': inner, 'title': title, 'items': items,
            'code': code, 'head': head, 'h': h, 'scene': scene}


def draw_card(c, card, lay, x, y, w, h, color, size, small):
    c.rect(x, y, w, h, color, rx=14, tint=True)
    strong = PALETTE[color][2]
    if lay['badge']:
        b = lay['badge']
        c.parts.append(f'<rect x="{x + 14}" y="{y + 14}" width="{b}" height="{b}" rx="{b * 0.22}" '
                       f'fill="{PALETTE[color][0]}" stroke="{PALETTE[color][1]}" stroke-width="1.5"/>')
        if icons.known(lay['icon']):
            c.icon(lay['icon'], x + 14 + b * 0.2, y + 14 + b * 0.2, b * 0.6, color)
        else:
            # a short text mark (e.g. "for", "[ ]"), as in specs written before the icon library
            c.text(x + 14 + b / 2, y + 14 + b / 2 + small * 0.36, lay['icon'][:4], size=small, mono=True,
                   weight=700, fill=strong)
    tx = x + 14 + (lay['badge'] + 10 if lay['badge'] else 0)
    title_h = len(lay['title']) * size * 1.3
    c.lines(tx, y + 14 + lay['head'] / 2 - title_h / 2 - size * 0.2, lay['title'], size=size, anchor='start',
            weight=800, fill=strong)
    cy = y + 14 + lay['head'] + small * 0.6
    for mark, lines in lay['items']:
        c.icon(mark, x + 14, cy + small * 0.12, small * 1.15, color)
        for k, line in enumerate(lines):
            c.text(x + 14 + small * 1.7, cy + small * (1.0 + k * 1.45), line, size=small, anchor='start')
        cy += len(lines) * small * 1.45
    if lay['code']:
        code_h = len(lay['code']) * small * 1.3 + 8
        c.parts.append(f'<rect x="{x + 12}" y="{cy + 4}" width="{lay["inner"] + 4}" height="{code_h}" rx="6" '
                       f'fill="#FFFFFF" opacity="0.75"/>')
        c.lines(x + 20, cy + 4, lay['code'], size=small, anchor='start', mono=True)
        cy += code_h + 10
    if lay['scene']:
        scene_block(c, x + 14, cy + small * 0.6, lay['inner'], lay['scene'], color)


def cards(c, spec, profile):
    items = spec['cards']
    columns = 3 if profile == 'large' else 2
    gap = c.pad / 2
    w = (c.w - 2 * c.pad - (columns - 1) * gap) / columns
    size, small = c.p['body'] * 0.85, c.p['small'] * 0.95
    colors = ('blue', 'purple', 'teal', 'green', 'orange', 'red')
    rows = [items[i:i + columns] for i in range(0, len(items), columns)]
    for r, row in enumerate(rows):
        layouts = [card_layout(c, card, r * columns + k + 1, w, size, small)
                   for k, card in enumerate(row)]
        h = max(lay['h'] for lay in layouts)
        for k, (card, lay) in enumerate(zip(row, layouts, strict=True)):
            color = colors[(r * columns + k) % len(colors)]
            draw_card(c, card, lay, c.pad + k * (w + gap), c.y, w, h, color, size, small)
        c.y += h + gap
    c.y += c.pad / 2
    if len(items) > 12:
        c.problems.append(f'{len(items)} cards: a cheat sheet holds at most 12')
    return 0  # cards are a reference sheet, not a diagram to take in at a glance


# ---------- music: chord diagrams, the fretboard and tablature ----------
