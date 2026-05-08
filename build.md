# Build Instructions for Claude

You are building a new app using this template. Follow these steps exactly, in order.

---

## Step 1 — Scaffold the frontend

```bash
npx create-expo-app@latest frontend --template blank
cd frontend && npx expo install expo-auth-session expo-web-browser expo-device expo-secure-store expo-application react-native-web react-dom @expo/metro-runtime
```

## Step 2 — Copy template files into the scaffold

Copy these two files from the template root into `frontend/`:

- `api.js` → `frontend/api.js`
- `app.json` → update `frontend/app.json`: set `name`, `slug`, and `scheme` to match the app name

## Step 3 — First commit (scaffold only, no app logic yet)

```bash
git add frontend/
git commit -m "scaffold: expo app initialized with auth template"
```

## Step 4 — Build the app

Now build the actual app UI in `frontend/App.js`.

Rules:
- Import `{ setGoogleToken, clearAuth, api }` from `./api` — do not rewrite auth logic
- Gate everything behind Google Sign-In (show login screen if no user)
- Store all data via `api.post('', { action, ...payload })` and `api.get()`
- The backend stores data as JSON at `gs://bucket/{app_name}/{user_email}/data.json`
- Design the data shape to fit in a single JSON object (flat is fine for simple apps)
- Keep it simple — one screen is enough unless the app clearly needs more

## Step 5 — Second commit (app logic)

```bash
git add frontend/App.js
git commit -m "feat: [app name] UI"
```

## Step 6 — If the backend needs custom logic

Edit `backend/main.py` only if the default GET/POST/PUT/DELETE on `data.json` isn't enough.
The todo app is a good example: it added action-based mutations (`add`, `toggle`, `delete`).

```bash
git add backend/
git commit -m "feat: [app name] backend logic"
```

---

## What you get out of the box (do not reimplement)

- Google Sign-In (ID token, verified server-side)
- Per-user isolated storage in GCS
- CORS handled
- Only `matanwis@gmail.com` can access by default (`ALLOWED_USERS` in `.env`)
- `make setup` → provisions GCP infra
- `make deploy` → deploys Cloud Function
- `make dev` → starts Expo with tunnel (phone + laptop)
