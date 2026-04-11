# Pinellas Ice Co — Launch Instructions
## Everything done from your iPad. Free. 25 minutes.

---

## PART 1 — Use the Tool Right Now (5 minutes)

You don't need to do anything else to start using the tool today.

1. Download **prospecting_tool.html** from Claude to your Files app
2. Rename it to **index.html** (tap and hold → Rename)
3. Go to **app.netlify.com/drop** in Safari
4. Tap **browse to upload** → select index.html
5. Netlify gives you a URL — **bookmark it immediately**

Your tool is live. Open it on your iPad whenever you want.
Your call log saves in Safari and persists across sessions.

> Your current Netlify site is: https://thunderous-zuccutto-27163f.netlify.app
> Just re-upload the new index.html to update it.

---

## PART 2 — Set Up Auto-Updates (20 minutes)

This makes the tool update itself every Monday with fresh FL inspection data.
No laptop. No terminal. Just Safari.

### Step 1 — Create a GitHub account

1. Go to **github.com** in Safari → Sign Up
2. Use your email, create a password, pick a username (e.g. `pinellasice`)
3. Verify your email when they send the confirmation link

### Step 2 — Create the repository

1. After logging in, tap the **+** button (top right) → **New repository**
2. Name it exactly: `pinellasice`
3. Make sure **Public** is selected (required for free GitHub Pages)
4. Tap **Create repository**

Leave this tab open.

### Step 3 — Upload your files

You have 5 files to upload. GitHub lets you upload them from your iPad.

On your new empty repository page, tap **uploading an existing file**.

**Upload these files one batch at a time:**

**Batch 1** — drag or select all of these:
- `build.py`
- `download_data.py`
- `gitignore.txt`
- `rebuild.yml`

After selecting, scroll down and tap **Commit changes**.

**Batch 2** — the docs folder (this is the tricky part on iPad):
1. Tap **Add file** → **Upload files**
2. Select `index.html` (your prospecting_tool.html, renamed)
3. **Before committing:** look at the filename field at the top of the page
4. Add `docs/` in front of the filename so it reads `docs/index.html`
5. GitHub creates the folder automatically when you type the slash
6. Tap **Commit changes**

**Batch 3** — the workflow folder:
1. Tap **Add file** → **Upload files**  
2. Select `rebuild.yml` again
3. Change the path to `.github/workflows/rebuild.yml`
4. Tap **Commit changes**

> **Note on gitignore.txt:** After uploading, tap the file in GitHub → tap the pencil (Edit) → rename it to `.gitignore` → Commit. The dot at the start is required.

### Step 4 — Enable GitHub Pages

1. In your repository, tap **Settings** (top navigation)
2. In the left sidebar tap **Pages**
3. Under **Branch**, select `main` and folder `/docs`
4. Tap **Save**

Wait 2-3 minutes. Your permanent URL will appear:
`https://yourusername.github.io/pinellasice`

**Bookmark this on your iPad. This is your tool URL forever.**

### Step 5 — Test the auto-update

1. Tap the **Actions** tab in your repository
2. Tap **Rebuild Prospect Tool** in the left list
3. Tap **Run workflow** → **Run workflow** (the green button)
4. Watch it run — green checkmark = success (takes 3-5 minutes)
5. Reload your bookmark — fresh data loaded

If it shows a red X, see Troubleshooting below.

---

## How It Works After Setup

**Every Monday at 7am**, GitHub automatically:
1. Downloads the latest FL DBPR inspection data for District 3 (your counties)
2. Downloads the active license extract (phones + seat counts)
3. Runs the scoring pipeline
4. Updates your URL with fresh prospects

You do nothing. It just stays current.

**To trigger manually** (e.g. after state posts new data):
GitHub → Actions tab → Rebuild Prospect Tool → Run workflow

---

## Your Call Log

Everything you log stays in Safari's storage on your iPad.
It persists across tool updates automatically.

**To back up your log:**
Tool → Data tab → Export Pipeline to CSV → saves to Files

**If you clear Safari history:** your log will be lost. Export first.

---

## Adding Phone Numbers

When you find a number the tool doesn't have:
1. Open the prospect → tap the card
2. Go to **Data** tab → **Add a Phone Number**  
3. Enter the License ID (shown on every card) + the number
4. Tap **Save** — persists through every future rebuild

---

## Files Reference

| File | Purpose |
|------|---------|
| `index.html` | The tool itself (upload to Netlify or docs/ folder) |
| `build.py` | Scoring pipeline — runs on GitHub's servers |
| `download_data.py` | Downloads FL data automatically |
| `rebuild.yml` | Weekly schedule — goes in `.github/workflows/` |
| `gitignore.txt` | Rename to `.gitignore` — keeps large data files out of git |

---

## Troubleshooting

**Action shows red X:**
- Click the failed run → click the failed step → read the error
- Most common: a URL changed on FL DBPR's site
- Come back to Claude with the error message — quick fix

**Tool shows blank / no cards:**
- Hard refresh: hold the reload button → "Reload Without Content Blockers"
- Check that you're on the GitHub Pages URL, not opening a local file

**Map doesn't load:**
- The map requires internet (loads OpenStreetMap tiles from CDN)
- Everything else works offline

**Netlify vs GitHub Pages:**
- Netlify: simpler, instant, manual re-upload to refresh data
- GitHub Pages: automatic weekly updates, permanent URL
- Use Netlify today, set up GitHub Pages this week

---

## Costs

Everything used is **completely free**:
- GitHub: free (public repo, Actions, Pages)
- Netlify: free (drop deployments)
- FL DBPR data: free (public records)
- OpenStreetMap: free (open source)
- Lexend font: free (Google Fonts)

The only thing that costs money is if you later add Google Places API
for phone enrichment — but that has a $200/month free credit which
covers thousands of lookups, more than enough for your territory.
