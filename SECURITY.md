# Security

**English** | [Português](SECURITY.pt-BR.md)

## Reporting a problem

If you find a security problem in the skill or the scripts (for example, something that exposes the user's tokens, passwords or files), **do not open a public issue**.

Use GitHub's private reporting: the repository's **Security** tab → **Report a vulnerability**. Describe the problem, how to reproduce it and its impact.

You will get a first answer within 7 days. When there is a fix, it goes into the [CHANGELOG](CHANGELOG.md) and the repository's security advisory.

## Practices the skill follows

- It never asks you to paste tokens, passwords or keys into the chat. Connections go through Claude's connectors (Notion, Google Drive, GitHub in the Claude app) or through your own login in Claude Code (`gh auth login` for GitHub).
- It does not download instructions from the internet while running: everything it follows comes in the installed package.
- Materials you send are used only as sources: the original files are never published. In Improve mode, the improved book goes to your library like any other book.
- Text inside your materials, web pages and other people's books is treated as content, never as instructions. Commands and projects of a book the skill did not write in the same session are shown to you before they run.
- The scripts download only over https, only images of at most 25 MB (an SVG with scripts is refused) and materials of at most 50 MB; image and project names that point outside the book's folders are refused, and they delete only files they generated themselves; the VS Code server used for screenshots listens only on your computer (127.0.0.1) and sees the book's folder read-only.
- A report of a problem in the skill (`scripts/report.py`) is sent only after you say yes, as a public issue in this repository. It carries what happened, the command, the error message, the skill version and the system; your home folder, user name, e-mail addresses and anything that looks like a token or password are removed first, and it never includes passages of your books or materials. You see the whole report before deciding.

## Supported versions

Only the latest version of the skill receives fixes.
