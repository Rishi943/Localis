# Feature Research

**Domain:** Local-first AI assistant — new feature milestone (5 features)
**Researched:** 2026-03-14
**Confidence:** MEDIUM (table stakes and anti-features from ecosystem research; differentiators cross-checked against LM Studio, Open WebUI, Firefly III, competitor LinkedIn AI tools)

---

## Overview

This document covers the feature landscape for five new capabilities being added to Localis. Each section follows the same structure: table stakes, differentiators, anti-features. A cross-feature dependency map and prioritization matrix follow at the end.

Because Localis is privacy-first and local-first, "anti-feature" includes anything that introduces unexpected network egress, uploads data to third parties, or undermines user control.

---

## Feature 1: LAB — LLM Parameter Playground

### Table Stakes

Features users expect based on comparable tools (LM Studio, Open WebUI, Ollama Modelfile system).

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Temperature slider (0.0–2.0) | Every local LLM UI exposes this; users arriving from LM Studio expect it | LOW | Default 0.7; show label "Creative / Precise" |
| Top-P slider (0.0–1.0) | Standard alongside temperature; widely documented in prompt engineering guides | LOW | Default 0.9; clarify it competes with Min-P |
| Repeat penalty control | Prevents repetition loops — users who hit this bug will look for the knob | LOW | llama-cpp-python exposes `repeat_penalty` directly |
| Context size (n_ctx) selector | Power users know context = memory; students want to stretch it | MEDIUM | Requires model reload; warn user that change triggers reload |
| GPU layers (n_gpu_layers) selector | Core to getting GPU acceleration; users configuring their first local setup need this | MEDIUM | Changing layers also requires model reload — batch with context change |
| Persist settings per model | Users expect settings to survive page refresh | LOW | Store in DB `app_settings` keyed by model name |
| Reset to defaults button | Any experiment-gone-wrong needs a bail-out | LOW | Restore to hardcoded sane defaults, not just empty |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Named preset system (A/B defaults) | Students can save "creative writing" vs "factual Q&A" presets and switch with one click — no other local tool does this with named persistence | MEDIUM | Store as named rows in DB; show preset pill selector in LAB |
| Live parameter effect preview | Show a fixed benchmark prompt response side-by-side at two temperature settings — makes parameters intuitive for beginners | HIGH | Requires two concurrent inference calls; need to queue against MODEL_LOCK carefully |
| Min-P exposure alongside Top-P | Min-P is now the recommended sampler for open-source models (2026 guidance) but most UIs still only expose Top-P | LOW | llama-cpp-python supports `min_p`; add with clear tooltip explaining the difference |
| Parameter diff annotation | When a preset differs from current settings, show which knobs are changed — makes switching presets transparent | LOW | Pure UI diff logic |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Cloud benchmark comparison (send prompt to GPT-4 as reference) | "How does my local model compare?" | Violates privacy-first principle; sends user data externally | Show local perplexity estimate or static reference scores from public benchmarks |
| Auto-tuning (app picks params based on task) | Sounds smart | Black-box behaviour destroys the learning value of LAB; students need to understand what changed | Offer suggested presets per task type; user still confirms |
| Continuous auto-apply on slider drag | "Real-time" feedback | Each param change touching context/GPU triggers expensive model reload; real-time isn't meaningful here | Apply on explicit "Apply" button or only apply soft params (temp/top-p) on-the-fly, hard params (n_ctx, n_gpu_layers) on commit |

---

## Feature 2: News RSS Feed

### Table Stakes

Based on established RSS reader expectations (Feedly, NetNewsWire, Inoreader patterns).

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Fetch and display posts from r/LocalLLaMA RSS | This is the stated default source; must work on first launch without user config | LOW | Reddit exposes RSS at `https://www.reddit.com/r/localllama/.rss` — no auth needed |
| Add / remove RSS feed URLs | Any feed reader that can't be configured feels like a demo | LOW | Store feed URLs in DB; validate on add |
| Mark read / unread | Core feed reader behaviour; users feel broken without it | LOW | Per-item state in SQLite |
| In-app article reader | Sending user to browser defeats the in-app purpose | MEDIUM | Render full-text from feed `<content:encoded>` or fetch page and strip to main content |
| Unread count badge | Users navigate by unread count; missing it is jarring | LOW | Aggregate per-feed, show in sidebar |
| Keyboard navigation (j/k next/prev) | Power users from Feedly/NewsBlur expect this | LOW | Standard pattern; add after core works |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Ask-the-article (RAG over feed items) | Feed item appears in chat: "Summarise this" or "What does this mean for Llama 4?" — unique to Localis as a local AI host | MEDIUM | Push article text into session RAG context; reuse existing RAG pipeline |
| Keyword filter across all feeds | Combined filter view (e.g. "llama.cpp") across r/LocalLLaMA + other sources | LOW | SQLite FTS5 full-text search over cached items |
| Auto-summarise on open (via local LLM) | One-tap summary using the loaded model — no cloud, zero privacy cost | MEDIUM | Send article text to chat endpoint with a summarise system prompt; show in article pane |
| Configurable refresh interval | Some users want 15 min polling, some want manual — local-first means respecting user preference | LOW | Background polling with configurable interval in settings |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Cloud-based RSS sync (Fever API, Miniflux) | "Access from any device" | Network dependency; Localis is local-first; introduces auth complexity | Single-device is fine for v1; document this as intentional |
| Push notifications | "Don't miss new posts" | Requires persistent background process or OS notification hooks; disproportionate complexity for an RSS reader | Red badge on the nav rail icon is sufficient |
| Social sharing buttons (post to Twitter, LinkedIn) | Seen in Feedly/Inoreader | Leaks URL + user interest to third-party APIs | Let user copy link; not Localis's job |
| AI-generated feed recommendations | "Discover new sources" | Requires calling an external recommendation API or training a local model on interest graph — both are out of scope | User adds feeds manually; keep it simple |

---

## Feature 3: YouTube Music via HA

### Table Stakes

Based on Home Assistant media_player integration expectations and comparable voice-to-music flows.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Voice command triggers playback ("Hey Jarvis, play [song/artist]") | This is the entire stated use case; if voice doesn't trigger it, the feature doesn't exist | MEDIUM | Parse intent from STT output; extract song/artist entity; call HA service |
| HA media_player service call (media_player.play_media) | Standard HA approach for triggering playback | LOW | Requires user to have configured `ytube_music_player` or Music Assistant in HA first — document this prerequisite |
| Playback controls via voice (pause, resume, stop, next) | Users expect follow-up commands after playback starts | MEDIUM | Detect playback control intent in router; map to `media_player.media_pause`, `.media_next_track`, etc. |
| Feedback confirmation ("Playing [track] by [artist]") | Without audio/visual feedback, user doesn't know if command worked | LOW | Parse HA state after service call; read back current `media_title` + `media_artist` |
| Error message if HA entity not found | Users will misconfigure; clear error beats silent failure | LOW | Check entity exists before sending service call; surface error in voice status bar |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Natural language query extraction ("something chill by Hozier") | Mood-based requests beyond exact song/artist names — local LLM parses the intent before sending to HA | MEDIUM | Prompt the router to extract structured `{query, artist, mood}` from free-form speech; pass as search term to ytube_music_player |
| Now-playing display in RSB (right sidebar) | Show current track name + artist in the Localis UI, pulled from HA media_player state | LOW | Poll `GET /assist/light_state`-style endpoint for media_player entity; render in RSB |
| Multi-entity support (choose speaker) | "Play on bedroom speaker" | LOW | Detect room intent in parsed command; map to different HA entity |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Direct YouTube Music API integration (bypass HA) | "More reliable, faster" | Requires OAuth to Google — network egress, credential storage, refresh token management; violates privacy-first stance | Keep HA as the only integration layer; user owns their HA config |
| Music recommendation ("play something I'd like") | Personalisation sounds good | Needs listening history; building a recommendation engine locally is a separate large feature | Voice command with explicit query is sufficient; defer taste-based recommendation to a future phase |
| Lyrics display | Nice to have | Requires Genius/Musixmatch API call — network egress | Out of scope for v1 |
| Queue management via voice | "Add to queue", "play next" | HA's ytube_music_player queue support is inconsistent across HA versions | Document as known limitation; don't build fragile queue logic |

---

## Feature 4: Financial Advisor

### Table Stakes

Based on comparable tools: Firefly III, Actual Budget, MoneyWiz, and RAG-over-documents patterns.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| CSV import with column mapping | CSV is the universal export from every Indian and global bank; without it nothing works | MEDIUM | Auto-detect common column layouts (date, amount, description, balance); allow manual mapping for unusual schemas |
| OFX/QFX import | Standard format from most banks' "download transactions" flow | MEDIUM | Parse OFX XML structure; OFX is well-specified |
| Automatic transaction categorisation | Users will not manually tag 200 transactions; auto-cat with editable rules is the minimum | MEDIUM | Rule-based first (regex on merchant name); LLM-assisted as fallback for ambiguous |
| Category editing (rename, merge, reassign) | Auto-cat will make mistakes; bulk edit is critical | LOW | Per-category batch edit in the dashboard UI |
| Expense breakdown chart (pie/donut by category) | This is the primary visualisation users expect from a finance tool | MEDIUM | Render with a lightweight charting lib — Chart.js is the obvious choice given vanilla JS stack |
| Monthly spend trend (bar chart) | Second most expected chart; "am I spending more this month?" | MEDIUM | Aggregate by month; same Chart.js setup |
| RAG chat over statement data | The stated differentiator; "how much did I spend on food in January?" | MEDIUM | Push transactions as structured text into session RAG context |
| Session-isolated data (statements don't leak across sessions) | Finance data is maximally sensitive; must not bleed across chat sessions | LOW | Reuse existing RAG session isolation (`_safe_session_id()`); enforce at API level |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Full local processing — zero cloud | No bank data ever leaves the device; this is the primary reason to use Localis over Copilot/Cleo | LOW (architecture) | Already satisfied by local-first design; must be prominently stated in UI |
| Recurring payment detection | Auto-flag subscriptions and recurring charges so user can see what they're committed to monthly | MEDIUM | Pattern match on merchant + amount across months; LLM can verify ambiguous cases |
| Natural language query ("what did I spend on Swiggy last quarter?") | Local LLM turns statements into a conversational interface — no other local-first tool does this | MEDIUM | Structured prompt with transaction table; model extracts filter and aggregates |
| Smart categorisation rules that persist across uploads | User corrects "Zomato" → Food once; system remembers and applies next upload | LOW | Store correction rules in SQLite; apply during ingest |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Bank account direct connect (Plaid, open banking API) | "Automatic sync, no manual export" | Requires OAuth to financial institutions, credential storage, ongoing API fees — catastrophic privacy and complexity cost | Manual CSV/OFX upload only; frame it as a privacy feature |
| Investment portfolio tracking | Natural extension of finance features | Entirely different data model (securities, NAV, XIRR); doubles scope | Explicitly out of scope v1; note the boundary |
| Tax filing assistance | "You have the data, help me file taxes" | Tax rules are jurisdiction-specific, change yearly, require legal disclaimers — legal risk for an OSS project | Add a disclaimer that Localis is not a tax advisor; don't build filing workflows |
| Export to shared spreadsheets (Google Sheets sync) | "Share with partner" | Network egress to Google; violates privacy-first | Offer CSV export from the dashboard instead |
| LLM fine-tuning on financial data | "Personalised financial advice model" | Fine-tuning on personal bank data introduces privacy risk if model weights are ever shared | RAG over raw data is safer and already sufficient |

---

## Feature 5: Post+ (Writing Style Mimicry)

### Table Stakes

Based on comparable tools (Pollen Content DNA, TeamPost, HyperWrite Imitate Writing Style) and few-shot learning research.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Accept text examples from user (paste or upload) | Style mimicry with zero examples is just a generic LLM prompt; examples are the entire premise | LOW | Accept pasted text in a textarea; store per-platform profile |
| Platform-separated profiles (Reddit vs LinkedIn) | Style differs dramatically between platforms — mixing them degrades output | LOW | Two distinct profile stores; separate example sets and generated output |
| Generate a post given a topic | The primary use case: user gives topic, system writes in their style | LOW | Few-shot prompt construction from stored examples; pass to loaded model |
| Soft warning below minimum example count | Stated product decision; educates user rather than blocking them | LOW | Threshold: 3 examples minimum for reasonable output (below 5 is low quality per few-shot research); show amber warning, not hard block |
| Regenerate / iterate | First draft is rarely final; one-click regenerate is expected | LOW | Re-run same prompt with `temperature` nudged slightly for variety |
| Edit generated post before using | Output is a starting point, not final copy | LOW | Inline editable text area after generation |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Example diversity scorer | Show user a quality indicator — "your 4 examples cover 2 topic types, add variety for better mimicry" — no competitor does this locally | MEDIUM | Compute embedding diversity across stored examples; ChromaDB already available |
| Platform-specific structural guidance | LinkedIn posts have hooks + line breaks; Reddit posts have contextual tone; system applies structural templates on top of style mimicry | LOW | Encode structural rules in system prompt per platform; user doesn't see the complexity |
| Tone knob per post (more formal / more casual within your style) | Fine-grained control over a single generation without changing the profile | LOW | Inject tone instruction into the generation prompt |
| Style profile import/export | Power users want to back up or share their style profile | LOW | Export examples as JSON; import from JSON file |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Auto-post directly to LinkedIn/Reddit | "One-click publish" | Requires OAuth tokens stored persistently; LinkedIn API is restrictive and terms-hostile to automated posting | Generate text only; user copies and pastes |
| Style scraping from a public profile URL | "Analyse my existing LinkedIn profile for me" | Requires outbound HTTP to LinkedIn/Reddit; LinkedIn blocks scrapers aggressively; legal grey area | User pastes their own text manually — they already have it |
| Ghostwriting detection bypass ("make it pass AI detectors") | Users will ask for this | Actively harmful feature; misleads readers; reputational risk for the project | Don't implement; if asked, explain why |
| Shared style marketplace (upload profile, download others') | Community feature | Network dependency; sharing style data has implicit privacy risks; out of scope for local-first tool | Single-user profiles only |
| Fine-tune model on user writing | "Train the model to always sound like me" | Fine-tuning requires significant GPU time, careful dataset prep, and risks catastrophic forgetting on a shared model | Few-shot prompting at inference time is good enough and safer |

---

## Feature Dependencies

```
Post+
    └──requires──> stored LLM model (any loaded model)
    └──enhances──> existing RAG pipeline (example storage in ChromaDB)

Financial Advisor
    └──requires──> existing RAG session isolation (rag.py)
    └──requires──> Chart.js (new dependency)
    └──independent of──> memory system (Tier-A/B)

News RSS Feed
    └──optional-enhances──> Financial Advisor (ask-the-article reuses same RAG pattern)
    └──independent of──> voice system

YouTube Music via HA
    └──requires──> existing HA integration (assist.py)
    └──requires──> existing STT/voice pipeline (voiceUI, wakewordUI)
    └──independent of──> RAG system

LAB
    └──requires──> model loader (main.py MODEL_LOCK)
    └──conflicts-with──> any in-progress inference (parameter changes that trigger reload must wait for MODEL_LOCK)
    └──independent of──> memory, RAG, voice
```

### Dependency Notes

- **Financial Advisor requires Chart.js:** This is the only new frontend dependency introduced. It must be loaded without a CDN (local-first: bundle the JS file into `app/static/`).
- **Post+ and Financial Advisor both use RAG pattern:** They use different session types but the same underlying `rag.py` infrastructure. No conflict, but both phases need to coordinate on RAG session naming conventions.
- **YouTube Music via HA requires voice pipeline:** The HA feature is meaningless without the existing wakeword + STT chain. If voice is broken, this feature fails silently. Add an explicit check in the music command handler.
- **LAB conflicts with active inference:** A reload triggered mid-conversation will fail with MODEL_LOCK contention. Hard-params (n_ctx, n_gpu_layers) must only apply when no inference is running. Soft-params (temp, top-p, repeat penalty) can be passed per-request without reload.

---

## MVP Definition

All five features are new additions to an existing working product, so "MVP" here means the minimum scope to consider each feature shippable.

### Launch With (each feature's v1)

**LAB:**
- [ ] Sliders for temp, top-p, repeat penalty (apply per-request, no reload)
- [ ] Inputs for n_ctx and n_gpu_layers with explicit Apply button + reload warning
- [ ] Persist current values to DB
- [ ] Reset to defaults button

**News RSS:**
- [ ] r/LocalLLaMA pre-loaded as default source
- [ ] Add/remove feeds
- [ ] Mark read/unread
- [ ] In-app article text display (feed content field; no full-page fetch)
- [ ] Unread badge on nav

**YouTube Music via HA:**
- [ ] Parse play/pause/stop/next from voice
- [ ] Call correct HA media_player service
- [ ] Read back current track name as TTS confirmation
- [ ] Clear error if entity not found

**Financial Advisor:**
- [ ] CSV import with auto column detection
- [ ] Auto-categorisation with edit capability
- [ ] Pie chart by category + bar chart by month
- [ ] RAG chat over uploaded statement

**Post+:**
- [ ] Paste examples for Reddit and LinkedIn (separate)
- [ ] Soft warning below 3 examples
- [ ] Generate post given a topic
- [ ] Inline edit + regenerate

### Add After Validation (v1.x)

- [ ] LAB named presets (A/B defaults) — after users confirm they use LAB regularly
- [ ] RSS ask-the-article (RAG) — after RSS reader core is stable
- [ ] RSS auto-summarise on open — after ask-the-article is validated
- [ ] Financial Advisor recurring payment detection — after import + charts are in daily use
- [ ] Post+ example diversity scorer — after users have built up 5+ example profiles

### Future Consideration (v2+)

- [ ] LAB live parameter comparison (two inference calls side-by-side) — high complexity, needs MODEL_LOCK scheduling
- [ ] Financial Advisor OFX import — CSV covers most use cases; add OFX when users request it specifically
- [ ] Post+ style profile import/export — quality-of-life; not blocking
- [ ] YouTube Music natural language mood extraction — depends on router model quality improvements

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| LAB — sliders + per-request params | HIGH (power users, students) | LOW | P1 |
| LAB — named presets | MEDIUM | MEDIUM | P2 |
| LAB — live comparison | LOW (niche) | HIGH | P3 |
| RSS — core reader (fetch, read, mark) | MEDIUM | LOW | P1 |
| RSS — ask-the-article | HIGH (Localis differentiator) | MEDIUM | P2 |
| RSS — auto-summarise | MEDIUM | MEDIUM | P2 |
| YouTube Music — voice play/control | HIGH (demo-worthy) | MEDIUM | P1 |
| YouTube Music — now-playing RSB | LOW | LOW | P2 |
| Financial Advisor — CSV + charts | HIGH (personal use, daily driver) | MEDIUM | P1 |
| Financial Advisor — RAG chat | HIGH (Localis differentiator) | MEDIUM | P1 |
| Financial Advisor — recurring detection | MEDIUM | MEDIUM | P2 |
| Post+ — core generation (paste → generate) | HIGH (daily use case) | LOW | P1 |
| Post+ — diversity scorer | MEDIUM | MEDIUM | P2 |
| Post+ — style export | LOW | LOW | P3 |

---

## Privacy Implications Summary

This is a privacy-first app. The following flags apply to these features:

| Feature | Privacy Risk | Mitigation |
|---------|-------------|------------|
| Financial Advisor — CSV upload | CRITICAL: bank statements contain PII, account numbers, merchant data | Session-isolated storage; files deleted on session end (add explicit delete prompt); never log transaction content; all processing local |
| Financial Advisor — RAG context | HIGH: transactions injected into LLM context | All inference is local; ensure no debug logging of context content when `LOCALIS_DEBUG=1` |
| Post+ — example text | MEDIUM: user writing may contain personal information | Stored locally in SQLite only; never logged; user can delete profile |
| News RSS — feed URLs | LOW: feed subscription list reveals interests | Stored locally; never sent anywhere |
| YouTube Music — song queries | LOW: voice queries are already processed locally | No new risk beyond existing voice pipeline |
| LAB — parameters | NONE | Pure local configuration |

---

## Competitor Feature Analysis

| Feature | LM Studio | Open WebUI | Localis Approach |
|---------|-----------|------------|-----------------|
| Parameter sliders | Yes, per-model GUI | Yes, per-chat | Persist per-model in DB; add named presets |
| RSS reader | None | None | First-class feature; integrated with LLM chat |
| Music voice control | None | None | HA-mediated; reuses existing voice pipeline |
| Finance analysis | None | None | RAG over statements; local-only |
| Writing style mimicry | None | None | Few-shot profiles per platform |

Localis is not competing with LM Studio or Open WebUI on parameter management — those are well-served. The differentiation is in the integrated, privacy-first feature set that goes beyond pure inference tooling.

---

## Sources

- LM Studio vs Open WebUI feature comparison: [markaicode.com](https://markaicode.com/vs/lm-studio-vs-ollama/)
- LLM sampling parameters (Min-P guidance): [letsdatascience.com](https://letsdatascience.com/blog/llm-sampling-temperature-top-k-top-p-and-min-p-explained)
- RSS reader table stakes: [Zapier best RSS apps 2026](https://zapier.com/blog/best-rss-feed-reader-apps/)
- Home Assistant YouTube Music integration: [ytube_music_player GitHub](https://github.com/KoljaWindeler/ytube_music_player), [Music Assistant HA docs](https://www.home-assistant.io/integrations/music_assistant/)
- Bank statement CSV/OFX import standards: [Koody CSV import](https://koody.com/blog/personal-finance-app-csv-import), [Firefly III](https://www.firefly-iii.org/)
- Financial PII in RAG: [LlamaIndex PII guide](https://www.llamaindex.ai/blog/pii-detector-hacking-privacy-in-rag), [bank statement LLM analysis](https://www.c-sharpcorner.com/article/automating-bank-statement-analysis-with-llms-rag-techniques/)
- Few-shot learning quality thresholds: [mem0.ai few-shot guide](https://mem0.ai/blog/few-shot-prompting-guide), [Label Studio few-shot](https://labelstud.io/learningcenter/few-shot-learning-train-ai-with-just-a-few-examples/)
- LinkedIn AI writing tools: [leapshq.com 2026 comparison](https://leapshq.com/blog/best-linkedin-post-generators), [TeamPost](https://teampost.ai/blog/best-ai-tools-linkedin-2026)

---

*Feature research for: Localis — new feature milestone (LAB, RSS, YouTube Music, Financial Advisor, Post+)*
*Researched: 2026-03-14*
