# Deploy Guide

This app is a single-file PWA (`index.html`) backed by Firebase Firestore.  
No build step required — just serve the files over HTTPS.

---

## Files

```
index.html             — entire app (HTML + CSS + JS)
manifest.json          — PWA manifest
logo.svg               — browser-tab / loading icon
apple-touch-icon.png   — iPhone home-screen icon (180×180) — must be uploaded!
sw.js                  — offline support (keeps the app usable without internet)
icons/
  icon-192.png         — PWA icon (192×192)
  icon-512.png         — PWA icon (512×512)
```

> After changing the icon on iPhone: delete the old home-screen shortcut, open the site in Safari, then Share → Add to Home Screen. iOS only reads the icon when the shortcut is created.

> **Icons** are included (generated from `logo.svg`). Upload all of the files above —  
> if `apple-touch-icon.png` is missing on the server, iPhone shows a page screenshot instead of the icon.

---

## Option 1 — GitHub Pages (free, recommended)

1. Push the files to a GitHub repo (e.g. `cheungcm/budget`).
2. Go to **Settings → Pages → Source** → select `main` branch, `/ (root)`.
3. Your app is live at `https://cheungcm.github.io/budget/`.

```bash
git init
git add index.html manifest.json logo.svg apple-touch-icon.png sw.js icons/
git commit -m "init"
git remote add origin https://github.com/cheungcm/budget.git
git push -u origin main
```

---

## Option 2 — Netlify (drag & drop)

1. Go to [netlify.com](https://netlify.com) → **Add new site → Deploy manually**.
2. Drag the `files/` folder onto the drop zone.
3. Done — Netlify gives you a `*.netlify.app` URL instantly.

---

## Option 3 — Firebase Hosting (same project as Firestore)

```bash
npm install -g firebase-tools
firebase login
firebase init hosting   # public dir = . (current folder), SPA = no
firebase deploy
```

---

## Firebase Setup

1. Go to [console.firebase.google.com](https://console.firebase.google.com).
2. Create a project → add a **Web App** → copy the config JSON.
3. **Firestore** → Create database → **Start in test mode**.
4. Open the app → **Settings → 連接 Firebase** → paste the config JSON.

### Firestore Security Rules (production)

Replace test-mode rules with:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /ledgers/{ledgerId}/{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

Enable **Email/Password** authentication in Firebase Auth if you want login-gating.

---

## PWA Install (iOS)

1. Open the app URL in Safari.
2. Tap **Share → Add to Home Screen**.
3. The app runs fullscreen with offline support from the local cache.

---

## Gemini AI Scan

1. Get a free API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
2. Open the app → **Settings** → paste the key into the Gemini API Key field.
3. Tap the 📷 camera button in the tab bar to scan receipts.

---

## Daily stock prices (GitHub Actions)

Investment holdings on the **Balance** tab are valued at each ticker's last closing price.
Browsers can't call Yahoo Finance directly, so a small scheduled job does it and saves the
prices into Firestore (`ledgers/shared-ledger/meta/assets` → `prices`), which every device reads.

Files: `.github/workflows/update-prices.yml` and `scripts/update_prices.py` (Python, no packages).

1. Push both files with the rest of the app (note the hidden `.github` folder):
   ```bash
   git add .github scripts
   git commit -m "Daily stock prices"
   git push
   ```
2. On GitHub: **Settings → Secrets and variables → Actions → New repository secret**
   - `FIREBASE_PROJECT_ID` — the `projectId` from your Firebase config
   - `FIREBASE_API_KEY` — the `apiKey` from your Firebase config (optional while Firestore is in test mode)
3. **Actions → Update stock prices → Run workflow** to test it once. The log lists each ticker and its close.

It then runs automatically Monday–Friday after the ASX/HK close (08:30 UTC) and after the US close (22:15 UTC).
Only the `prices` fields are written; nobody's assets are changed.

> If you switch Firestore to the production rules above (`request.auth != null`), this job can no
> longer write without signing in — keep test-mode rules for `ledgers/shared-ledger/meta/assets`
> or tell Claude to add a service-account login to the script.
