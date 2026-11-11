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
git add index.html manifest.json logo.svg apple-touch-icon.png icons/
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
