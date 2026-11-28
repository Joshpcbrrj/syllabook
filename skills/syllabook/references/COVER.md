# Cover

A book cover, not a template: original, clean and readable as a small thumbnail.

## Content

- Title and subtitle, in the book language.
- "by <author>" with `author` from `library.yaml` (in the book language, e.g. "por <author>"). With no `author` there, ask the user for the name to show and write it in `library.yaml` before drawing; a cover without it has to be redrawn when the book is published in a library that has one.
- For improved materials, a small line under the subtitle: the kind of original ("based on course notes").
- No third-party logos, brands, mascots or characters, ever. Represent a technology with an original abstract shape, never its logo.

## Format

- Source in SVG (`cover.svg`), exported to PNG at **1600 × 2560** (`cover.png`) for the EPUB. Text as real text, not paths.
- One idea in the artwork: an abstract shape or a simple scene that hints at the topic (stacked blocks for containers, sound waves for music, a timeline for history).
- Two typefaces at most; the title fills about a third of the width and stays readable at 160 px wide.
- High contrast between text and background; works in grayscale.
- A consistent series look per library: same layout grid and type, a different accent color per track.

## Process

1. Write in one sentence the visual idea and the accent color.
2. Build the SVG with a `viewBox` of 1600 × 2560. When the library already has covers, reuse the layout grid and type of one of them (`cover.svg` in another book's folder) and change only the artwork and the accent color.
3. Render the PNG with `python scripts/diagram.py --png cover.svg` and look at it at two sizes: full and 160 px wide.
4. Check: title readable at 160 px; nothing touching the edges; no third-party marks; author and edition correct.
