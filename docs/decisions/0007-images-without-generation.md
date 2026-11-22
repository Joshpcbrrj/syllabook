# 7. Images: diagrams, free-license photos and real screenshots, no image generation

**English** | [Português](0007-images-without-generation.pt-BR.md)

**Status:** accepted · **Source:** `plano/PLANO.md §10`

## Context

Generated pictures can look real without being real, often carry wrong text, and need paid APIs and network access.

## Decision

Images are SVG diagrams drawn by a script from a spec, simple SVG illustrations for analogies (written as code and checked by a script), photos with a free license (public domain, CC0, CC BY, CC BY-SA) with their credit, and screenshots of the real application. No image-generation models, and no third-party logos or brands.

## Consequences

Every real image has its author, license and link in `img/CREDITS.md` and in the caption. A real photo or screenshot is never faked.
