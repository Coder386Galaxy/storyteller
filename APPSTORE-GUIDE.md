# 🍎 Publishing Storyteller CYOP to the Apple App Store

Everything needed to submit is in this folder. The iOS app is a native SwiftUI
shell (`StorytellerCYOP.xcodeproj`) around your web app (bundled in `www/`).

---

## ⚠️ Read first: the one thing that WILL get you rejected

**Apple Guideline 3.1.1** — digital goods and subscriptions sold inside an iOS
app **must use Apple In-App Purchase**. Your Storyteller Pro subscription uses
Stripe links, which Apple rejects (this is the rule that got Netflix/Spotify
deals in the news). I already handled v1 for you:

- The iOS shell injects `window.__CYOP_IOS__ = true` into the app.
- `startCheckout()` detects it and shows a friendly "not available in the iOS
  app" toast instead of opening Stripe. **No rejection risk.**

Your options going forward (pick one, in this order of effort):

1. **Ship v1 free** (recommended first release) — Pro simply can't be bought
   in the app; users subscribe on the web version. Totally fine to say in the
   review notes.
2. **Add StoreKit 2 / RevenueCat** — real IAP auto-renewable subscriptions.
   Requires App Store Connect setup + code. RevenueCat makes this easy later.

Do **not** link out to Stripe from inside the iOS app — instant rejection.

---

## What's in this folder

```
ios/
├── StorytellerCYOP.xcodeproj/     ← open this in Xcode
└── StorytellerCYOP/
    ├── App.swift                  ← SwiftUI + WKWebView wrapper
    ├── Info.plist                 ← name, orientation, launch screen, version
    ├── Assets.xcassets/           ← app icon (1024px) + accent color
    └── www/                       ← your app (index.html + icons)
```

> **Whenever you update the web app**, re-copy it into the shell:
> `cp index.html icon-*.png ios/StorytellerCYOP/www/`

---

## Prerequisites (non-negotiable Apple requirements)

1. **A Mac** with Xcode 15+ (free on the Mac App Store).
2. **Apple Developer Program membership** — $99/year at
   <https://developer.apple.com/programs>. You cannot ship without it.
3. An iPhone or the iOS Simulator for testing.

## Build & test (10 minutes)

1. Double-click `ios/StorytellerCYOP.xcodeproj` (opens in Xcode).
2. Click the project → **Signing & Capabilities** → check
   **Automatically manage signing** → select your **Team**
   (your Apple ID, enrolled in the Developer Program).
3. Optional: change `PRODUCT_BUNDLE_IDENTIFIER` if you don't want
   `com.coder386galaxy.storytellercyop` (must be unique on the App Store —
   the default works unless taken).
4. Pick an iPhone simulator → ▶ Run. Play with the app: build a story,
   publish, read it back. Stories persist between launches (localStorage).
5. **Note:** in the simulator, the 🤖 AI Editor works (network allowed),
   Stripe buttons politely decline (by design), and the 📲 Install button is
   hidden (PWA install doesn't apply to the native shell).

## Submit to the App Store

1. In Xcode: **Product → Archive** (choose "Any iOS Device (arm64)").
2. **Distribute App → App Store Connect → Upload**.
3. Go to <https://appstoreconnect.apple.com> → My Apps → **+** →
   New App → name **Storyteller CYOP**, primary language, bundle ID
   (matches step 3 above), SKU `storytellercyop`.
4. Fill in the metadata below, add screenshots, submit for review.

### Screenshots you need

In the simulator, take screenshots (⌘S) at these sizes and upload:

| Device in simulator | Screenshot size | Required? |
|---|---|---|
| iPhone 15 Pro Max (6.7") | 1290×2796 | **Yes** (need 2–10) |
| iPhone 8 Plus (5.5") | 1242×2208 | only if you support older devices |

Good screenshot ideas: the home screen, a story mid-play with choices, the
AI Convert finalize moment, the library grid.

### Metadata (copy-paste ready)

- **Name:** Storyteller CYOP
- **Subtitle:** Build your own path stories
- **Category:** Books (or Games → Adventure)
- **Description:**

  > Build branching choose-your-own-path stories right in your browser —
  > and in this app, everything stays on your device.
  >
  > WRITE: Type scenes one by one. Add A/B/C choices, lead them to victory
  > or death endings, and test-play instantly. Or paste a rough draft and
  > let AI turn it into a playable adventure.
  >
  > AI EDITOR: After finalizing, chat with the AI to reshape your story —
  > "add a scene where you find a key," "make the ending a victory," and
  > it edits the passages for you. (Bring your own OpenAI API key.)
  >
  > SHARE: Publish to your library, share any adventure as a code, and
  > play stories your friends made. Leave a thumbs up, thumbs down, or a
  > comment on adventures you read.
  >
  > Every story is age-rated automatically, mature stories require age
  > verification, and readers verify with a quick ID scan before playing.

- **Keywords:** `cyoa,interactive fiction,story games,choose your own,adventure,writing,stories,game maker,text game`
- **Copyright:** © 2026 Coder386Galaxy

### Age rating questionnaire (answer like this → gets 9+)

| Question | Answer |
|---|---|
| Cartoon/fantasy violence | None / Mild |
| Realistic violence | None |
| Mature/suggestive themes | None |
| Profanity | None |
| Horror/fear themes | Mild (death endings exist) |
| Gambling | None |
| Unrestricted web access | **No** (content is user-generated in-app; no browser) |

Your app carries user-generated stories — Apple will also ask about UGC:
you have **age verification, mature-content gates, and a report path
(comments/votes are local to each device)**, which satisfies 1.2 safely.

### App Privacy (nutrition labels)

Answer: **No data collected, no data shared.** Everything (stories, age,
votes, comments, API key) stays in the device's localStorage. The only
network calls are to api.openai.com *if the user adds their own key* (a
user-initiated, user-credentialed service — declare under "Contact Info →
Other" only if Apple's reviewer asks).

### Review notes (paste into the "Notes" box)

> This is a story-builder app. All content is created and stored locally on
> the device. The ID-scan and age gates are simulated educational-style
> checks performed on-device; no government ID is collected or transmitted.
> Subscriptions are not sold inside the app.

---

## Pre-flight checklist

- [ ] Apple Developer Program membership active
- [ ] App opens in Xcode, signs with your team, runs in simulator
- [ ] Played through a story on the simulator without crashes
- [ ] Screenshots taken (6.7" minimum)
- [ ] Privacy policy hosted (use `privacy-policy.html` in this repo — GitHub
      Pages is fine) and URL pasted into App Store Connect
- [ ] Age rating questionnaire answered (table above)
- [ ] App Privacy answered (no data collected)
- [ ] Review notes pasted
- [ ] Archive → Upload → Submit for Review

Typical review time: 24–48 hours. Good luck! 🚀
