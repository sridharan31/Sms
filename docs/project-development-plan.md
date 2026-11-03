# SMS Finance Tracker: End-to-End Project Development Plan

Nov 3, 2026 · Companion to [`project-research.md`](project-research.md)

## How to use this plan

This plan takes the project from an unfinished research idea to a launched, maintained app. It is sized for **one person building with AI**: validate first, keep the documents few, write real code early, and get a thin version into testers' hands fast. Each stage ends with a **gate**, a short checklist that has to pass before the next stage starts.

| # | Stage | Main output | Tool | Rough time (solo + AI) |
|---|---|---|---|---|
| R | Research, idea validation + **technical spike** | Validated business plan; proof that capture works on real phones | You + Claude (sections R1–R4) | 3–4 weeks |
| 0–2 | **Lean spec:** stack, BRD, functional spec, privacy/legal drafts, budget | `plancasting/` (tech stack, short BRD, PRD = the one living spec) | Transmute `/tech-stack`, `/brd`, `/prd`, `/validate-specs` | 1–2 weeks |
| 3 | Technical architecture | One `docs/architecture.md` + short ADRs; second spike if needed | Claude | 3–5 days |
| 4 | UI/UX design (overlaps Stage 3) | Wireframes, design tokens, clickable prototype | Claude + a design tool | 1 week |
| 5 | Development in vertical slices | Thin end-to-end slice with closed testers by dev week 4–6, then grow | Claude Code + Transmute `/scaffold`, `/implement` | 10–14 weeks (MVP) |
| 6 | Testing and QA | Test reports, audit fixes | Transmute audits + mobile test stack | Alongside Stage 5, plus 2 weeks hardening |
| 7 | Deployment, operations, feedback loop | Play Store release, monitoring, monthly releases | Play Console, CI/CD, Transmute `/feedback` | 2–4 weeks staged rollout, then ongoing |

**Rough timeline:** first real code in week 3 (the spike); spec done by week 6; development starts around week 7; first slice with closed testers around weeks 10–12; MVP launch around weeks 20–24.

**One framework.** Transmute is the only spec framework. It has no architecture or design stage, so Claude writes those two documents directly. BMAD and Spec Kit aren't needed and would add a second set of file conventions.

**Documents are kept few on purpose.** The BRD is generated once and frozen as the baseline. The **PRD is the single living spec**: when something changes, update the PRD (and an ADR if it's a big decision), nothing else.

You are at **Stage R**. The research now covers metrics, MVP scope, edge cases and global requirements; what's missing is evidence from real users, a technical spike and a few open decisions (section R1).

---

## Stage R: Research and idea validation

**Goal:** prove that real people have this problem and would pay for this app, before writing requirements.

The research now targets **anyone whose money lives in more than one currency or country** (migrant workers, expat professionals, students, travelers, families at home, investors abroad), with **India–UAE as the launch corridor**. Its section *Gap analysis for a global BRD* already answers most of what this stage asked for. What remains is mainly **evidence from real users** and a few open decisions.

### R1. Status of the research

| Item | Status | Where |
|---|---|---|
| Problem, personas, modules, regulation, pricing, competitors | Done | `project-research.md` |
| Success metrics and North Star (G2) | Done | Research → Success metrics |
| MVP boundary (G3) | Done | Research → MVP boundary |
| Transaction edge-case rules (G4) | Done | Research → Edge-case rules |
| Parsing accuracy, security, consent, AI targets (G5–G8) | Done (targets set) | Research → Critical gaps |
| Global gaps: number/date formats, time zones, wallets, remittance channels, store taxes, country rules as data, eligibility, inflation (G21–G28) | Done (requirements written) | Research → Important gaps |
| New ideas: rule file, "report wrong parse", salary-day plan, send-home signal, safe-to-spend widget, gratuity + return-home readiness | Done (rule file and "report wrong parse" are MVP Must) | Research → New ideas in detail |
| **User evidence (G1)** | **Open** | R2 below |
| **Open decisions** (launch corridors, Flutter vs native, cloud region, AI vendor and cost cap, prices, SMS at launch or later) | **Open** | Research → Open decisions |
| **Legal:** UAE PDPL Executive Regulations still unpublished (G20); SMS permission rejections still happen in practice (G19) | **Open, tracked** | Research → Review findings |

Corrections already made in the research, which this plan follows:
- **SMS is optional at launch.** The MVP launches on notification capture plus paste and statement import; SMS is added if Google Play approves it.
- **On-device AI is not the main parser.** Gemini Nano runs only on some recent phones and only in the foreground, so parsing is rules first, Nano as an optional speed-up, and masked cloud AI only with opt-in and a cost cap.
- **Rule files must be pure data, never code,** to stay within Google Play's policy on downloaded code.

### R2. How to validate the idea (2–4 weeks)

Follow the research's *User research plan*. In practice:

1. **Interviews: 20–30 people across 3 corridors:** India–UAE (launch), Philippines–Gulf, and one Western corridor (e.g. Mexico–US or expats in the UK). Ask about past behaviour, not opinions: "How did you track money last month?" "Walk me through your last transfer home and what it cost." "Which apps did you try and why did you stop?" Write each up in `docs/research/interviews/`.
2. **Count the evidence.** For each pain point, note how many people raised it without prompting. Keep features most people raised; move the rest to "later".
3. **Waitlist page** in English, Arabic and one Asian language, with the price shown. Measure sign-ups per visitor and per corridor.
4. **Concierge test.** For 5–10 friendly users, build their monthly multi-currency summary by hand (a spreadsheet is fine) from SMS they choose to share (masked, with consent, deleted afterwards). Note what surprised them and what they would pay for.
5. **Collect the SMS test set:** at least 500 masked messages per launch country (the research's accuracy target), including exchange houses and wallets.
6. **Close the open decisions** listed in the research, and record each one as an ADR (Stage 3).

**Decision rule (from the research):** proceed if most interviewees describe the multi-currency problem unprompted and the waitlist shows clear interest at the listed price; otherwise narrow to the strongest corridor.

### R3. Further ideas not yet in the research

| Idea | What it does | Phase |
|---|---|---|
| Remittance cost league table | Uses the user's own past transfers to rank providers by true cost (builds on G24) | 2 |
| Hours-of-work view | "This AED 450 dinner = 6 hours of work", from the user's salary | 2 |
| Family view with one-way share | Earner abroad sees the family's shared budget at home, with each person's consent | 3 |
| Chat-style quick entry | "taxi 25 aed" typed or spoken becomes a transaction | 3 |
| Shareable monthly card | Privacy-safe image ("Saved 22% this month") for community groups | 3 |

Avoid or delay: anything that names specific funds or stocks (regulated advice), lending or credit scoring (strict Google Play personal-loan rules), reading contacts.

### R4. Technical spike (weeks 3–4, alongside interviews)

Before writing specs, build the riskiest piece for real, as throwaway code. The question to answer: **can the app capture and read transactions reliably on the phones your users own?**

- A minimal Android app (Flutter + Kotlin plugin) that listens to notifications (and reads SMS on a test build), runs a few parser rules, and shows a list.
- Run it for a week on 3–4 real phones, including a budget Xiaomi or Samsung (these often stop background apps to save battery).
- Measure: share of bank alerts captured, how many are cut short, parsing accuracy on your first samples, battery use.
- Write the result as the first ADR. If capture is unreliable, the MVP leans harder on statement import, and the plan changes **now** rather than in month 3.

### R5. Play Store and account decisions (start now, they take time)

- **Closed testing rule.** New *personal* Google Play developer accounts (created after 13 Nov 2023) must run a closed test with at least **12 testers opted in for 14 continuous days** before each new app can go to production; internal testing doesn't count ([Google Play help](https://support.google.com/googleplay/android-developer/answer/14151465?hl=en-GB), [summary](https://www.testerscommunity.com/blog/google-play-closed-testing-requirements-2026)). **Recruit 20–25 testers from the waitlist during Stage R** so it can't block the launch.
- **Personal or organization account.** Google requires an organization account for apps offering financial products and services such as banking, loans, stock trading or investment funds ([Google Play policy](https://support.google.com/googleplay/android-developer/answer/10788890?hl=en)). A tracker and simulator probably falls outside that, but broker links or investment features could pull it in. An organization account needs a registered company and a D-U-N-S number, and it's exempt from the 12-tester rule. Decide before registering, since account type is hard to change later.
- **Financial features declaration.** Every app must complete it in Play Console, even one with no financial features.

**Gate R → 0:** interviews done and written up; decision rule met; spike result recorded as an ADR; open decisions closed; developer account type chosen; 20+ testers recruited; SMS test set started (≥ 200 samples); legal questions have an owner and date.

---

## Stages 0–2: Lean spec (1–2 weeks)

**Input:** the research doc, validation results and the spike ADR.
**Output:** `plancasting/tech-stack.md`, a short BRD (`plancasting/brd/`), the PRD (`plancasting/prd/`), privacy/legal drafts and a budget.

Run the Transmute stages back to back, without polishing each document separately:

1. Copy `docs/project-research.md`, the validation results and the spike ADR into `plancasting/businessplan/` (Transmute reads `.md` or `.pdf` from there).
2. `/tech-stack`: answer with the recommended stack below.
3. `/brd`: check it has goals and KPIs, the seven personas, MVP scope, business rules (edge cases, duplicates, currency, remittance cost, gratuity and safe-to-spend formulas, simulator rules and disclaimers), country rules as data (G26), regulation (SEBI advice line, DPDP, PDPL, GDPR baseline, Play policy) and NFRs (G9–G11, G21–G22). Transmute marks guesses as `ASSUMPTION`; get the assumption volume **below 30%**. Then freeze the BRD as the baseline.
4. `/prd` then `/validate-specs`. The PRD must define:
   - **Screens:** onboarding + consent, permissions explainer, home dashboard, transactions list, transaction detail/edit, accounts, import (paste/file), duplicate review, categories, insights, what-if simulator, settings, privacy centre (export/delete), paywall.
   - **User flows:** first-run (install → consent → grant notification or SMS access → history import → first summary); daily capture; correcting a parse; reviewing a possible duplicate; running a simulation from an insight; trial end.
   - **Acceptance criteria** in Given/When/Then form. Example: *Given* "Purchase of AED 85.50 with Card ending 1234 at CARREFOUR", *when* it arrives, *then* a debit of 85.50 AED on card ••1234, merchant Carrefour, category Groceries is created within 2 seconds, and *no* duplicate is created when the matching statement line is imported later.
   - **Data model** and **parser contract:** input (sender, body, timestamp) → output (fields + confidence + rule ID).
   - **Analytics events** for each KPI in the research (activation, auto-capture rate, retention, trial-to-paid), with no personal data in any event.
5. **Privacy and legal drafts (now, not at the end):** privacy policy, Play Data safety form answers, consent screen texts, the SMS permission declaration text, the financial features declaration, and the "scenarios, not advice" wording for the lawyer's review.
6. **Budget** (see the Budget section): confirm what the MVP year will cost.

### Recommended stack

| Layer | Choice | Reason |
|---|---|---|
| App | **Flutter** (Dart) with a small **Kotlin** plugin for SMS and notification access | One codebase for the later iOS app; SMS/notification reading has to be native Android anyway. Kotlin Multiplatform is the alternative if you prefer fully native UI and already know Kotlin |
| State | Riverpod | Testable, widely used |
| Local DB | SQLite via Drift, encrypted with SQLCipher; key in Android Keystore | Offline, encrypted at rest, typed queries, migrations |
| Parser | Rule engine reading a signed JSON rule pack (pure data, never code); Gemini Nano as an optional speed-up on supported phones; masked cloud AI only with opt-in and a cost cap | Works on budget phones; known banks parse fast and privately; unknown formats still work |
| Charts | fl_chart | Native Flutter, works on low-end phones |
| Backend (thin) | Serverless functions (e.g. Cloudflare Workers or Supabase Edge) for: FX rates, rule pack hosting, billing webhooks, masked parse reports | Local-first app; avoid running servers in the MVP |
| Sync (phase 2) | Supabase (Postgres) with end-to-end encrypted payloads, or skip sync until asked | Keep the MVP server-light |
| Billing | Google Play Billing (via RevenueCat or the official plugin) | Trials, regional prices, entitlements |
| Crash/analytics | Sentry or Firebase Crashlytics with PII scrubbing; privacy-first analytics | From the first build; no amounts, merchants or SMS ever leave the phone |
| CI/CD | GitHub Actions + Fastlane (or Codemagic) | Builds, tests, signed releases to Play tracks |

**Gate 0–2 → 3:** stack confirmed; BRD assumption volume < 30% and frozen; `/validate-specs` shows no uncovered requirements or contradictions; every MVP screen has acceptance criteria; privacy and legal drafts written; budget agreed.

---

## Stage 3: Technical architecture (3–5 days)

Claude writes **one** document, `docs/architecture.md`, from the PRD, plus short ADRs. No separate HLD/LLD files.

**`docs/architecture.md` covers:**
- Component diagram: capture sources (notifications, SMS, paste, file) → normalizer → parser (rules → optional on-device AI → masked cloud AI) → dedup/transfer matcher → encrypted store → analytics/simulator → UI. Thin cloud: rates, rule packs, billing, masked reports.
- Data flow and trust boundaries: what never leaves the phone (raw SMS, amounts unless sync is on).
- Database schema and migration approach.
- Rule-pack format (JSON schema, version, signature, built-in test samples, rollback).
- Duplicate score algorithm with the research's weights, and thresholds for auto-merge vs asking the user.
- FX service (sources, caching, offline fallback) and background work (WorkManager, battery limits).
- App folder structure (feature-first) and logging rules (no personal data).
- Threat model (STRIDE) mapped to OWASP MASVS controls.

**ADRs (`docs/adr/`)**, one short file per big decision: spike result; Flutter vs KMP; local-first; SQLCipher; rule pack as data; parser AI order; billing provider; developer account type.

**Second spike (1–2 days, only if needed):** anything the first spike didn't cover and the design depends on, e.g. SQLCipher speed on a 2 GB phone or rule-pack signing.

**Gate 3 → 4:** architecture reviewed; every NFR has an answer; threat model done.

---

## Stage 4: UI/UX design (1 week, overlaps Stage 3)

1. **Information architecture:** bottom navigation of 4–5 tabs (Home, Transactions, Insights, Plan, Settings).
2. **Wireframes** for every PRD screen, low fidelity first.
3. **Design system:** colours as tokens, type scale, spacing, motion (durations, easing, when to animate), components (cards, amount chips with currency, charts). Plan for dark mode, RTL (Arabic), large text and "reduce motion" from the start.
4. **Key UX rules for this app:**
   - Always show the original currency next to the converted amount.
   - Use an "Illustrative" label and a range (low/mid/high) on every projection.
   - Explain each permission on a screen of its own *before* the system prompt.
   - Show at least one useful insight within 10 minutes of install (the research's activation target).
   - Make correcting a wrong parse take 1 tap.
5. **Clickable prototype** (Figma or similar) and **5 usability tests** with target users, ideally people from the tester list.

Tools: Claude for flows, screen specs and design tokens; a design tool for visuals. Transmute's `/redesign` and `/polish` come later, on the built app.

**Gate 4 → 5:** prototype tested with 5 users; top usability issues fixed; design tokens exported.

---

## Stage 5: Development (AI-assisted)

### 5.1 Build order: vertical slices

Get a **thin end-to-end slice** working first, put it in closed testers' hands, then widen it. Each slice runs from capture all the way to the screen.

| Sprint (2 weeks) | Slice | Delivered to |
|---|---|---|
| 1 | Scaffold (`/scaffold`), CI, encrypted DB, crash reporting and analytics events, app lock. **Slice 1:** notification capture → rule parser for the first 5 banks → transaction list → this month's total in home currency | Internal testing |
| 2 | Rule pack + accuracy test in CI; paste import; categories with corrections; "report wrong parse" | Internal testing |
| 3 | Accounts, multi-currency, FX rates offline; monthly dashboard. **Open the closed test track** (the 14-day clock starts) | **Closed testers (dev weeks 5–6)** |
| 4 | Duplicate check and transfer matching; statement import; remittance cost | Closed testers |
| 5 | Insights (subscriptions, delivery, fees); what-if simulator (SIP/EMI) | Closed testers |
| 6 | Privacy centre (export/delete), consent log, paywall + Play Billing, SMS reading if approved | Closed testers |
| 7 | Hardening, audits (Stage 6), fixes from tester feedback | Closed testers → production review |

Review analytics and tester feedback at the end of every sprint, and update the PRD before starting the next one.

### 5.2 The AI-assisted ("vibe coding") workflow

"Vibe coding" works for prototypes. For a finance app, use **spec-driven AI development**: the AI writes most of the code, but always from a written spec, in small steps, with tests and reviews.

**Tools**

| Role | Recommended | Notes |
|---|---|---|
| Main coding agent | **Claude Code** (terminal, desktop, or cloud sessions like this one) | Plans, edits many files, runs tests, commits |
| Editor | Android Studio (Flutter plugin) or VS Code / Cursor | For reading code, debugging, emulators |
| Spec framework | **Transmute** (installed) for BRD → PRD → scaffold → implement → audits | Already in `.claude/skills/` |
| Architecture + UX docs | Claude, directly from the PRD | Transmute has no stage for these; one document each |
| Code review | Claude Code `/code-review` and `/security-review` on every PR | A second pass catches what the writing pass missed |
| CI | GitHub Actions | Runs lint, tests, parser accuracy, build on every push |

Use **one** spec framework (Transmute) so there is only one set of file conventions.

**Project files that steer the AI** (create in Stage 5, sprint 1):

- `CLAUDE.md` at the repo root: what the app is, the stack, folder layout, commands (`flutter test`, `flutter analyze`), coding rules, and the hard rules below. Keep it under ~150 lines; link to docs instead of copying them.
- `AGENTS.md`: a short copy of the same rules if you also use other agents.
- `docs/` specs and ADRs, which the AI reads before changing code.

**Hard rules to put in `CLAUDE.md`:**
- Never commit real SMS, account numbers or names. Test data is synthetic or masked.
- Never log amounts, merchants or message text.
- Every parser change adds or updates test cases; accuracy must not drop.
- No investment advice wording; projections always show a range and the disclaimer.
- Money is stored as integer minor units plus an ISO 4217 currency code (some currencies have 0 or 3 decimals), never as floats.
- Times are stored in UTC plus the local offset; months follow the user's home time zone.
- Rule packs and country packs are data only; never download or run code.
- Database changes need a migration and a migration test.

**Daily loop for each feature**

1. **Pick one small task** (≤ 1 day) from the PRD with its acceptance criteria.
2. **Plan first:** ask Claude to read the spec and the relevant code and propose a plan. Approve or correct it before any code.
3. **Tests first:** have it write failing tests from the acceptance criteria.
4. **Implement** until tests pass; run `flutter analyze` and the full test suite.
5. **Review:** run `/code-review`, read the diff yourself, and fix what matters.
6. **Commit** with a clear message and open a PR; CI must be green to merge.
7. **Update docs** if the behaviour or a decision changed.

Use a separate branch (or git worktree) per feature so parallel AI sessions don't collide.

**Prompt templates**

*Feature implementation*
```
Implement <feature> from plancasting/prd/<file>.md (acceptance criteria AC-1..AC-n).
First read CLAUDE.md, the PRD section, and <relevant folders>.
Propose a plan (files to change, tests to add) and wait for my OK.
Then: write failing tests for each AC, implement, run flutter analyze and flutter test,
and show me the results. Follow the hard rules in CLAUDE.md. Keep the change under ~400 lines;
if it's bigger, split it and tell me.
```

*New bank SMS format*
```
Add parser support for <bank>. Masked samples are in test/fixtures/sms/<bank>.txt
(expected fields in <bank>.expected.json). Add rules to the rule pack, not code, unless a
new rule type is truly needed. Run the accuracy test; report accuracy before and after,
per bank. Don't lower any other bank's accuracy.
```

*Bug fix*
```
Bug: <what happens> vs <what should happen>. Steps: <steps>.
Reproduce it with a failing test first, then fix the cause (not the symptom),
and explain the root cause in the PR description.
```

*Review*
```
Review this branch against main for: correctness, money handling (minor units, rounding,
currency), privacy (no PII in logs/analytics), security (MASVS), and missing tests.
List findings by severity with file:line. Don't change code.
```

### 5.3 Production-ready standards (Definition of Done)

A feature is done only when:

- [ ] All acceptance criteria have passing automated tests.
- [ ] `flutter analyze` is clean (use a strict lint set such as `very_good_analysis`).
- [ ] Unit test coverage ≥ 80% overall; ≥ 95% for the parser, money maths and dedup.
- [ ] Parser accuracy on the SMS test set did not drop (target ≥ 95% amount + currency + direction; < 0.5% wrong merges).
- [ ] No personal data in logs, crash reports or analytics.
- [ ] Works offline; handles errors with a clear message.
- [ ] Screen works with large text, screen reader and Arabic RTL layout.
- [ ] Code reviewed (AI review + your own read of the diff).
- [ ] Docs/ADRs updated if behaviour or a decision changed.

---

## Stage 6: Testing and QA

| Test type | What | Tool |
|---|---|---|
| Unit | Parser rules, money maths, FX conversion, dedup scoring, simulator formulas | `flutter test` |
| Parser accuracy | ≥ 500 masked messages per launch country with expected fields; report per bank and country pack; fails CI if accuracy drops | Custom test built from the SMS test set collected in Stage R |
| Widget + golden | Each screen in light/dark, LTR/RTL, large text | Flutter golden tests |
| Integration / end-to-end | First-run, SMS capture, import, duplicate review, paywall | `integration_test` or Patrol, on emulators |
| Device matrix | Low-end (2–3 GB RAM, Android 10) to latest Android; Samsung, Xiaomi, Pixel (OEM battery killers affect background capture) | Firebase Test Lab or real devices |
| Security | OWASP MASVS checklist, dependency scan, secrets scan | Transmute `/audit-security`, Claude `/security-review` |
| Accessibility | Screen reader, contrast, touch targets | Transmute `/audit-a11y` (adapt for Flutter), Android Accessibility Scanner |
| Completeness | Every PRD feature implemented, no stubs | Transmute `/audit-completeness` |
| Performance | Cold start, history import time, memory on a low-end phone | Flutter DevTools, Android profiler |
| Beta | 30–50 real users from the waitlist for 4 weeks | Play Console closed testing |

**Note on Transmute's Stage 6:** `/verify`, `/optimize` and `/smoke` assume a web app in a browser (`localhost`, Lighthouse). For this Android app, use the checklists in those skills but run them against emulators and the tools above.

**Gate 6 → 7:** all must-have tests green; external test against OWASP MASVS passed with no critical or high findings open; beta crash-free rate ≥ 99.5%; parse accuracy and monthly totals (within 1% of bank statements) meet the research targets; `/prelaunch` checklist passed.

---

## Stage 7: Deployment and operations

1. **Play Console setup:** app listing, Data safety form (must match what the app really does), SMS permission declaration form with a demo video, content rating, privacy policy URL.
2. **Release tracks:** internal → closed testing (from Stage 5 sprint 3; on a personal account, at least 12 testers opted in for 14 continuous days before production access) → production with **staged rollout** (5% → 20% → 50% → 100%), pausing if the crash rate rises.
3. **CI/CD:** tag → GitHub Actions builds and signs → uploads to the Play internal track. Keep signing keys in Play App Signing and CI secrets, never in the repo.
4. **Monitoring:** crash-free rate, ANRs, parse-failure rate per bank (from masked reports), billing errors, FX rate job health.
5. **Operations runbook (`docs/ops/`):** what to do when a bank changes its SMS format (ship a rule pack update), when FX rates fail (use cache, show "rate as of"), when Play rejects a release, and when there's a data incident (DPDP/PDPL breach reporting).
6. **Feedback loop:** every month, collect in-app feedback, "report wrong parse" data, store reviews and KPI analytics → run Transmute `/feedback` to turn them into PRD updates → re-prioritise the backlog → ship. Compare KPIs with the research's targets each month and revisit the business plan every quarter.
7. **Maintenance:** `/maintain` for monthly dependency and security updates.

---

## Budget (first year, rough)

Confirm current prices before committing; most services have free tiers that cover an MVP.

| Item | Cost | Notes |
|---|---|---|
| Google Play developer account | USD 25, one-time | Organization account also needs a company and a D-U-N-S number |
| Apple developer account | USD 99/year | Only when the iOS app starts (not MVP) |
| AI coding tools | Your Claude plan, plus any editor subscription | The largest fixed cost for a solo builder |
| Serverless backend + rule-pack hosting | Free tier at MVP scale | Cloudflare Workers or Supabase |
| Cloud AI for unknown SMS formats | Capped per user (research: per-user cost cap) | Set a monthly ceiling and alerts |
| FX rates API | Free tier, or low monthly fee | Cache on the phone |
| Crash reporting, analytics, billing tools | Free tiers at start | Sentry/Crashlytics, RevenueCat |
| Domain, landing page, email | Low yearly cost | Needed in Stage R |
| Legal review (India + UAE) | Get quotes | "Scenarios, not advice" wording, privacy policy, terms |
| External security test (OWASP MASVS) | Get quotes | Required by the Stage 6 gate |
| Test phones (budget Xiaomi/Samsung) | One-off | Needed for the spike and device testing |

Add the total to the business plan, and compare it with the research's revenue model to see how many paying users cover costs.

## Folder layout

```
docs/
  project-research.md          research (Stage R)
  project-development-plan.md  this plan
  research/interviews/         interview notes (R2)
  architecture.md              architecture (Stage 3)
  adr/                         decision records
  ux/                          wireframes, flows, design tokens (Stage 4)
  ops/                         runbooks (Stage 7)
plancasting/                   Transmute's working folder
  businessplan/                lean spec input
  tech-stack.md, brd/          lean spec (BRD frozen as baseline)
  prd/                         the one living spec
CLAUDE.md                      AI working rules (Stage 5)
```

## Next actions (this week)

- [ ] Write the interview script and book the first 5 interviews across the 3 corridors (R2).
- [ ] Start collecting masked SMS samples, aiming for 200 by the end of Stage R.
- [ ] Put up the landing page and waitlist; recruit 20–25 closed testers from it.
- [ ] Decide personal vs organization Play developer account (R5).
- [ ] Plan the technical spike for weeks 3–4 (R4).
- [ ] Close the research's open decisions and record each as an ADR.
- [ ] Track the UAE PDPL regulations and Google Play SMS policy (G19, G20).
- [ ] When the Stage R gate passes: copy the research into `plancasting/businessplan/` and run `/tech-stack`.

## Sources

- [Google Play — SMS and Call Log policy preview (July 2026)](https://support.google.com/googleplay/android-developer/answer/17225965)
- [Simmons & Simmons — UAE PDPL FAQs](https://www.simmons-simmons.com/en/publications/ckwugz8lu16rs0a44qvbqcbz9/uae-personal-data-protection-law-faqs)
- [Google Play — app testing requirements for new personal accounts](https://support.google.com/googleplay/android-developer/answer/14151465?hl=en-GB)
- [Testers Community — Google Play closed testing requirements 2026](https://www.testerscommunity.com/blog/google-play-closed-testing-requirements-2026)
- [Google Play — organization account requirement and financial features declaration](https://support.google.com/googleplay/android-developer/answer/10788890?hl=en)
- [Flutter vs Kotlin Multiplatform in 2026 (FlutterFever)](https://flutterfever.com/news/flutter-vs-kotlin-multiplatform/)
- [AI coding workflow best practices: CLAUDE.md, AGENTS.md, subagents (2026)](https://www.youngju.dev/blog/culture/2026-05-14-ai-coding-workflow-best-practices-2026-claude-md-agents-md-cursorrules-subagent-skill-design-deep-dive.en)
- Other facts (regulation, market size, pricing) are sourced in `project-research.md`.
