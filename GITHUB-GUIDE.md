# 🐙 GitHub Guide — Put Storyteller CYOP on the Internet (Free)

This gets your app **live on a public link** anyone can open, makes it
**installable** on phones (📲 Install button works), and **unlocks the AI
Editor** (the in-chat preview blocks outside APIs — a real website doesn't).
Time: ~10 minutes. Cost: $0.

---

## Part 1 — Create the repo on github.com (2 min)

1. Go to **<https://github.com>** and sign in as **Coder386Galaxy**
   (create the account first if you haven't).
2. Click the **+** in the top-right corner → **New repository**.
3. Fill it in exactly like this:
   - **Repository name:** `storyteller`
   - **Visibility:** ✅ **Public** (required for free GitHub Pages)
   - ❌ Do **NOT** check "Add a README" (we already have commits — an
     initialized repo would conflict)
4. Click **Create repository**. Leave the page open — you'll come back for
   the token in a second.

## Part 2 — Create a Personal Access Token (PAT) (3 min)

A PAT is a password that lets a computer push code to your repo.

1. On GitHub, click your **profile picture** (top right) → **Settings**.
2. In the left sidebar, scroll all the way down → **Developer settings**.
3. **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
4. Set it up:
   - **Token name:** `storyteller-push`
   - **Expiration:** 90 days (or longer)
   - **Repository access:** **Only select repositories** → pick `storyteller`
   - **Permissions → Repository permissions → Contents:** **Read and write**
   - Everything else: leave as "No access"
5. Click **Generate token**.
6. **Copy the token NOW** (starts with `github_pat_…`). GitHub only shows it
   **once**.

> 🔒 **Treat the token like a password.** Don't post it anywhere public.
> If it ever leaks, revoke it in the same page and make a new one.

## Part 3 — Get the code onto GitHub

### Option A: have me push it (easiest)

Paste the token into our chat and say "push". I'll run:

```bash
cd /home/user/story-maker
git remote add origin https://github.com/Coder386Galaxy/storyteller.git
git push https://<YOUR_TOKEN>@github.com/Coder386Galaxy/storyteller.git main
```

(The token is used for the push only — it never gets saved into the project.)

### Option B: do it yourself

1. Download the `story-maker` folder from this workspace to your computer.
2. If you don't have git: install it from <https://git-scm.com> (Windows/Mac).
3. Open a terminal in the folder and run:

```bash
git remote add origin https://github.com/Coder386Galaxy/storyteller.git
git push -u origin main
```

4. When asked for a password: **paste the PAT** (not your GitHub password —
   GitHub doesn't accept passwords for git anymore).

✅ **Check:** refresh your repo page — you should see `index.html`,
`APPSTORE-GUIDE.md`, the `ios/` folder, etc.

## Part 4 — Turn on GitHub Pages (the actual website) (1 min)

1. In your repo, go to **Settings** → left sidebar **Pages**.
2. Under **Build and deployment**:
   - **Source:** Deploy from a branch
   - **Branch:** `main` and **/ (root)** ← make sure it's root, not /docs
3. Click **Save**.
4. Wait 1–2 minutes, refresh the page. You'll see:

   > Your site is live at **https://coder386galaxy.github.io/storyteller/**

🎉 That URL is your published app. Share it anywhere. On a phone, open it in
Safari/Chrome and use **Add to Home Screen** (or tap the 📲 Install button in
the app header) — it installs like a real app, icon and all.

## Part 5 — After it's live

**Updating the app:** change the code (in our chat, or yourself) → commit →
`git push`. GitHub Pages re-deploys automatically in ~1 minute.

**Things that start working on the real site (but not in our preview):**
- 🤖 **AI Editor** — the chat can reach api.openai.com, so add your key in ⚙
  Settings and it works fully.
- 💳 **Stripe checkout** — opens properly; set each Payment Link's
  "After payment → redirect" to
  `https://coder386galaxy.github.io/storyteller/index.html` so Pro unlocks
  automatically.
- 📲 **Install** — the browser's install prompt fires (service worker +
  manifest are served over HTTPS).

**For the App Store later:** your privacy policy URL is already hosted at
`https://coder386galaxy.github.io/storyteller/privacy-policy.html` — paste
that into App Store Connect.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Authentication failed` on push | You pasted your GitHub password — use the **PAT** instead. Or the token expired / lacks Contents: Read and write. |
| `Repository not found` | Repo name/username typo in the URL, or repo is Private. Free Pages needs Public. |
| Pages 404 | Settings → Pages: did you pick **main** + **/ (root)** and Save? Wait 2 min. Also check the repo is Public. |
| Site shows old version | Hard-refresh (Ctrl+Shift+R). Pages caches briefly. |
| `Updates were rejected` on push | Someone/something pushed first — run `git pull --rebuild`… actually: `git pull origin main --allow-unrelated-histories` then push again. |
| Token lost before saving | No problem: revoke it in Developer settings and generate a new one. |

## Security habits

- PATs can push code — never paste one into an issue, comment, or screenshot.
- Expired token? Just make a new one (Part 2) — takes 2 minutes.
- Your app itself is safe to make public: everything runs in the visitor's
  browser, and there are no secrets in the code (your OpenAI key lives only
  in each user's own browser storage).
