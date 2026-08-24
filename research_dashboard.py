"""
research_dashboard.py — renders central_fl_research.csv as a static HTML
dashboard (Central Florida Wire) for publishing as an Artifact.

Usage:
    python research_dashboard.py [output_path]

Reads central_fl_research.csv from the repo root and writes a self-contained
HTML file (default: central_fl_wire.html) with the current data embedded
directly in the page. Re-run this after event_research.py appends new rows,
then re-publish the output file to update the live dashboard.
"""

import csv
import html
import json
import os
import re
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(__file__)
RESEARCH_CSV = os.path.join(REPO_ROOT, "central_fl_research.csv")
DEFAULT_OUTPUT = os.path.join(REPO_ROOT, "central_fl_wire.html")

CATEGORY_LABELS = {
    "black_cultural": "Black Cultural",
    "womens": "Women's",
    "creator": "Creator",
    "nonprofit_programs": "Nonprofit Programs",
    "community": "Community",
    "holiday_activation": "Holiday Activation",
    "influencer_campaign": "Influencer Campaigns",
    "new_location": "New Locations",
    "product_launch": "Product Launches",
    "funding_opening": "Funding & Openings",
    "nonprofit_campaign": "Nonprofit Campaigns",
}

BUCKET_LABELS = {
    "event": "Event",
    "business_signal": "Business Signal",
}


def _parse_pubdate(raw: str):
    """Parse an RFC-822 pubDate string; return a datetime or None."""
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%a, %d %b %Y %H:%M:%S %Z")
    except ValueError:
        return None


def _clean_snippet(snippet: str, title: str) -> str:
    """Drop snippets that just repeat the title (common in RSS descriptions)."""
    cleaned = re.sub(r"\s+", " ", (snippet or "").replace("\xa0", " ")).strip()
    title_clean = re.sub(r"\s+", " ", (title or "")).strip()
    if not cleaned or cleaned.lower().startswith(title_clean.lower()[:40].lower()):
        return ""
    return cleaned


def load_rows(csv_path: str = RESEARCH_CSV) -> list[dict]:
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        dt = _parse_pubdate(r.get("published", ""))
        r["_sort_date"] = dt.isoformat() if dt else r.get("date_found", "")
        r["_display_date"] = dt.strftime("%b %-d, %Y") if dt else r.get("date_found", "")
        r["snippet"] = _clean_snippet(r.get("snippet", ""), r.get("title", ""))
        r["category_label"] = CATEGORY_LABELS.get(r.get("category", ""), r.get("category", ""))
        r["bucket_label"] = BUCKET_LABELS.get(r.get("bucket", ""), r.get("bucket", ""))

    rows.sort(key=lambda r: r["_sort_date"], reverse=True)
    return rows


PAGE_TEMPLATE = """<title>Central Florida Wire</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,500&family=Public+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
  :root {
    --paper: #F2F5F3;
    --paper-raised: #FFFFFF;
    --ink: #17212B;
    --ink-soft: #5B6B66;
    --ink-faint: #8A9793;
    --line: #D8DEDC;
    --line-soft: #E6EAE8;
    --accent-event: #E2622A;
    --accent-event-soft: #FBE7DC;
    --accent-signal: #1F6F5C;
    --accent-signal-soft: #DCEAE5;
    --focus: #1F6F5C;
  }

  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --paper: #121A1F;
      --paper-raised: #182229;
      --ink: #EAF0EE;
      --ink-soft: #9FB0AB;
      --ink-faint: #6C7C78;
      --line: #2A363B;
      --line-soft: #223037;
      --accent-event: #F0834F;
      --accent-event-soft: #3A2A22;
      --accent-signal: #4FAE93;
      --accent-signal-soft: #1C332C;
      --focus: #4FAE93;
    }
  }

  :root[data-theme="dark"] {
    --paper: #121A1F;
    --paper-raised: #182229;
    --ink: #EAF0EE;
    --ink-soft: #9FB0AB;
    --ink-faint: #6C7C78;
    --line: #2A363B;
    --line-soft: #223037;
    --accent-event: #F0834F;
    --accent-event-soft: #3A2A22;
    --accent-signal: #4FAE93;
    --accent-signal-soft: #1C332C;
    --focus: #4FAE93;
  }

  * { box-sizing: border-box; }

  body {
    margin: 0;
    background: var(--paper);
    color: var(--ink);
    font-family: "Public Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
    -webkit-font-smoothing: antialiased;
    font-variant-numeric: tabular-nums;
  }

  a { color: inherit; }

  h1, h2, h3 { font-family: "Newsreader", Georgia, serif; text-wrap: balance; }

  .masthead {
    border-bottom: 1px solid var(--line);
    padding: 28px clamp(16px, 4vw, 48px) 20px;
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 8px 24px;
  }

  .masthead-title {
    font-size: clamp(28px, 4vw, 38px);
    font-weight: 600;
    font-style: italic;
    letter-spacing: -0.01em;
    margin: 0;
  }

  .masthead-meta {
    font-family: "IBM Plex Mono", ui-monospace, monospace;
    font-size: 12px;
    color: var(--ink-soft);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .masthead-sub {
    width: 100%;
    font-size: 14px;
    color: var(--ink-soft);
    max-width: 62ch;
  }

  main {
    max-width: 1180px;
    margin: 0 auto;
    padding: 28px clamp(16px, 4vw, 48px) 80px;
  }

  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1px;
    background: var(--line);
    border: 1px solid var(--line);
    margin-bottom: 32px;
  }

  .stat {
    background: var(--paper-raised);
    padding: 16px 18px;
  }

  .stat-value {
    font-family: "IBM Plex Mono", ui-monospace, monospace;
    font-size: 26px;
    font-weight: 500;
    line-height: 1.1;
  }

  .stat-label {
    font-size: 12px;
    color: var(--ink-soft);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 4px;
  }

  .stat.event .stat-value { color: var(--accent-event); }
  .stat.signal .stat-value { color: var(--accent-signal); }

  .controls {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px 8px;
    margin-bottom: 24px;
  }

  .search {
    flex: 1 1 220px;
    min-width: 180px;
    font: inherit;
    font-size: 14px;
    padding: 9px 12px;
    border: 1px solid var(--line);
    border-radius: 6px;
    background: var(--paper-raised);
    color: var(--ink);
  }

  .search:focus-visible { outline: 2px solid var(--focus); outline-offset: 1px; }

  .chip {
    font: inherit;
    font-size: 12.5px;
    font-weight: 500;
    padding: 7px 12px;
    border-radius: 999px;
    border: 1px solid var(--line);
    background: var(--paper-raised);
    color: var(--ink-soft);
    cursor: pointer;
    white-space: nowrap;
  }

  .chip:focus-visible { outline: 2px solid var(--focus); outline-offset: 1px; }

  .chip[aria-pressed="true"] {
    color: var(--paper-raised);
    border-color: transparent;
  }

  .chip[aria-pressed="true"].bucket-event { background: var(--accent-event); }
  .chip[aria-pressed="true"].bucket-signal { background: var(--accent-signal); }
  .chip[aria-pressed="true"].bucket-all { background: var(--ink); }

  .chip-group { display: flex; flex-wrap: wrap; gap: 6px; }

  .count {
    font-size: 13px;
    color: var(--ink-faint);
    margin-bottom: 14px;
    font-family: "IBM Plex Mono", ui-monospace, monospace;
  }

  .cards { display: flex; flex-direction: column; gap: 1px; background: var(--line-soft); border: 1px solid var(--line-soft); }

  .card {
    background: var(--paper-raised);
    padding: 16px 18px;
    display: grid;
    grid-template-columns: 3px 1fr auto;
    gap: 0 16px;
    border-left: none;
  }

  .card-bar { border-radius: 2px; }
  .card.bucket-event .card-bar { background: var(--accent-event); }
  .card.bucket-signal .card-bar { background: var(--accent-signal); }

  .card-body { min-width: 0; }

  .card-tags {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }

  .tag {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 2px 8px;
    border-radius: 4px;
  }

  .tag.bucket-event { background: var(--accent-event-soft); color: var(--accent-event); }
  .tag.bucket-signal { background: var(--accent-signal-soft); color: var(--accent-signal); }

  .tag-location { color: var(--ink-faint); font-weight: 500; text-transform: none; letter-spacing: 0; }

  .card-title {
    font-size: 16px;
    font-weight: 600;
    line-height: 1.35;
    margin: 0 0 4px;
    text-decoration: none;
  }

  .card-title:hover { text-decoration: underline; }

  .card-snippet {
    font-size: 13.5px;
    color: var(--ink-soft);
    line-height: 1.5;
    margin: 0 0 6px;
    max-width: 68ch;
  }

  .card-source {
    font-size: 12.5px;
    color: var(--ink-faint);
  }

  .card-date {
    font-family: "IBM Plex Mono", ui-monospace, monospace;
    font-size: 12px;
    color: var(--ink-faint);
    white-space: nowrap;
    text-align: right;
    padding-top: 2px;
  }

  .empty {
    padding: 48px 16px;
    text-align: center;
    color: var(--ink-faint);
    font-size: 14px;
  }

  footer {
    max-width: 1180px;
    margin: 0 auto;
    padding: 0 clamp(16px, 4vw, 48px) 40px;
    font-size: 12px;
    color: var(--ink-faint);
  }

  @media (max-width: 560px) {
    .card { grid-template-columns: 3px 1fr; }
    .card-date { grid-column: 2; text-align: left; padding-top: 6px; }
  }

  @media (prefers-reduced-motion: no-preference) {
    .card { transition: background-color 120ms ease; }
  }
</style>

<header class="masthead">
  <h1 class="masthead-title">Central Florida Wire</h1>
  <div class="masthead-meta">Updated __GENERATED_AT__</div>
  <p class="masthead-sub">Google News scanned daily for Orlando-area events and brand/partnership signals — Danni Adams outreach research.</p>
</header>

<main>
  <div class="stats">
    <div class="stat event">
      <div class="stat-value">__EVENT_COUNT__</div>
      <div class="stat-label">Events tracked</div>
    </div>
    <div class="stat signal">
      <div class="stat-value">__SIGNAL_COUNT__</div>
      <div class="stat-label">Business signals</div>
    </div>
    <div class="stat">
      <div class="stat-value">__CATEGORY_COUNT__</div>
      <div class="stat-label">Categories</div>
    </div>
    <div class="stat">
      <div class="stat-value">__DATE_RANGE__</div>
      <div class="stat-label">Coverage window</div>
    </div>
  </div>

  <div class="controls">
    <input class="search" type="search" id="search" placeholder="Search titles, sources, locations…" aria-label="Search results">
    <div class="chip-group" id="bucket-filters">
      <button class="chip bucket-all" data-bucket="all" aria-pressed="true">All</button>
      <button class="chip bucket-event" data-bucket="event" aria-pressed="false">Events</button>
      <button class="chip bucket-signal" data-bucket="business_signal" aria-pressed="false">Business signals</button>
    </div>
  </div>

  <div class="controls" id="category-filters"></div>

  <div class="count" id="result-count"></div>
  <div id="cards" class="cards"></div>
  <div id="empty" class="empty" style="display:none;">No results match those filters.</div>
</main>

<footer>Sourced from Google News RSS, filtered for Central Florida relevance. Review before acting — location keywords can occasionally match unrelated mentions.</footer>

<script>
  const DATA = __DATA_JSON__;
  const CATEGORY_LABELS = __CATEGORY_LABELS_JSON__;

  const state = { bucket: "all", category: "all", query: "" };

  function categoriesForBucket(bucket) {
    const set = new Set();
    DATA.forEach(function (r) {
      if (bucket === "all" || r.bucket === bucket) set.add(r.category);
    });
    return Array.from(set);
  }

  function renderCategoryChips() {
    const container = document.getElementById("category-filters");
    const cats = categoriesForBucket(state.bucket);
    if (state.category !== "all" && cats.indexOf(state.category) === -1) {
      state.category = "all";
    }
    let html = '<div class="chip-group">';
    html += '<button class="chip" data-category="all" aria-pressed="' + (state.category === "all") + '">All categories</button>';
    cats.forEach(function (c) {
      const label = CATEGORY_LABELS[c] || c;
      html += '<button class="chip" data-category="' + c + '" aria-pressed="' + (state.category === c) + '">' + label + '</button>';
    });
    html += '</div>';
    container.innerHTML = html;
    container.querySelectorAll('[data-category]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        state.category = btn.getAttribute('data-category');
        render();
      });
    });
  }

  function escapeHtml(s) {
    const d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
  }

  function render() {
    document.querySelectorAll('#bucket-filters .chip').forEach(function (btn) {
      btn.setAttribute('aria-pressed', btn.getAttribute('data-bucket') === state.bucket ? 'true' : 'false');
    });
    renderCategoryChips();

    const q = state.query.trim().toLowerCase();
    const filtered = DATA.filter(function (r) {
      if (state.bucket !== 'all' && r.bucket !== state.bucket) return false;
      if (state.category !== 'all' && r.category !== state.category) return false;
      if (q && (r.title + ' ' + r.source + ' ' + r.location_hint).toLowerCase().indexOf(q) === -1) return false;
      return true;
    });

    document.getElementById('result-count').textContent = filtered.length + (filtered.length === 1 ? ' result' : ' results');

    const cardsEl = document.getElementById('cards');
    const emptyEl = document.getElementById('empty');
    if (filtered.length === 0) {
      cardsEl.innerHTML = '';
      cardsEl.style.display = 'none';
      emptyEl.style.display = 'block';
      return;
    }
    emptyEl.style.display = 'none';
    cardsEl.style.display = 'flex';

    cardsEl.innerHTML = filtered.map(function (r) {
      const bucketClass = r.bucket === 'event' ? 'bucket-event' : 'bucket-signal';
      const tagLabel = r.bucket === 'event' ? 'Event' : 'Signal';
      const catLabel = CATEGORY_LABELS[r.category] || r.category;
      const snippet = r.snippet ? '<p class="card-snippet">' + escapeHtml(r.snippet) + '</p>' : '';
      return (
        '<article class="card ' + bucketClass + '">' +
          '<div class="card-bar"></div>' +
          '<div class="card-body">' +
            '<div class="card-tags">' +
              '<span class="tag ' + bucketClass + '">' + tagLabel + '</span>' +
              '<span class="tag-location">' + escapeHtml(catLabel) + ' · ' + escapeHtml(r.location_hint) + '</span>' +
            '</div>' +
            '<a class="card-title" href="' + r.link + '" target="_blank" rel="noopener">' + escapeHtml(r.title) + '</a>' +
            snippet +
            '<div class="card-source">' + escapeHtml(r.source) + '</div>' +
          '</div>' +
          '<div class="card-date">' + escapeHtml(r.display_date) + '</div>' +
        '</article>'
      );
    }).join('');
  }

  document.querySelectorAll('#bucket-filters .chip').forEach(function (btn) {
    btn.addEventListener('click', function () {
      state.bucket = btn.getAttribute('data-bucket');
      state.category = 'all';
      render();
    });
  });

  document.getElementById('search').addEventListener('input', function (e) {
    state.query = e.target.value;
    render();
  });

  render();
</script>
"""


def generate_dashboard_html(csv_path: str = RESEARCH_CSV) -> str:
    rows = load_rows(csv_path)

    data_for_js = [
        {
            "bucket": r["bucket"],
            "category": r["category"],
            "title": r["title"],
            "source": r["source"],
            "location_hint": r["location_hint"],
            "link": r["link"],
            "snippet": r["snippet"],
            "display_date": r["_display_date"],
        }
        for r in rows
    ]

    event_count = sum(1 for r in rows if r["bucket"] == "event")
    signal_count = sum(1 for r in rows if r["bucket"] == "business_signal")
    categories = sorted(set(r["category"] for r in rows))

    dates_found = sorted(set(r.get("date_found", "") for r in rows if r.get("date_found")))
    if dates_found:
        date_range = dates_found[0] if dates_found[0] == dates_found[-1] else f"{dates_found[0]} – {dates_found[-1]}"
    else:
        date_range = "—"

    generated_at = datetime.now(timezone.utc).strftime("%b %-d, %Y")

    page = PAGE_TEMPLATE
    page = page.replace("__DATA_JSON__", json.dumps(data_for_js))
    page = page.replace("__CATEGORY_LABELS_JSON__", json.dumps(CATEGORY_LABELS))
    page = page.replace("__EVENT_COUNT__", str(event_count))
    page = page.replace("__SIGNAL_COUNT__", str(signal_count))
    page = page.replace("__CATEGORY_COUNT__", str(len(categories)))
    page = page.replace("__DATE_RANGE__", html.escape(date_range))
    page = page.replace("__GENERATED_AT__", html.escape(generated_at))
    return page


if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT
    html_content = generate_dashboard_html()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Wrote {out_path}")
