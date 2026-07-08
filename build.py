#!/usr/bin/env python3
"""
Build index.html from content.md + template.html.

Content structure (sections separated by `---` on their own line):

    Section 1 — Hero:
        <!--- background --->   (annotation on the next image line)
        ![](assets/splash.svg)  (becomes full-bleed hero background)
        # Title
        Paragraph(s) of subtitle / description.
        <!--- centered 50% --->
        ![](assets/figure.svg)  (rendered as a centered figure)

    Section 2 — Steps:
        ## Step title
        Body paragraph(s).
        > terminal command      (blockquote = terminal code block)
        ![](assets/pic.png)     (step screenshot, optional)

    Section 3 — Video:
        ## Section headline
        ![](assets/demo.mp4)    (or a YouTube/Vimeo URL)

    Section 4 — Learn more (optional):
        ## Learn more
        [label](url)            (rendered as a big link/CTA)

Annotations in HTML comments (<!--- ... --->) act as *hints* for the
following image or blockquote:
    background     — treat image as full-bleed hero background
    centered NN%   — center the image at NN% width
    code for the terminal — render blockquote as a terminal snippet

Run:  python3 build.py
"""

from __future__ import annotations
import html
import re
from pathlib import Path

ROOT = Path(__file__).parent
CONTENT = ROOT / "content.md"
TEMPLATE = ROOT / "template.html"
OUTPUT = ROOT / "index.html"

SITE_TITLE = "Safe Lab Agents"
SITE_DESCRIPTION = "Safely run AI agents inside a sandbox to control scientific experiments."

COMMENT_RE = re.compile(r"<!---?\s*(.*?)\s*-?-->", re.DOTALL)
IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
BLOCKQUOTE_RE = re.compile(r"^>\s?(.*)$")


# ---------- tiny inline-markdown renderer ----------------------------------
# Handles: **bold**, *italic*, `code`, [text](url).

def inline_md(text: str) -> str:
    # Protect existing raw HTML by not escaping < > (we control inputs).
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                  lambda m: f'<a href="{html.escape(m.group(2))}"'
                            + (' target="_blank" rel="noopener"' if m.group(2).startswith("http") else "")
                            + f'>{html.escape(m.group(1))}</a>',
                  text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


# ---------- token stream ---------------------------------------------------
# Turn a Markdown block into a sequence of tokens with optional annotations
# from preceding HTML comments.

def tokenize(block: str) -> list[dict]:
    tokens: list[dict] = []
    pending_hint: str | None = None
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            text = " ".join(l.strip() for l in paragraph_lines).strip()
            if text:
                tokens.append({"kind": "p", "text": text})
            paragraph_lines = []

    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # HTML comment → hint for next token
        m = COMMENT_RE.match(stripped)
        if m:
            flush_paragraph()
            pending_hint = m.group(1).strip().lower()
            i += 1
            continue

        if not stripped:
            flush_paragraph()
            i += 1
            continue

        if stripped.startswith("# "):
            flush_paragraph()
            tokens.append({"kind": "h1", "text": stripped[2:].strip(), "hint": pending_hint})
            pending_hint = None
            i += 1
            continue

        if stripped.startswith("## "):
            flush_paragraph()
            tokens.append({"kind": "h2", "text": stripped[3:].strip(), "hint": pending_hint})
            pending_hint = None
            i += 1
            continue

        img = IMG_RE.match(stripped)
        if img:
            flush_paragraph()
            tokens.append({"kind": "img", "alt": img.group(1), "src": img.group(2), "hint": pending_hint})
            pending_hint = None
            i += 1
            continue

        bq = BLOCKQUOTE_RE.match(stripped)
        if bq:
            flush_paragraph()
            # collect consecutive blockquote lines
            bq_lines = [bq.group(1)]
            j = i + 1
            while j < len(lines) and BLOCKQUOTE_RE.match(lines[j].strip()):
                bq_lines.append(BLOCKQUOTE_RE.match(lines[j].strip()).group(1))
                j += 1
            tokens.append({"kind": "quote", "lines": bq_lines, "hint": pending_hint})
            pending_hint = None
            i = j
            continue

        paragraph_lines.append(line)
        i += 1

    flush_paragraph()
    return tokens


# ---------- section renderers ---------------------------------------------

def render_hero(tokens: list[dict]) -> dict:
    bg_src = ""
    title = ""
    subtitle_html_parts: list[str] = []

    for t in tokens:
        if t["kind"] == "img" and (t.get("hint") or "").startswith("background"):
            bg_src = t["src"]
        elif t["kind"] == "h1":
            title = t["text"]
        elif t["kind"] == "p":
            subtitle_html_parts.append(f'<p class="hero__text">{inline_md(t["text"])}</p>')
        elif t["kind"] == "img":
            hint = t.get("hint") or ""
            width_match = re.search(r"(\d+)%", hint)
            width = width_match.group(1) + "%" if width_match else "60%"
            cls = "hero__figure" + (" hero__figure--centered" if "centered" in hint else "")
            subtitle_html_parts.append(
                f'<figure class="{cls}" style="--fig-w: {width}">'
                f'<img src="{html.escape(t["src"])}" alt="{html.escape(t["alt"])}" />'
                f'</figure>'
            )

    return {
        "hero_bg": html.escape(bg_src) if bg_src else "assets/splash.svg",
        "hero_title": inline_md(title),
        "hero_body": "\n      ".join(subtitle_html_parts),
    }


def render_step_content(tokens: list[dict]) -> tuple[str, str]:
    """Return (body_html, figure_html) for a single step's inner tokens."""
    body_parts: list[str] = []
    figure_html = ""

    for t in tokens:
        if t["kind"] == "p":
            body_parts.append(f'<p class="step__text">{inline_md(t["text"])}</p>')
        elif t["kind"] == "quote":
            code = "\n".join(t["lines"])
            body_parts.append(
                f'<pre class="step__terminal"><code>{html.escape(code)}</code></pre>'
            )
        elif t["kind"] == "img":
            figure_html = (
                f'<div class="step__figure">'
                f'<img src="{html.escape(t["src"])}" alt="{html.escape(t["alt"])}" />'
                f'</div>'
            )
    return "\n          ".join(body_parts), figure_html


def render_steps(tokens: list[dict]) -> str:
    # group tokens into steps by h2 boundaries
    steps: list[tuple[str, list[dict]]] = []
    current_title = None
    current: list[dict] = []
    for t in tokens:
        if t["kind"] == "h2":
            if current_title is not None:
                steps.append((current_title, current))
            current_title = t["text"]
            current = []
        else:
            if current_title is None:
                continue  # ignore anything before first ##
            current.append(t)
    if current_title is not None:
        steps.append((current_title, current))

    rendered: list[str] = []
    for i, (title, inner) in enumerate(steps, start=1):
        body_html, figure_html = render_step_content(inner)
        rendered.append(f'''<li class="step">
        <div class="step__num">{i}</div>
        <div class="step__body">
          <h3 class="step__title">{inline_md(title)}</h3>
          {body_html}
        </div>
        {figure_html}
      </li>''')
    return "\n      ".join(rendered)


def render_video(tokens: list[dict]) -> dict:
    title = "See it in action"
    embed = ""
    for t in tokens:
        if t["kind"] == "h2":
            title = t["text"]
        elif t["kind"] == "img":
            src = t["src"]
            if src.endswith((".mp4", ".webm", ".mov")):
                embed = (f'<video controls poster="assets/video-poster.jpg">'
                         f'<source src="{html.escape(src)}" type="video/mp4" />'
                         f'</video>')
            else:
                embed = (f'<iframe src="{html.escape(src)}" '
                         f'allowfullscreen loading="lazy"></iframe>')
    return {"video_title": inline_md(title), "video_embed": embed}


def render_learn_more(tokens: list[dict]) -> dict:
    title = "Learn more"
    parts: list[str] = []
    for t in tokens:
        if t["kind"] == "h2":
            title = t["text"]
        elif t["kind"] == "p":
            parts.append(f'<p class="learn__text">{inline_md(t["text"])}</p>')
    return {
        "learn_title": inline_md(title),
        "learn_body": "\n      ".join(parts),
    }

def render_discussion(tokens: list[dict]) -> dict:
    title = "Join the discussion"
    parts: list[str] = []
    for t in tokens:
        if t["kind"] == "h2":
            title = t["text"]
        elif t["kind"] == "p":
            parts.append(f'<p class="discussion__text">{inline_md(t["text"])}</p>')
    return {
        "discussion_title": inline_md(title),
        "discussion_body": "\n      ".join(parts),
    }


# ---------- main -----------------------------------------------------------

def build() -> None:
    md = CONTENT.read_text(encoding="utf-8")
    raw_sections = [s.strip() for s in re.split(r"(?m)^---\s*$", md) if s.strip()]
    if len(raw_sections) < 3:
        raise SystemExit(
            f"Expected at least 3 sections separated by `---`, got {len(raw_sections)}."
        )

    hero_tok = tokenize(raw_sections[0])
    steps_tok = tokenize(raw_sections[1])
    video_tok = tokenize(raw_sections[2])
    learn_tok = tokenize(raw_sections[3]) if len(raw_sections) > 3 else []
    discussion_tok = tokenize(raw_sections[4]) if len(raw_sections) > 4 else []
    
    ctx: dict[str, str] = {
        "site_title": SITE_TITLE,
        "site_description": SITE_DESCRIPTION,
    }
    ctx.update(render_hero(hero_tok))
    ctx["steps"] = render_steps(steps_tok)
    ctx.update(render_video(video_tok))
    ctx.update(render_learn_more(learn_tok))
    ctx.update(render_discussion(discussion_tok))

    tpl = TEMPLATE.read_text(encoding="utf-8")
    out = re.sub(r"\{\{(\w+)\}\}", lambda m: ctx.get(m.group(1), ""), tpl)
    OUTPUT.write_text(out, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
