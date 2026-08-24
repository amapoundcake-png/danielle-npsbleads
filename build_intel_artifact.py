"""
build_intel_artifact.py — render the Orlando intel digest as a self-contained
HTML page, ready to hand to the Artifact publish tool.

This is separate from orlando_intel.py's own Markdown report because the
HTML page is meant for a specific audience (a published Claude Artifact,
viewable by anyone with the link) with its own layout, fonts, and light/dark
theming, not for the plain-text digest orlando_intel.py already produces.

Usage:
  python build_intel_artifact.py [output_path]
  (defaults to orlando_intel_digest.html in the current directory)
"""

import html
import sys
from datetime import datetime

from orlando_intel import gather_digest, CATEGORIES, ORLANDO_INTEL_LOOKBACK_DAYS

# Which brand pipeline (from CLAUDE.md's positioning guide) each category
# is color-coded to in the digest's left rail.
PIPELINE = {
    "nonprofit_opportunities": ("danielle", "Danielle Adams"),
    "conferences": ("danni", "Danni Adams"),
    "networking_events": ("danni", "Danni Adams"),
    "creator_events": ("brand", "Amapoundcake"),
    "creators_talent": ("brand", "Danni Adams / Amapoundcake"),
    "brand_activations": ("brand", "Amapoundcake"),
    "business_openings": ("brand", "Amapoundcake / Danielle Adams"),
    "cultural_events": ("danni", "Danni Adams / Amapoundcake"),
    "marketing_news": ("neutral", "Trend watch"),
    "events": ("neutral", "General radar"),
}


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def render(buckets: dict, lookback_days: int) -> str:
    total_items = sum(len(items) for items in buckets.values())
    all_sources = {item["source"] for items in buckets.values() for item in items}
    gen_label = datetime.now().strftime("%A, %B %-d, %Y · %-I:%M %p")

    nav_items = []
    sections = []

    for key, items in buckets.items():
        meta = CATEGORIES[key]
        pipeline_key, pipeline_label = PIPELINE.get(key, ("neutral", ""))
        count = len(items)

        nav_items.append(
            f'<a class="nav-link" data-pipeline="{pipeline_key}" href="#{key}">'
            f'<span class="nav-dot"></span><span class="nav-label">{esc(meta["label"])}</span>'
            f'<span class="nav-count">{count}</span></a>'
        )

        item_rows = []
        if not items:
            item_rows.append('<p class="empty-note">Nothing cleared the filter this window.</p>')
        for it in items:
            date_str = it["published"].strftime("%b %d") if it["published"] else "undated"
            summary_html = f'<p class="item-summary">{esc(it["summary"])}</p>' if it["summary"] else ""
            item_rows.append(f'''
        <article class="item">
          <div class="item-meta"><span class="item-source">{esc(it["source"])}</span><span class="item-dot">·</span><span class="item-date">{esc(date_str)}</span></div>
          <h3 class="item-title"><a href="{esc(it["link"])}" target="_blank" rel="noopener">{esc(it["title"])}</a></h3>
          {summary_html}
        </article>''')

        sections.append(f'''
      <section class="category" id="{key}" data-pipeline="{pipeline_key}">
        <header class="category-head">
          <div class="category-heading">
            <h2>{esc(meta["label"])}</h2>
            <span class="category-count">{count} item{"s" if count != 1 else ""}</span>
          </div>
          <p class="category-angle"><span class="angle-tag">{esc(pipeline_label)}</span>{esc(meta["brand_note"])}</p>
        </header>
        <div class="item-list">
          {"".join(item_rows)}
        </div>
      </section>''')

    nav_html = "\n".join(nav_items)
    sections_html = "\n".join(sections)

    return f'''<title>Orlando Intel Digest</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Libre+Caslon+Display&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<div class="page">

  <header class="masthead">
    <div class="masthead-top">
      <p class="kicker">Central Florida Intelligence Wire</p>
      <h1>ORLANDO INTEL</h1>
    </div>
    <div class="masthead-stats">
      <div class="stat"><span class="stat-value">{total_items}</span><span class="stat-label">items</span></div>
      <div class="stat"><span class="stat-value">{len(buckets)}</span><span class="stat-label">categories</span></div>
      <div class="stat"><span class="stat-value">{len(all_sources)}</span><span class="stat-label">sources</span></div>
      <div class="stat"><span class="stat-value">{lookback_days}d</span><span class="stat-label">lookback</span></div>
    </div>
    <p class="dateline">Filed {esc(gen_label)}</p>
  </header>

  <p class="scan-note">Sourced from Orlando/Central Florida RSS plus keyword-matched Google News searches. Matching is loose by design &mdash; skim for the off-topic straggler before acting on anything.</p>

  <div class="layout">
    <nav class="rail" aria-label="Categories">
      <p class="rail-label">Jump to</p>
      {nav_html}
    </nav>

    <main class="content">
      {sections_html}
    </main>
  </div>

  <footer class="colophon">
    <p>Generated by <code>orlando_intel.py</code> &middot; danielle&#8209;npsbleads &middot; refreshes daily</p>
  </footer>
</div>

<style>
  :root {{
    --paper: #eef2f1;
    --paper-raised: #ffffff;
    --paper-sunken: #e2e8e6;
    --ink: #16221f;
    --ink-soft: #46564f;
    --ink-faint: #7c8b84;
    --hairline: #c9d3cf;
    --accent: #d9591f;
    --accent-ink: #ffffff;
    --pipeline-danielle: #2e4057;
    --pipeline-danni: #b9791f;
    --pipeline-brand: #9a3b6b;
    --pipeline-neutral: #5b6b66;
    --focus: #2e4057;

    --font-display: 'Libre Caslon Display', Georgia, 'Times New Roman', serif;
    --font-body: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono: 'IBM Plex Mono', 'SF Mono', Consolas, monospace;
  }}

  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --paper: #12181a;
      --paper-raised: #1a2224;
      --paper-sunken: #0d1214;
      --ink: #eaeee9;
      --ink-soft: #b7c2bc;
      --ink-faint: #7c8b84;
      --hairline: #2c3a37;
      --accent: #ef7b3a;
      --accent-ink: #14100b;
      --pipeline-danielle: #7f9bc2;
      --pipeline-danni: #e0ac4d;
      --pipeline-brand: #d97fab;
      --pipeline-neutral: #8ea198;
      --focus: #ef7b3a;
    }}
  }}

  :root[data-theme="dark"] {{
    --paper: #12181a;
    --paper-raised: #1a2224;
    --paper-sunken: #0d1214;
    --ink: #eaeee9;
    --ink-soft: #b7c2bc;
    --ink-faint: #7c8b84;
    --hairline: #2c3a37;
    --accent: #ef7b3a;
    --accent-ink: #14100b;
    --pipeline-danielle: #7f9bc2;
    --pipeline-danni: #e0ac4d;
    --pipeline-brand: #d97fab;
    --pipeline-neutral: #8ea198;
    --focus: #ef7b3a;
  }}

  * {{ box-sizing: border-box; }}
  html {{ background: var(--paper); }}

  body {{
    background: var(--paper);
    color: var(--ink);
    font-family: var(--font-body);
    font-size: 15px;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
  }}

  a {{ color: inherit; }}
  a:focus-visible, button:focus-visible {{
    outline: 2px solid var(--focus);
    outline-offset: 2px;
  }}

  .page {{
    max-width: 1180px;
    margin: 0 auto;
    padding: 2.5rem 1.5rem 4rem;
  }}

  .masthead {{
    border-bottom: 3px solid var(--ink);
    padding-bottom: 1.1rem;
    margin-bottom: 0.6rem;
  }}
  .masthead-top {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.4rem 1.5rem;
  }}
  .kicker {{
    font-family: var(--font-mono);
    font-size: 0.7rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--accent);
    margin: 0;
  }}
  h1 {{
    font-family: var(--font-display);
    font-size: clamp(2.4rem, 5vw, 3.6rem);
    letter-spacing: 0.01em;
    margin: 0.1rem 0 0;
    text-wrap: balance;
    line-height: 0.95;
  }}
  .masthead-stats {{
    display: flex;
    gap: clamp(1.2rem, 4vw, 2.4rem);
    margin-top: 1.1rem;
    flex-wrap: wrap;
  }}
  .stat {{ display: flex; flex-direction: column; }}
  .stat-value {{
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--ink);
  }}
  .stat-label {{
    font-family: var(--font-mono);
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ink-faint);
  }}
  .dateline {{
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: var(--ink-faint);
    margin: 0.9rem 0 0;
  }}

  .scan-note {{
    font-size: 0.85rem;
    color: var(--ink-soft);
    max-width: 62ch;
    margin: 1.1rem 0 2.2rem;
    padding-left: 0.85rem;
    border-left: 2px solid var(--hairline);
  }}

  .layout {{
    display: grid;
    grid-template-columns: 200px minmax(0, 1fr);
    gap: 2.5rem;
    align-items: start;
  }}

  .rail {{
    position: sticky;
    top: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
  }}
  .rail-label {{
    font-family: var(--font-mono);
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--ink-faint);
    margin: 0 0 0.5rem;
  }}
  .nav-link {{
    display: grid;
    grid-template-columns: 8px 1fr auto;
    align-items: center;
    gap: 0.55rem;
    padding: 0.42rem 0.4rem;
    border-radius: 4px;
    text-decoration: none;
    font-size: 0.86rem;
    color: var(--ink-soft);
    transition: background-color 0.15s ease, color 0.15s ease;
  }}
  .nav-link:hover {{ background: var(--paper-sunken); color: var(--ink); }}
  .nav-link.active {{ background: var(--paper-sunken); color: var(--ink); font-weight: 600; }}
  .nav-dot {{
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--pipeline-neutral);
  }}
  .nav-link[data-pipeline="danielle"] .nav-dot {{ background: var(--pipeline-danielle); }}
  .nav-link[data-pipeline="danni"] .nav-dot {{ background: var(--pipeline-danni); }}
  .nav-link[data-pipeline="brand"] .nav-dot {{ background: var(--pipeline-brand); }}
  .nav-count {{
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
    font-size: 0.75rem;
    color: var(--ink-faint);
  }}

  .content {{ display: flex; flex-direction: column; gap: 3rem; min-width: 0; }}

  .category {{
    border-left: 3px solid var(--pipeline-neutral);
    padding-left: 1.3rem;
    scroll-margin-top: 1.5rem;
  }}
  .category[data-pipeline="danielle"] {{ border-color: var(--pipeline-danielle); }}
  .category[data-pipeline="danni"] {{ border-color: var(--pipeline-danni); }}
  .category[data-pipeline="brand"] {{ border-color: var(--pipeline-brand); }}

  .category-head {{ margin-bottom: 1.1rem; }}
  .category-heading {{
    display: flex;
    align-items: baseline;
    gap: 0.7rem;
    flex-wrap: wrap;
  }}
  .category-heading h2 {{
    font-family: var(--font-display);
    font-size: 1.5rem;
    margin: 0;
    text-wrap: balance;
  }}
  .category-count {{
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--ink-faint);
  }}
  .category-angle {{
    margin: 0.35rem 0 0;
    font-size: 0.83rem;
    color: var(--ink-soft);
    max-width: 68ch;
  }}
  .angle-tag {{
    font-family: var(--font-mono);
    font-size: 0.68rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    background: var(--paper-sunken);
    color: var(--ink);
    padding: 0.15rem 0.45rem;
    border-radius: 3px;
    margin-right: 0.55rem;
    display: inline-block;
  }}

  .item-list {{ display: flex; flex-direction: column; }}
  .item {{
    padding: 0.85rem 0;
    border-top: 1px solid var(--hairline);
  }}
  .item:first-child {{ border-top: none; padding-top: 0; }}
  .item-meta {{
    font-family: var(--font-mono);
    font-size: 0.72rem;
    color: var(--ink-faint);
    display: flex;
    gap: 0.4rem;
    margin-bottom: 0.15rem;
  }}
  .item-title {{
    font-family: var(--font-body);
    font-weight: 600;
    font-size: 0.98rem;
    margin: 0;
    line-height: 1.4;
  }}
  .item-title a {{
    text-decoration: none;
    background-image: linear-gradient(var(--ink-faint), var(--ink-faint));
    background-size: 100% 1px;
    background-repeat: no-repeat;
    background-position: 0 100%;
  }}
  .item-title a:hover {{ color: var(--accent); background-image: linear-gradient(var(--accent), var(--accent)); }}
  .item-summary {{
    margin: 0.3rem 0 0;
    font-size: 0.86rem;
    color: var(--ink-soft);
    max-width: 68ch;
  }}
  .empty-note {{ color: var(--ink-faint); font-size: 0.85rem; font-style: italic; }}

  .colophon {{
    margin-top: 3.5rem;
    padding-top: 1rem;
    border-top: 1px solid var(--hairline);
    font-family: var(--font-mono);
    font-size: 0.72rem;
    color: var(--ink-faint);
  }}
  .colophon code {{
    background: var(--paper-sunken);
    padding: 0.1rem 0.35rem;
    border-radius: 3px;
  }}

  @media (max-width: 860px) {{
    .layout {{ grid-template-columns: 1fr; }}
    .rail {{
      position: static;
      flex-direction: row;
      flex-wrap: wrap;
      gap: 0.4rem;
      margin-bottom: 0.5rem;
    }}
    .rail-label {{ display: none; }}
    .nav-link {{
      grid-template-columns: 8px auto auto;
      background: var(--paper-raised);
      border: 1px solid var(--hairline);
    }}
  }}

  @media (prefers-reduced-motion: no-preference) {{
    html {{ scroll-behavior: smooth; }}
  }}
</style>

<script>
  (function () {{
    var links = Array.prototype.slice.call(document.querySelectorAll(".nav-link"));
    var sections = links.map(function (l) {{ return document.getElementById(l.getAttribute("href").slice(1)); }});
    if (!("IntersectionObserver" in window)) return;
    var observer = new IntersectionObserver(function (entries) {{
      entries.forEach(function (entry) {{
        var idx = sections.indexOf(entry.target);
        if (idx === -1) return;
        if (entry.isIntersecting) {{
          links.forEach(function (l) {{ l.classList.remove("active"); }});
          links[idx].classList.add("active");
        }}
      }});
    }}, {{ rootMargin: "-10% 0px -70% 0px" }});
    sections.forEach(function (s) {{ if (s) observer.observe(s); }});
  }})();
</script>
'''


if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else "orlando_intel_digest.html"
    buckets = gather_digest()
    page = render(buckets, ORLANDO_INTEL_LOOKBACK_DAYS)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
    total = sum(len(items) for items in buckets.values())
    print(f"Wrote {out_path} ({total} items across {len(buckets)} categories)")
