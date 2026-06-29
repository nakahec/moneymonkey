# Splits — Deploy Guide

## Files needed
```
index.html
manifest.json
icon.svg
```

---

## Step 1 — GitHub Repository

1. Go to **github.com** → sign in → click **New repository**
2. Name it (e.g. `splits`) → set to **Public** → click **Create repository**
3. Upload files:
   - Click **Add file → Upload files**
   - Drag in `index.html`, `manifest.json`, `icon.svg`
   - Click **Commit changes**

---

## Step 2 — GitHub Pages

1. In your repo → **Settings** tab
2. Left sidebar → **Pages**
3. Under **Source** → select **Deploy from a branch**
4. Branch: **main** → Folder: **/ (root)** → **Save**
5. Wait ~1 minute → your URL appears:
   `https://YOUR_USERNAME.github.io/splits/`

---

## Step 3 — Firebase Setup

### 3a. Create Firebase Project
1. Go to **console.firebase.google.com**
2. Click **Add project** → name it → click through setup
3. Disable Google Analytics (optional) → **Create project**

### 3b. Create Firestore Database
1. Left sidebar → **Firestore Database** → **Create database**
2. Choose **Start in test mode** → select a region → **Done**
3. Test mode allows all reads/writes for 30 days (fine for personal use)

### 3c. Register Web App
1. Project overview → click **</>** (Web) icon
2. App nickname: `splits` → **Register app**
3. Copy the `firebaseConfig` object — looks like:
```json
{
  "apiKey": "AIza...",
  "authDomain": "your-project.firebaseapp.com",
  "projectId": "your-project-id",
  "storageBucket": "your-project.appspot.com",
  "messagingSenderId": "123456789",
  "appId": "1:123:web:abc123"
}
```

### 3d. Connect in the App
1. Open your GitHub Pages URL
2. Tap **Settings** tab → **Connect Firebase**
3. Paste the JSON config → tap **Connect**
4. Green "Live" badge = connected ✓

---

## Step 4 — Install as iPhone App (PWA)

1. Open your GitHub Pages URL in **Safari** (must be Safari)
2. Tap the **Share** button (box with arrow)
3. Scroll down → **Add to Home Screen**
4. Tap **Add**
5. App icon appears on your home screen

---

## Step 5 — Exchange Rates

1. Settings → **Update Now** under Exchange Rates
2. Downloads 2 years of daily rates from Yahoo Finance via proxy
3. Rates are stored locally — historical transactions are never recalculated

---

## Firestore Security Rules (after testing)

Once you're ready to lock down your database, replace test mode rules:

1. Firestore → **Rules** tab → paste:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /ledgers/{ledgerId}/transactions/{txId} {
      allow read, write: if true;
    }
  }
}
```

For proper auth, add Firebase Authentication and restrict by user.

---

## Update the App

To update after changes to `index.html`:
1. Go to your GitHub repo
2. Click `index.html` → pencil icon (edit) → or upload new version
3. GitHub Pages auto-deploys in ~30 seconds
4. Refresh Safari → the PWA gets the update on next load

---

## Data Architecture Summary

```
localStorage (device-only, fast)
├── Firebase config
├── People (with UUIDs)
├── Categories (with UUIDs)
├── Ledger list
└── FX rates (date → currency → rate)

Firestore (synced, multi-device)
└── /ledgers/{ledgerId}/transactions/{txId}
    ├── type: "expense" | "transfer"
    ├── itemName, categoryId, paidByPersonId, usedByPersonIds
    ├── currency, amount, fxRate, baseAmount (immutable after save)
    ├── date, remark, status
    └── recurringRuleId (optional)
```

**Key design principle:** Transaction amounts are stored with the FX rate at time of creation. Updating exchange rates never modifies historical data.
