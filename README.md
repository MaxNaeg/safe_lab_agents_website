# safe-lab-agents.org

Static single-page website for the **Safe Lab Agents** open-source project.
Hand-written HTML + CSS, no build framework. All page text lives in a single
Markdown file (`content.md`); a small Python script assembles `index.html`
from that Markdown plus an HTML template.

## Files

```
content.md         # all textual content (edit this)
template.html      # HTML skeleton with {{slot}} placeholders
build.py           # renders content.md + template.html -> index.html
index.html         # generated — do not edit by hand
style.css          # all styling (dark theme, orange accent, three font sizes)
CNAME              # custom domain for GitHub Pages
assets/            # images, background, screenshots, (later) video
```

## Editing workflow

1. Open `content.md` and edit text, or add/remove steps.
2. Run:

   ```bash
   python3 build.py
   ```

   This regenerates `index.html`.
3. Reload the browser to see the change (hard-reload with **Cmd+Shift+R** if
   the CSS or fonts don't seem to update — the browser caches them).

Requires Python 3.9+. No external dependencies.

### Content structure

`content.md` is split into sections separated by lines containing only `---`:

1. **Hero** — `# Title`, then paragraphs of subtitle text, optional figures.
2. **Steps** — one `## Step title` per numbered step; each may contain text,
   a `> terminal command` blockquote, and an `![](assets/image.jpg)` figure.
3. **Video** — currently hidden in the template (uncomment the block in
   `template.html` when the demo video is ready).
4. **Learn more** — heading + link(s).

HTML comments `<!--- hint --->` before an image or blockquote act as *hints*:

- `<!--- background --->` marks an image as the full-bleed hero background.
- `<!--- centered 50% --->` renders the following image as a centered figure
  at 50% container width (any percent works).
- `<!--- code for the terminal --->` documents that the following blockquote
  is meant as a terminal snippet (rendered as a monospace box with a `$` prompt).

## Local preview

Any static server works. Simplest:

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

Or use the VS Code "Live Server" extension for auto-reload on save.

## Deploy to GitHub Pages

1. Create a new GitHub repo (e.g. `safe-lab-agents-website`).
2. Push the contents of this folder to the repo's `main` branch.
3. In the repo → **Settings → Pages**, set source to **`main` branch / root**.
4. Point DNS for `safe-lab-agents.org` at GitHub Pages
   (see <https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site>).
5. The `CNAME` file already in the repo tells Pages which domain to serve.

Because `index.html` is committed (generated ahead of time), GitHub Pages
just serves static files — no build step runs on GitHub's side.

## Assets currently referenced

Under `assets/`:

- `splash_background.jpg` — full-bleed hero background
- `fig_main_points.png` — centered vector figure in hero (transparent background)
- `tools_code.jpg` — step 2 screenshot
- `fig_agent_start.jpg` — step 3 screenshot
- `fig_browsing_auto_log.jpg` — step 4 screenshot
- `demo.mp4` + `video-poster.jpg` — for the (currently hidden) video section

## Design tokens

Edit the `:root` block at the top of `style.css` to tweak the look
globally:

- `--accent`, `--accent-hi` — orange used for step circles and links.
- `--font-sans`, `--font-mono` — currently Inter + JetBrains Mono
  (loaded from Google Fonts in `template.html`).
- `--bg`, `--fg`, `--fg` — the dark palette.
- `--maxw` — max content width (currently 1100px).

The whole document uses exactly three type sizes: the hero title
(`clamp(2.5rem, 7vw, 5.5rem)`), section/step titles (`1.75rem`), and body
text (`1.5rem`).
