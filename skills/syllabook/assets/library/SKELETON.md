# Library skeleton

The skill copies these files into the user's library repository when it does not have them yet (`modes/PUBLISH.md` §2). The same files, without this note, make up the library template (https://github.com/Joshpcbrrj/syllabook-library), kept in sync by `tools/sync_template.py`. Never overwrite a file that already exists there, and never copy this note (`SKELETON.md`).

| File | Where it goes |
| --- | --- |
| `README.md`, `README.pt-BR.md` | repository root: the library's front page; `build.py lists` turns the site address into a link once `repository` is set in `library.yaml`, opens the page with **📂 Folders** (a link to each folder below and how many books it holds) and then lists every book with its website and EPUB, by track |
| `LICENSE`, `LICENSE-CODIGO` | repository root: CC BY-SA 4.0 for the content, MIT for code; the user may choose others |
| `library.yaml` | repository root; the skill fills `author`, `repository`, `commit_name` and `commit_email` |
| `created-books/`, `improved-materials/`, `translated-books/`, `site/` | repository root, with their READMEs in English and Portuguese |
| `.github/workflows/epub.yml` | builds one EPUB per book on every push and publishes it on the `epub_release` release |
| `.github/workflows/site.yml` | builds the website with Zensical and publishes it on GitHub Pages (the user turns Pages on once: Settings → Pages → Source: GitHub Actions) |

**One folder per way the skill makes a book**, and every book in the folder of the mode that made it: `created-books/<slug>/` (Create and the next book in a track), `improved-materials/<slug>/` (Improve), `translated-books/<slug>-<lang>/` (Translate). Never put a book at the root, in `site/` or in a folder of its own choosing: the front page, the lists, the website and the EPUB workflow find books only there. After adding, moving or publishing a book, run `build.py lists`, so the folder links and counts on the front page stay right.

Both workflows do nothing while the library has no books. They use the scripts in the repository when it has a copy of the skill, and otherwise download the latest Syllabook release.
