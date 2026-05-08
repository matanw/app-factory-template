# App Factory Template

A template for deploying personal apps in ~5 minutes.
Each app gets its own isolated GCP bucket, Cloud Function, and service account.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Expo (React Native + Web) |
| Backend | Python Cloud Function (GCP gen2) |
| Storage | Google Cloud Storage (one JSON file per app) |
| Auth | Shared secret (`MASTER_KEY`) baked into bundle |
| Infra | Terraform |

---

## First time on a new machine

```bash
brew install --cask google-cloud-sdk terraform
make login
```

---

## Starting a new app (5 minutes)

```bash
gh repo create my-app --template matanw/app-factory-template
cd my-app
make init      # generates MASTER_KEY, writes .env — save the key shown!
make setup     # provisions GCP: bucket, service account, IAM
make deploy    # deploys the Cloud Function
make dev       # Expo tunnel — scan QR in Expo Go or open URL in browser
```

`make init` prints your access code **once**. Save it — it's your app's password.

---

## Building the UI (tell Claude this)

```
Build me a [describe your app].

Instructions:
1. Scaffold the frontend:
   npx create-expo-app@latest frontend --template blank
   cd frontend && npx expo install expo-secure-store react-native-web react-dom @expo/metro-runtime

2. Create frontend/api.js:

const API_URL    = process.env.EXPO_PUBLIC_API_URL    || '';
const MASTER_KEY = process.env.EXPO_PUBLIC_MASTER_KEY || '';

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${MASTER_KEY}` },
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || `HTTP ${res.status}`);
  return body;
}

export const api = {
  get:  (path = '')       => request(path),
  post: (path = '', data) => request(path, { method: 'POST', body: JSON.stringify(data) }),
  put:  (path = '', data) => request(path, { method: 'PUT',  body: JSON.stringify(data) }),
  del:  (path = '')       => request(path, { method: 'DELETE' }),
};

3. git add frontend/ && git commit -m "scaffold: expo app initialized"

4. Build the app UI in frontend/App.js. Rules:
   - Import { api } from './api' — never rewrite auth or fetch
   - No login screen — auth is invisible (MASTER_KEY bundled via EXPO_PUBLIC_MASTER_KEY)
   - Store all data via api.post/put — backend stores one JSON file per app
   - Keep it simple: one screen unless the app clearly needs more

5. If the backend needs custom mutations (e.g. add/delete items in an array),
   override backend/main.py. See the todo app for a working example.

6. git add . && git commit -m "feat: [app name]"
```

---

## How auth works

`make init` generates a random `MASTER_KEY` → saved to `.env` (gitignored).  
`make deploy` injects it into the Cloud Function.  
`make dev` bakes it into the Expo bundle via `EXPO_PUBLIC_MASTER_KEY`.  
Every API call sends `Authorization: Bearer <key>` — the function rejects anything else.

**Never commit `.env` or `frontend/.env.local`** — both are gitignored.

---

## Commands

| Command | What it does |
|---|---|
| `make init` | Generates MASTER_KEY, writes `.env` |
| `make login` | Authenticates gcloud (once per machine) |
| `make setup` | Provisions GCP infrastructure via Terraform |
| `make deploy` | Deploys the Cloud Function |
| `make dev` | Starts Expo dev server with tunnel |
| `make destroy` | Tears down ALL GCP resources for this app |

---

## Deleting an app

```bash
make destroy
gh repo delete my-app
```

Each app is fully isolated — deleting one never affects others.
