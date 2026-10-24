# jcssicaxie.com — Portfolio, Edition 2026

The portfolio of Jessica Xie, art-directed as an independent publication: a cover, a selected-work section, a full index, and individual project pages.

Still plain HTML, CSS and JavaScript, published by GitHub Pages from `main` with the custom domain in `CNAME`. No framework, no npm, no GitHub Actions.

## Structure

```
index.html            Cover, selected work, note, "also in this edition", closing page
work.html             Index of work (filterable: work.html#ui, #ux, #graphic, #editorial, #photography)
work/<slug>.html      One page per project
about.html            About + contact sheet
contact.html          Contact
404.html              "Erratum" page (GitHub Pages serves it automatically)
assets/css/jx.css     The whole design system (tokens, grid, type, components)
assets/js/jx.js       Small enhancements: theme, menu, filter, previews, page strip
assets/img/           Optimised WebP images (generated)
_build/content.json   ALL text and image choices live here
_build/build.py       Generates every page from content.json
_build/images.json    Generated image manifest (sizes, keys)
images/, documents/   Your original files (untouched, still the source)
projects/*.html, works.html, cv.html
                      Redirects from the old URLs to the new pages
```

## Editing content

1. Edit `_build/content.json` (texts, metadata, which images, in what layout).
2. Run `python3 _build/build.py` from the repo root.
3. Preview: `python3 -m http.server 3333` and open http://localhost:3333
   (the "portfolio" launch config in `.claude/launch.json` does the same).

Adding new images needs Pillow once: `pip3 install pillow`. The build then creates
640/1200/2000px WebP versions automatically. Video posters need `ffmpeg` (optional).

### Image block layouts (in a project's `blocks`)

| type      | what it does |
|-----------|--------------|
| `full`    | edge-to-edge image |
| `wide`    | 11 of 12 columns |
| `offset`  | 8 columns, `"side": "left"` or `"right"` |
| `pair`    | two images, `"ratio": "6-6" / "7-5" / "5-7"`, optional `"stagger": true` |
| `trio`    | three images with a stepped rhythm |
| `row`     | n equal images (posters, flyers); items may be `{"video": "..."}` |
| `sheet`   | small contact-sheet grid |
| `scroll`  | tall full-page designs in scrollable frames |
| `pages`   | horizontal magazine page strip |
| `heading` | a section label + one line of text |

Projects can also have `chapters` (see Lowside).

## Design system in one paragraph

Background `#F5F4F0`, ink `#0B0B0A`, cream `#FDFBE2` panels, and one accent: pink `#F973B8`
(from the previous site), used as "pink ink" for the script and the hand-drawn oval.
Text links ("CLICK to…") use the same pink. In dark mode the accent becomes turquoise `#1EBDB5`. Jost for everything (display, body, labels),
Pinyon Script for handwriting, Ballet only for the name on the cover. The 12-column grid (8 on tablet, 4 on phone) is asymmetric by design. The site is
always light by default; dark mode only appears when a visitor presses the toggle. Motion respects `prefers-reduced-motion`.

## Content still to add (not invented)

- A CV PDF, if you want one linked from About.
- Short reflections per project (each page has room under the intro; add a `body` paragraph).
- LumiRise: images and `documents/DesignRationaleLumiRise.pdf` exist but it was not on the old
  site, so it is not in the index yet.
- Year for the photos on About, if you want them captioned.

## Notes

- The old `styles/`, `scripts/` and `font/` folders are no longer used by any page and can be deleted.
