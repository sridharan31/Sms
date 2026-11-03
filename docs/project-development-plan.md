# SMS Finance Tracker: End-to-End Project Development Plan

Nov 3, 2026 · Companion to [`project-research.md`](project-research.md)

## How to use this plan

This plan takes the project from an unfinished research idea to a launched, maintained app. It runs in 9 stages, and each one ends with a **gate**: a short checklist that has to pass before the next stage starts. Gates stop you from writing code on top of requirements that aren't settled yet.

| # | Stage | Main output | Tool | Rough time (solo + AI) |
|---|---|---|---|---|
| R | Research and idea validation | Validated business plan | You + Claude (this plan, sections R1–R6) | 2–4 weeks |
| 0 | Business plan and tech stack | `plancasting/tech-stack.md` | Transmute `/tech-stack` | 2–3 days |
| 1 | BRD | `plancasting/brd/` | Transmute `/brd` | 3–5 days |
| 2 | Functional design (PRD/FDD) | `plancasting/prd/` | Transmute `/prd` then `/validate-specs` | 1 week |
| 3 | Technical architecture (HLD/LLD) | `docs/architecture/` + ADRs | BMAD Architect, or Claude directly | 1 week |
| 4 | UI/UX design | `docs/ux/` + clickable prototype | BMAD UX Designer + a design tool | 1–2 weeks |
| 5 | Development | Working app, built feature by feature | Claude Code + Transmute `/scaffold`, `/implement` | 10–14 weeks (MVP) |
| 6 | Testing and QA | Test reports, audit fixes | Transmute audits + mobile test stack | Runs alongside Stage 5, plus 2 weeks hardening |
| 7 | Deployment and operations | Play Store release, monitoring | Play Console, CI/CD | 2–4 weeks staged rollout |

You are at **Stage R**. The research document is a strong start, but it isn't yet a business plan the later stages can rely on. The gaps are listed in section R2.

---

## Stage R: Research and idea validation

**Goal:** prove that real people have this problem and would pay for this app, before writing requirements.

### R1. What the research already covers well

- A clear target user (Indians working in the UAE) and a sharp promise: three currencies, one view, plus "what could this money become".
- A realistic plan for when SMS access is refused (notification listener, email forwarding, statement import).
- Duplicate detection, remittance cost and currency effects worked out in detail.
- The regulatory line ("scenarios, not advice") drawn early.
- Pricing, a competitor scan and a risk register.

### R2. Missing requirements and gaps

These are the gaps found by checking the research against what a BRD and a production fintech app need. They are grouped by how much they matter.

**Critical (must be decided before the BRD)**

| # | Gap | Why it matters | What to add |
|---|---|---|---|
| G1 | **No user evidence** | All pain points are assumptions; nothing yet shows people would switch or pay | 15–20 user interviews and a waitlist test (R3) |
| G2 | **No success metrics** | Nothing to judge the MVP against | North Star metric plus 4–6 KPIs (R5) |
| G3 | **No MVP boundary** | The feature table has 40+ features across 4 phases; nothing is labelled "must have for launch" | MoSCoW list (R6) |
| G4 | **Transaction edge cases not covered** | These break totals and user trust | Rules for refunds and reversals, partial refunds, card pre-auth holds, declined/failed transactions, cashback, card purchases converted to EMI, UPI autopay mandate setup (not a debit), ATM cash out (becomes "cash wallet"), credit card bill payment (a transfer, not spending) |
| G5 | **No parsing accuracy target** | "Works" is not testable | e.g. ≥ 95% correct amount + currency + direction on a masked set of 500+ SMS; ≥ 85% correct category before user edits |
| G6 | **Security requirements thin** | Finance app on phones that get lost or shared | Threat model; app lock (PIN + biometric); encrypted DB with key in Android Keystore; block screenshots on sensitive screens; root/tamper detection (warn, don't block); no OTP ever stored; encrypted backups with a recovery plan; follow OWASP MASVS |
| G7 | **Consent and data lifecycle** | Required by India's DPDP rules and UAE PDPL | Consent screens per data source, consent log, retention period, one-tap delete, data export format, privacy policy text |
| G8 | **AI processing rules undefined** | "Send to an AI model" may move personal data off the phone | Decide: on-device model first (e.g. Gemini Nano where the phone supports it), cloud only with masked text and opt-in; set a cost cap per user |

**Important (add to the BRD)**

| # | Gap | What to add |
|---|---|---|
| G9 | Non-functional requirements | Cold start < 2 s on a low-end phone (2–3 GB RAM); parse 10,000 SMS history in < 60 s; works fully offline; app size < 30 MB; battery impact negligible |
| G10 | Languages and right-to-left | English first; Arabic needs full RTL layout; Hindi, Malayalam, Tamil later. Design for this from day one, even if translated later |
| G11 | Accessibility | Large text, screen reader labels, colour-blind-safe charts (WCAG 2.2 AA) |
| G12 | Merchant cleaning | A merchant dictionary ("AMZN MKTP" → Amazon, "CAREEM*RIDE" → Careem) shared between the parser and categories |
| G13 | Exchange houses | Many UAE workers send money through exchange houses (and apps like Wise), not banks. Their receipts and SMS need parsers |
| G14 | Cash and gold | Cash spending is common for the blue-collar persona; gold buying is common in the UAE. Both need manual or quick entry |
| G15 | Billing and entitlements | Google Play Billing, trial rules, stopping trial abuse (one trial per account), grace period, restoring purchases |
| G16 | Multi-device sync conflicts | If sync is offered, decide how conflicts are resolved (simplest: last write wins per field, with an edit history) |
| G17 | Support and feedback | In-app "report a wrong parse" button that sends a masked sample with consent. This is also how the parser keeps improving |
| G18 | Analytics without personal data | Product analytics and crash reports must never contain amounts, merchants or SMS text |
| G19 | Policy re-check | Google Play's SMS/Call Log policy changed again in July 2026 (default-handler rules; financial-transaction exceptions). Re-read the current policy text before the BRD is final ([Google Play policy preview](https://support.google.com/googleplay/android-developer/answer/17225965)) |
| G20 | UAE PDPL status | Sources disagree on whether the PDPL Executive Regulations have been issued; nothing confirms it from a primary UAE source ([Simmons & Simmons FAQ](https://www.simmons-simmons.com/en/publications/ckwugz8lu16rs0a44qvbqcbz9/uae-personal-data-protection-law-faqs)). Track as an open legal question |

### R3. How to validate the idea (2–4 weeks)

Do these in order; each costs little and can stop a bad idea early.

1. **Problem interviews (15–20 people).** Mix of the four personas. Ask about the past, not about your app: "Walk me through the last time you sent money home." "How do you know what you spent last month?" "What apps have you tried and why did you stop?" Write each one up in `docs/research/interviews/`.
2. **Count the evidence.** For each pain point in the research, note how many people raised it *without prompting*. Keep features where ≥ 40% did; push the rest to "later".
3. **Landing page and waitlist.** One page with the promise, three screenshots (mock-ups are fine) and an email sign-up. Share in UAE Indian community groups. Target: ≥ 300 sign-ups or a ≥ 10% sign-up rate from visits.
4. **Price test.** On the waitlist confirmation, ask "Would you pay AED 9.99/month or AED 79/year?" with three answers (yes / maybe at a lower price / no).
5. **Concierge test.** For 5–10 friendly users, build their monthly multi-currency summary by hand (a spreadsheet is fine) from SMS they choose to share (masked, with consent, deleted afterwards). Show them the result. Note what surprised them and what they would pay for.
6. **Collect the SMS test set.** Gather 500+ masked bank SMS from UAE and Indian banks (the research asked for 50; aim higher). This becomes the parser's accuracy test.

**Kill or pivot criteria:** fewer than 5 of 20 interviewees track money at all, *and* fewer than 100 sign-ups → narrow to one persona (e.g. salaried professionals only), or re-think.

### R4. Suggested improvements and new ideas

Ranked by value for the target users and how cheaply they can be built.

| Idea | What it does | Why it's strong | Phase |
|---|---|---|---|
| **Parser rules as signed data** | Bank SMS templates live in a JSON rule pack the app downloads and verifies, not in app code | Fix a broken bank format in hours, without a Play Store release | MVP |
| **"Report wrong parse" loop** | User taps a transaction → corrects it → masked template (no amounts, no names) is sent with consent | The parser improves from real use; a moat competitors lack for UAE banks | MVP |
| **Salary-day plan** | When a salary SMS arrives: "AED 18,000 in. Last 3 months you sent AED 5,000 home and spent AED 9,200. Plan this month?" | Turns tracking into a monthly habit at the moment money arrives | MVP+ |
| **Send-home timing signal** | Shows today's INR/AED rate against the 30- and 90-day average | Practical, not advice, and directly tied to remittances | 2 |
| **Remittance cost league table** | Uses the user's *own* past transfers to show true cost per provider | Builds on the cost formula already designed | 2 |
| **"Safe to spend" widget** | Home-screen widget: what's left this month after rent, EMIs and planned remittance | Daily reason to open the app | 2 |
| **Hours-of-work view** | "This AED 450 dinner = 6 hours of work" from the user's salary | Simple, memorable, good for the blue-collar persona | 2 |
| **Family view with one-way share** | Earner in UAE sees the India family's shared budget (each person consents) | Matches how NRI money actually works; strong reason for the Family plan | 3 |
| **Gratuity + return-home readiness** | UAE end-of-service gratuity estimate plus "months of India expenses covered" | Unique to the Gulf expat case | 3 |
| **WhatsApp-style quick entry** | "taxi 25 aed" typed or spoken in a chat box becomes a transaction | Fast cash entry, familiar format | 3 |
| **Share a monthly card** | A privacy-safe image ("Saved 22% this month") to share | Free growth inside community groups | 3 |

Ideas to **avoid or delay**: anything that suggests specific funds or stocks (regulated advice); credit scoring or lending (Google Play's personal loan rules are strict); reading contacts.

### R5. Success metrics

- **North Star:** monthly active users who have ≥ 80% of their transactions captured automatically.
- Activation: % of new users who see their first monthly summary within 24 hours of install (target ≥ 60%).
- Parse accuracy: % of auto-captured transactions not edited by the user (target ≥ 90%).
- Retention: week-4 retention ≥ 35%.
- Trial to paid: ≥ 5% (research model's low case), aim for 10%.
- Trust: share of users who turn on cloud sync or "report wrong parse" (proxy for trust).

### R6. Proposed MVP scope (Android only)

| Must have | Should have | Later |
|---|---|---|
| SMS capture (if approved) **and** notification listener + paste import | Statement CSV/PDF import | Bank data feeds (AA, AlTareq) |
| Parser for top 10 UAE + top 10 Indian banks, rule pack updates | Screenshot import of holdings | Broker APIs (IBKR) |
| Accounts with own currency; any home currency; daily FX rates offline | Subscriptions detector | Family plan |
| Duplicate check + own-account transfer matching | Remittance cost per transfer | iOS app |
| Categories with learn-from-correction | Goals | Languages beyond English and Arabic |
| Monthly dashboard: income, spending, savings rate, by country | Travel mode | AI "ask your money" |
| What-if simulator (SIP, lump sum, EMI vs save) with ranges and disclaimer | | |
| App lock, encrypted DB, export, delete account | | |
| Free trial + Premium via Play Billing | | |

**Gate R → 0:** interviews done and written up; top 3 pains confirmed; MVP list agreed; metrics set; SMS test set ≥ 200 samples; open legal questions listed.

---

## Stage 0: Business plan and tech stack

**Input:** the research doc updated with R2–R6.
**Output:** `plancasting/businessplan/` (the business plan) and `plancasting/tech-stack.md`.

1. Turn the research into a business plan: copy `docs/project-research.md` plus the validation results into `plancasting/businessplan/` (Transmute reads `.md` or `.pdf` files from there).
2. Run `/tech-stack`. It will ask questions; the recommended answers are below.

### Recommended stack

| Layer | Choice | Reason |
|---|---|---|
| App | **Flutter** (Dart) with a small **Kotlin** plugin for SMS and notification access | One codebase for the later iOS app; SMS/notification reading has to be native Android anyway. Kotlin Multiplatform is the alternative if you prefer fully native UI and already know Kotlin |
| State | Riverpod | Testable, widely used |
| Local DB | SQLite via Drift, encrypted with SQLCipher; key in Android Keystore | Offline, encrypted at rest, typed queries, migrations |
| Parser | Rule engine reading a signed JSON rule pack; falls back to on-device AI, then masked cloud AI with opt-in | Known banks parse fast and privately; unknown formats still work |
| Charts | fl_chart | Native Flutter, works on low-end phones |
| Backend (thin) | Serverless functions (e.g. Cloudflare Workers or Supabase Edge) for: FX rates, rule pack hosting, billing webhooks, masked parse reports | Local-first app; avoid running servers in the MVP |
| Sync (phase 2) | Supabase (Postgres) with end-to-end encrypted payloads, or skip sync until asked | Keep the MVP server-light |
| Billing | Google Play Billing (via RevenueCat or the official plugin) | Trials, regional prices, entitlements |
| Crash/analytics | Sentry or Firebase Crashlytics with PII scrubbing; privacy-first analytics | No amounts, merchants or SMS ever leave the phone |
| CI/CD | GitHub Actions + Fastlane (or Codemagic) | Builds, tests, signed releases to Play tracks |

**Gate 0 → 1:** tech stack confirmed; hosting region chosen (UAE or India); budget for paid services noted.

---

## Stage 1: Business Requirements Document (BRD)

Run `/brd`. It reads the business plan and tech stack and writes `plancasting/brd/`.

**Check that the BRD contains:** business goals and KPIs (R5); personas; scope in/out (R6); business rules (edge cases G4, duplicate rules, currency rules, remittance cost formula, simulator rules and disclaimers); regulatory requirements (SEBI advice line, DPDP, PDPL, Play policy); NFRs (G9–G11); risks and assumptions.

Transmute marks guesses as `ASSUMPTION` and computes an assumption volume. **Get it below 30%** by answering the open questions; above that it flags the BRD as critical.

**Gate 1 → 2:** assumption volume < 30%; every requirement has an ID (BR-, FR-, NFR-); legal questions have an owner and a date.

---

## Stage 2: Functional Design (PRD / FDD)

Run `/prd`, then `/validate-specs`.

**What the functional design must define for this app:**

- **Screens:** onboarding + consent, permissions explainer, home dashboard, transactions list, transaction detail/edit, accounts, import (paste/file), duplicate review, categories, insights, what-if simulator, goals, settings, privacy centre (export/delete), paywall.
- **User flows:** first-run (install → consent → grant SMS or notification access → history import → first summary); daily capture; correcting a parse; reviewing a possible duplicate; running a simulation from an insight; trial end.
- **Acceptance criteria** in Given/When/Then form for each feature. Example:
  *Given* an SMS "Purchase of AED 85.50 with Card ending 1234 at CARREFOUR", *when* it arrives, *then* a debit of 85.50 AED on card ••1234, merchant Carrefour, category Groceries is created within 2 seconds, and *no* duplicate is created when the matching bank statement line is later imported.
- **Data model:** accounts, transactions (original amount, currency, rate, rate source, home amount), sources, merchants, categories, rules, FX rates, holdings, goals, consents.
- **Parser contract:** input (sender, body, timestamp) → output (fields + confidence + rule ID).

**Gate 2 → 3:** `/validate-specs` shows no uncovered BRD requirements and no contradictions; every MVP screen has acceptance criteria.

---

## Stage 3: Technical Architecture (HLD / LLD)

Transmute has no dedicated architecture stage, so write these documents before scaffolding. Use BMAD's Architect agent, or ask Claude to write them from the PRD.

**HLD (`docs/architecture/hld.md`):**
- Component diagram: capture sources (SMS, notifications, paste, file) → normalizer → parser (rules → on-device AI → cloud AI) → dedup/transfer matcher → encrypted store → analytics/simulator → UI. Thin cloud: rates, rule packs, billing, masked reports.
- Data flow and trust boundaries: what never leaves the phone (raw SMS, amounts unless sync is on).
- Deployment view: app, edge functions, storage, CI/CD.
- Threat model (STRIDE) and mapping to OWASP MASVS controls.

**LLD (`docs/architecture/lld/`):**
- Database schema and migrations.
- Parser rule-pack format (JSON schema, version, signature), and rule matching order.
- Duplicate score algorithm with the weights from the research, and thresholds for auto-merge vs ask the user.
- FX service: sources, caching, fallback when offline.
- Background work: Android WorkManager jobs, battery limits.
- Module/package structure for the Flutter app (feature-first folders).
- Error handling and logging rules (no personal data in logs).

**Architecture Decision Records (`docs/adr/`)** — one short file per big choice: Flutter vs KMP; local-first; SQLCipher; rule pack as data; on-device AI first; billing provider.

**Gate 3 → 4:** HLD and LLD reviewed; every NFR has an architectural answer; threat model done.

---

## Stage 4: UI/UX Design

1. **Information architecture:** bottom navigation of 4–5 tabs (Home, Transactions, Insights, Plan, Settings).
2. **Wireframes** for every PRD screen, low fidelity first.
3. **Design system:** colours as tokens, type scale, spacing, components (cards, amount chips with currency, charts). Plan for dark mode, RTL (Arabic) and large text from the start.
4. **Key UX rules for this app:**
   - Always show the original currency next to the converted amount.
   - Use an "Illustrative" label and a range (low/mid/high) on every projection.
   - Explain each permission on a screen of its own *before* the system prompt.
   - Show at least one useful insight within 5 minutes of install.
   - Make correcting a wrong parse take 1 tap.
5. **Clickable prototype** (Figma or similar) and **5 usability tests** with target users before coding.

Tools: BMAD's UX Designer agent for flows and specs; a design tool for visuals. Transmute's `/redesign` and `/polish` come later, on the built app.

**Gate 4 → 5:** prototype tested with 5 users; top usability issues fixed; design tokens exported.

---

## Stage 5: Development (AI-assisted)

### 5.1 Build order

Build the riskiest, most valuable parts first.

| Sprint (2 weeks) | Deliverable |
|---|---|
| 1 | Project scaffold (`/scaffold`), CI, encrypted DB, design tokens, app lock |
| 2 | Parser engine + rule pack for the first banks; accuracy test running in CI |
| 3 | SMS reader and notification listener (Kotlin plugin), paste import, history import |
| 4 | Accounts, multi-currency, FX rates offline, transaction list and edit |
| 5 | Duplicate check, transfer matching, categories with learning |
| 6 | Dashboard, insights (subscriptions, delivery, fees, remittance cost) |
| 7 | What-if simulator, privacy centre (export/delete), paywall + Play Billing |
| 8 | Hardening, audits (Stage 6), closed beta |

### 5.2 The AI-assisted ("vibe coding") workflow

"Vibe coding" works for prototypes. For a finance app, use **spec-driven AI development**: the AI writes most of the code, but always from a written spec, in small steps, with tests and reviews.

**Tools**

| Role | Recommended | Notes |
|---|---|---|
| Main coding agent | **Claude Code** (terminal, desktop, or cloud sessions like this one) | Plans, edits many files, runs tests, commits |
| Editor | Android Studio (Flutter plugin) or VS Code / Cursor | For reading code, debugging, emulators |
| Spec framework | **Transmute** (installed) for BRD → PRD → scaffold → implement → audits | Already in `.claude/skills/` |
| Architecture + UX | **BMAD Method** Architect and UX Designer agents ([BMAD guide](https://developertoolkit.ai/en/ecosystem/frameworks/bmad-method/)) | Fills Transmute's Stage 3–4 gap |
| Per-feature specs | **GitHub Spec Kit** (`/specify` → `/plan` → `/tasks`) is an option for new features after launch ([Spec Kit guide](https://codemyspec.com/blog/github-spec-kit-guide)) | GitHub calls it an experiment; Transmute's `/feedback` covers similar ground |
| Code review | Claude Code `/code-review` and `/security-review` on every PR | A second pass catches what the writing pass missed |
| CI | GitHub Actions | Runs lint, tests, parser accuracy, build on every push |

Pick **one** spec framework per stage to avoid conflicting file layouts: Transmute for 0–2 and 5–7, BMAD only for 3–4.

**Project files that steer the AI** (create in Stage 5, sprint 1):

- `CLAUDE.md` at the repo root: what the app is, the stack, folder layout, commands (`flutter test`, `flutter analyze`), coding rules, and the hard rules below. Keep it under ~150 lines; link to docs instead of copying them.
- `AGENTS.md`: a short copy of the same rules if you also use other agents.
- `docs/` specs and ADRs, which the AI reads before changing code.

**Hard rules to put in `CLAUDE.md`:**
- Never commit real SMS, account numbers or names. Test data is synthetic or masked.
- Never log amounts, merchants or message text.
- Every parser change adds or updates test cases; accuracy must not drop.
- No investment advice wording; projections always show a range and the disclaimer.
- Money is stored as integer minor units (fils, paise, cents) plus currency code, never as floats.
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
- [ ] Parser accuracy on the SMS test set did not drop.
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
| Parser accuracy | 500+ masked SMS with expected fields; report per bank; fails CI if accuracy drops | Custom test built from the SMS test set collected in Stage R |
| Widget + golden | Each screen in light/dark, LTR/RTL, large text | Flutter golden tests |
| Integration / end-to-end | First-run, SMS capture, import, duplicate review, paywall | `integration_test` or Patrol, on emulators |
| Device matrix | Low-end (2–3 GB RAM, Android 10) to latest Android; Samsung, Xiaomi, Pixel (OEM battery killers affect background capture) | Firebase Test Lab or real devices |
| Security | OWASP MASVS checklist, dependency scan, secrets scan | Transmute `/audit-security`, Claude `/security-review` |
| Accessibility | Screen reader, contrast, touch targets | Transmute `/audit-a11y` (adapt for Flutter), Android Accessibility Scanner |
| Completeness | Every PRD feature implemented, no stubs | Transmute `/audit-completeness` |
| Performance | Cold start, history import time, memory on a low-end phone | Flutter DevTools, Android profiler |
| Beta | 30–50 real users from the waitlist for 4 weeks | Play Console closed testing |

**Note on Transmute's Stage 6:** `/verify`, `/optimize` and `/smoke` assume a web app in a browser (`localhost`, Lighthouse). For this Android app, use the checklists in those skills but run them against emulators and the tools above.

**Gate 6 → 7:** all must-have tests green; no critical or high security findings open; beta crash-free rate ≥ 99.5%; parse accuracy meets the R2 target; `/prelaunch` checklist passed.

---

## Stage 7: Deployment and operations

1. **Play Console setup:** app listing, Data safety form (must match what the app really does), SMS permission declaration form with a demo video, content rating, privacy policy URL.
2. **Release tracks:** internal → closed testing (beta) → production with **staged rollout** (5% → 20% → 50% → 100%), pausing if the crash rate rises.
3. **CI/CD:** tag → GitHub Actions builds and signs → uploads to the Play internal track. Keep signing keys in Play App Signing and CI secrets, never in the repo.
4. **Monitoring:** crash-free rate, ANRs, parse-failure rate per bank (from masked reports), billing errors, FX rate job health.
5. **Operations runbook (`docs/ops/`):** what to do when a bank changes its SMS format (ship a rule pack update), when FX rates fail (use cache, show "rate as of"), when Play rejects a release, and when there's a data incident (DPDP/PDPL breach reporting).
6. **After launch:** Transmute `/feedback` to turn feedback into spec updates and `/maintain` for monthly dependency updates; release monthly.

---

## Folder layout

```
docs/
  project-research.md          research (Stage R)
  project-development-plan.md  this plan
  research/interviews/         interview notes (R3)
  architecture/  hld.md, lld/  (Stage 3)
  adr/                         decision records
  ux/                          wireframes, flows, design tokens (Stage 4)
  ops/                         runbooks (Stage 7)
plancasting/                   Transmute's working folder
  businessplan/                Stage 0 input
  tech-stack.md                Stage 0 output
  brd/  prd/                   Stages 1–2
CLAUDE.md                      AI working rules (Stage 5)
```

## Next actions (this week)

- [ ] Write the interview script and book the first 5 interviews (R3).
- [ ] Start collecting masked SMS samples, aiming for 200 by the end of Stage R.
- [ ] Put up the landing page and waitlist.
- [ ] Add R2–R6 decisions to `project-research.md` as they're made.
- [ ] Re-read the current Google Play SMS policy and note what applies (G19).
- [ ] When the Stage R gate passes: copy the research into `plancasting/businessplan/` and run `/tech-stack`.

## Sources

- [Google Play — SMS and Call Log policy preview (July 2026)](https://support.google.com/googleplay/android-developer/answer/17225965)
- [Simmons & Simmons — UAE PDPL FAQs](https://www.simmons-simmons.com/en/publications/ckwugz8lu16rs0a44qvbqcbz9/uae-personal-data-protection-law-faqs)
- [Developer Toolkit — BMAD Method: agile roles as agents](https://developertoolkit.ai/en/ecosystem/frameworks/bmad-method/)
- [CodeMySpec — GitHub Spec Kit guide (2026)](https://codemyspec.com/blog/github-spec-kit-guide)
- [Flutter vs Kotlin Multiplatform in 2026 (FlutterFever)](https://flutterfever.com/news/flutter-vs-kotlin-multiplatform/)
- [AI coding workflow best practices: CLAUDE.md, AGENTS.md, subagents (2026)](https://www.youngju.dev/blog/culture/2026-05-14-ai-coding-workflow-best-practices-2026-claude-md-agents-md-cursorrules-subagent-skill-design-deep-dive.en)
- Other facts (regulation, market size, pricing) are sourced in `project-research.md`.
