# 📖 Storyteller

**Write your own choose-your-own-adventure stories — entirely in the browser.**

Storyteller is a zero-backend, single-page CYOA builder. Write passages, add branching choices (A/B/C/D), end scenes in 💀 death or 🏆 victory, and publish into a personal library grouped by series. Paste an existing story and AI finalizes it into a playable adventure — or build from scratch.

## ✨ Features

- **🔀 Build tab** — passage-by-passage editor with Continue (dialogue/narration) and branching choices. Auto-saves as you type.
- **✨ AI Convert** — paste prose with or without inline `A)`/`B.`/`- bullet` choices; AI parses scenes, chains narration with Continue →, wires your choices to new passages, plants light side branches and death/victory endings.
- **▶ Play** — built-in test player with restart tracking and honest first-try win rates.
- **📚 Library** — published stories grouped by series (a story can belong to multiple series at once). Real play counts — no fake numbers.
- **🤖 AI age rating** — every story gets rated ST-1 (all ages) through ST-5 (18+). School-friendly badge for classroom-safe stories.
- **🔗 Share codes** — base64url-encoded story codes you can send to friends; they paste into the import box and play. URL support (`?story=...`) opens the story automatically.
- **🔒 Private by design** — all data stays in your browser's `localStorage`. No account, no server.
- **👑 Pro tier** (demo Stripe test checkout) — unlocks photos, video embeds (YouTube/Vimeo/mp4), and sound effects per passage.

## 🚀 Run it locally

```bash
cd story-maker
python3 -m http.server 8080
# then open http://localhost:8080
```

Or just double-click `index.html` — it works from `file://` too.

## 🧭 Controls

- **Ctrl/Cmd + Enter** in the writing box → auto-create the next Continue scene
- **Esc** → close the topmost open modal
- **Top-right 👤 Age N** → change your birthday at any time

## 📁 Files

- `index.html` — the entire app (HTML, CSS, JS in one file)
- `js/data.js` — (optional) seed/example data
- `server.py` — tiny local dev server that disables caching so changes show up immediately

## License

Personal project — use freely, fork, remix.
