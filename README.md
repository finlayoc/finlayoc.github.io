# Finlay O'Connor — personal site

| File | What it is |
|---|---|
| `index.html` | The whole site (design, content, and the code that draws the feeds) |
| `watchlist.txt` | Bring a Trailer listing URLs to show in **The watchlist** |
| `reading.txt` | Article links + your note, for **The clippings file** |
| `scripts/update_feeds.py` | Reads both lists, fetches current bids / headlines, writes `data/*.json` |
| `.github/workflows/update-feeds.yml` | Runs that script on GitHub every 2 hours, and whenever you edit a list |

## Day to day

- **Follow a new auction:** paste its BaT URL as a new line in `watchlist.txt`.
- **Share an article:** add `URL | why it caught your eye` at the top of `reading.txt`
  (add `| Headline` at the end for paywalled sites).

Edit either file right on github.com; the site refreshes itself within a few minutes.

## Hosting

The live feeds need a host that runs the update job, which Canva sites can't do.
The plan is GitHub Pages (free), with a custom domain pointed at it if you buy one.
Before deploying, `index.html` needs the standard `<!doctype html>` wrapper added.
