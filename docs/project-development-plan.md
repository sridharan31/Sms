# SMS Finance Tracker: End-to-End Project Development Plan

Nov 3, 2026 · Companion to [`project-research.md`](project-research.md)

## How to use this plan

This plan takes the project from an unfinished research idea to a launched, maintained app. It runs in 9 stages, and each one ends with a **gate**: a short checklist that has to pass before the next stage starts. Gates stop you from writing code on top of requirements that aren't settled yet.

| # | Stage | Main output | Tool | Rough time (solo + AI) |
|---|---|---|---|---|
| R | Research and idea validation | Validated business plan | You + Claude (this plan, sections R1–R3) | 2–4 weeks |
| 0 | Business plan and tech stack | `plancasting/tech-stack.md` | Transmute `/tech-stack` | 2–3 days |
| 1 | BRD | `plancasting/brd/` | Transmute `/brd` | 3–5 days |
| 2 | Functional design (PRD/FDD) | `plancasting/prd/` | Transmute `/prd` then `/validate-specs` | 1 week |
| 3 | Technical architecture (HLD/LLD) | `docs/architecture/` + ADRs | BMAD Architect, or Claude directly | 1 week |
| 4 | UI/UX design | `docs/ux/` + clickable prototype | BMAD UX Designer + a design tool | 1–2 weeks |
| 5 | Development | Working app, built feature by feature | Claude Code + Transmute `/scaffold`, `/implement` | 10–14 weeks (MVP) |
| 6 | Testing and QA | Test reports, audit fixes | Transmute audits + mobile test stack | Runs alongside Stage 5, plus 2 weeks hardening |
| 7 | Deployment and operations | Play Store release, monitoring | Play Console, CI/CD | 2–4 weeks staged rollout |

You are at **Stage R**. The research now covers metrics, MVP scope, edge cases and global requirements; what's missing is evidence from real users and a few open decisions (section R1).

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

**Gate R → 0:** interviews done and written up; decision rule met; open decisions closed; SMS test set started (≥ 200 samples); legal questions have an owner and date.

---

## Stage 0: Business plan and tech stack

**Input:** the research doc plus the validation results from Stage R.
**Output:** `plancasting/businessplan/` (the business plan) and `plancasting/tech-stack.md`.

1. Turn the research into a business plan: copy `docs/project-research.md` plus the validation results into `plancasting/businessplan/` (Transmute reads `.md` or `.pdf` files from there).
2. Run `/tech-stack`. It will ask questions; the recommended answers are below.

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
| Crash/analytics | Sentry or Firebase Crashlytics with PII scrubbing; privacy-first analytics | No amounts, merchants or SMS ever leave the phone |
| CI/CD | GitHub Actions + Fastlane (or Codemagic) | Builds, tests, signed releases to Play tracks |

**Gate 0 → 1:** tech stack confirmed; hosting region chosen (UAE or India); budget for paid services noted.

---

## Stage 1: Business Requirements Document (BRD)

Run `/brd`. It reads the business plan and tech stack and writes `plancasting/brd/`.

**Check that the BRD contains:** business goals and KPIs; all seven personas; scope in/out (the research's MVP boundary); business rules (edge-case rules, duplicate rules, currency rules, remittance cost, gratuity and safe-to-spend formulas, simulator rules and disclaimers); country rules as versioned data (G26); regulatory requirements (SEBI advice line, DPDP, PDPL, GDPR baseline, Play policy); NFRs (G9–G11, G21–G22); risks and assumptions.

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

- [ ] Write the interview script and book the first 5 interviews across the 3 corridors (R2).
- [ ] Start collecting masked SMS samples, aiming for 200 by the end of Stage R.
- [ ] Put up the landing page and waitlist.
- [ ] Close the research's open decisions and record each as an ADR.
- [ ] Track the UAE PDPL regulations and Google Play SMS policy (G19, G20).
- [ ] When the Stage R gate passes: copy the research into `plancasting/businessplan/` and run `/tech-stack`.

## Sources

- [Google Play — SMS and Call Log policy preview (July 2026)](https://support.google.com/googleplay/android-developer/answer/17225965)
- [Simmons & Simmons — UAE PDPL FAQs](https://www.simmons-simmons.com/en/publications/ckwugz8lu16rs0a44qvbqcbz9/uae-personal-data-protection-law-faqs)
- [Developer Toolkit — BMAD Method: agile roles as agents](https://developertoolkit.ai/en/ecosystem/frameworks/bmad-method/)
- [CodeMySpec — GitHub Spec Kit guide (2026)](https://codemyspec.com/blog/github-spec-kit-guide)
- [Flutter vs Kotlin Multiplatform in 2026 (FlutterFever)](https://flutterfever.com/news/flutter-vs-kotlin-multiplatform/)
- [AI coding workflow best practices: CLAUDE.md, AGENTS.md, subagents (2026)](https://www.youngju.dev/blog/culture/2026-05-14-ai-coding-workflow-best-practices-2026-claude-md-agents-md-cursorrules-subagent-skill-design-deep-dive.en)
- Other facts (regulation, market size, pricing) are sourced in `project-research.md`.
