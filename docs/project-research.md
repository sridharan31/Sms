# SMS Finance Tracker & Investment Simulator — Project Research

Nov 2, 2026 · @Sridharan

## Executive summary

Build an Android-first app that reads bank SMS in USD, AED and INR, turns them into one multi-currency spending view, and shows what the money could become if invested instead. The first users are Indians working in the UAE (NRIs) who earn in AED or USD, spend in both countries, and send money home every month. The design is global: anyone in any country picks a home currency, adds banks in any currency, and imports by SMS, paste or file (see Global design).

The app has four parts:

1. **Capture** — read bank and card SMS (and later, bank data feeds) automatically.
2. **Understand** — convert every amount to one home currency and sort spending into categories.
3. **Compare** — simulate the same money in Indian stocks and funds (Groww), US and global stocks (IBKR), land in India, or paying an EMI versus saving first.
4. **Plan** — set goals (house, education, retirement) and track progress.

The core promise: *"See where your money went in three currencies, and what it could become."* The app should show scenarios, not give personal buy or sell advice, because that is a regulated activity in India (see Regulatory section).

## Problem and target users

About 4.3 million Indians live in the UAE, and the UAE sends about 19.2% of India's remittances — the second-largest source ([Indian Embassy UAE](https://www.indembassyuae.gov.in/page/bilateral-economic-and-commercial-relations/)). India's inward remittances hit a record USD 135.46 billion in FY2024–25 ([Gulf News, citing RBI](https://gulfnews.com/gn-focus/how-digital-integration-and-exchange-rates-boost-uae-india-money-transfers-1.500425616)).

The pain points this app solves:

- **Money is scattered.** Salary arrives in AED, card spending is in AED and USD, family spending and EMIs are in INR. SMS alerts arrive from different banks in different formats.
- **No single view.** Indian apps track INR only; UAE apps track AED only. Nobody shows net worth across both countries.
- **Hidden remittance cost.** People see the amount sent, not the fee plus the exchange-rate markup.
- **No "what if".** People rarely see what a monthly AED 1,000 on food delivery could grow to if invested.
- **Confusing NRI rules.** NRE vs NRO accounts, property rules and taxes in two countries.

| Persona | Income | Main need |
| --- | --- | --- |
| Blue-collar worker in UAE | AED 1,500–4,000/month | Track remittances, save, avoid high fees |
| Salaried professional in UAE | AED 10,000–40,000/month | Multi-currency budget, invest in India and US |
| Family in India receiving money | INR | See how money sent is used, EMIs |
| Returning NRI | AED + INR assets | Plan land, property and retirement in India |

## Module 1: SMS capture and parsing

SMS reading is allowed on Android for budget apps, but only after Google Play review; iOS does not allow it, so bank data feeds are the long-term path.

**Android rules.** Google Play lists "SMS-based money management — apps that track and manage budget" as a permitted use of READ\_SMS and RECEIVE\_SMS, subject to review and approval. The permission must serve the app's core function, and a declaration form is required ([Google Play SMS policy](https://support.google.com/googleplay/android-developer/answer/10208820?hl=en)). Plan for a rejection risk: some budget apps dropped SMS features after the 2019 policy change ([Bluecoins notice](https://bluecoinsapp.com/?p=9286)).

**iPhone.** Apps cannot read the SMS inbox. Options: share-sheet import (user forwards an SMS to the app), manual paste, bank statement PDF upload, or bank data feeds.

**Bank data feeds (better long-term than SMS):**

| Country | System | Status |
| --- | --- | --- |
| India | [Account Aggregator](https://sahamati.org.in/?p=1269258) (RBI-regulated, consent-based) | 181M+ accounts linked by June 2025; 15+ licensed AAs such as Setu, Anumati, PhonePe |
| UAE | [AlTareq Open Finance](https://facephi.com/observatory/en/open-finance-eau-2026/) (Central Bank of UAE, via Nebras API hub) | Live at ADCB, CBD, FAB, ADIB; early stage; access needs a CBUAE licence or a licensed partner |

To use India's AA network, the app must join as a Financial Information User (FIU), which normally means being an RBI-, SEBI-, IRDAI- or PFRDA-regulated entity, or partnering with one.

**Parsing pipeline:**

1. Filter by sender ID (e.g. `JD-HDFCBK`, `ENBD`, `ADCBAlert`) to keep only bank messages.
2. Run regex templates per bank for amount, currency, card/account last 4 digits, merchant, balance, date.
3. Unknown format → send the text (with account numbers masked) to an on-device or cloud AI model to extract fields.
4. Deduplicate (the same purchase can trigger card SMS plus bank SMS).
5. Ask the user to confirm low-confidence results; their corrections train the templates.

**Example SMS and extracted fields:**

| SMS (sample) | Amount | Currency | Type | Merchant |
| --- | --- | --- | --- | --- |
| "Purchase of AED 85.50 with Card ending 1234 at CARREFOUR..." | 85.50 | AED | Debit | Carrefour |
| "Rs.12,450 debited from A/c XX5678 for EMI..." | 12,450 | INR | Debit | Loan EMI |
| "USD 19.99 spent on card XX1234 at NETFLIX.COM" | 19.99 | USD | Debit | Netflix |
| "Salary AED 18,000 credited to A/c XX9012" | 18,000 | AED | Credit | Salary |

Privacy rule: parse on the phone where possible, and never upload raw SMS text (it contains OTPs and personal messages).

### If SMS access is refused: other ways to automate

The app should not depend on SMS alone. If Google Play refuses READ\_SMS, a mix of notification reading, email forwarding and statement import still captures most transactions automatically.

| Method | How it works | Automation | Limits |
| --- | --- | --- | --- |
| Notification listener | User grants "notification access"; the app reads bank app and SMS notifications as they arrive | High, real-time | New messages only (no history); long texts may be cut. Since Android 15, notifications with one-time passcodes are hidden from ordinary apps ([Android Authority](https://androidauthority.com/android-15-two-factor-authentication-codes-3492585)) — good for privacy, as bank alerts still come through |
| Email forwarding address | User sets an auto-forward rule in Gmail or Outlook for bank alerts and e-statements to a private app address | High after one-time setup | Needs a server to receive mail; must be encrypted and deleted after parsing |
| Gmail / Outlook API | App reads the inbox directly with permission | High | Every Gmail read scope is "restricted"; Google requires verification plus a yearly third-party security assessment (CASA) when data passes through a server ([Nylas docs](https://developer.nylas.com/docs/cookbook/use-cases/build/google-oauth-scopes/)). Forwarding avoids this |
| Bank data feeds | India Account Aggregator, UAE AlTareq, open banking elsewhere | Highest, includes history | Needs licensed partners; country by country |
| Statement import | Monthly PDF/CSV upload or paste; duplicate check skips rows already captured | Medium (monthly) | User effort once a month; good as a "catch-all" |
| Phone automation | iPhone Shortcuts or Android automation apps forward bank messages to the app | Medium | User must set it up; not every user will |
| Default SMS app role | The app becomes the user's SMS app, which the policy permits | High | Must build a full messaging app; few users will switch |
| Receipt scan and voice entry | Photo or "spent 40 dirham on taxi" | Low–medium | For cash and small purchases |

**Recommended stack:** notification listener for real-time capture, email forwarding for e-statements and alerts, and monthly statement import as the safety net, with the duplicate check (see Global design) merging all three. Add bank data feeds when partners are signed. Apply for SMS permission anyway; if approved, it becomes one more source in the same pipeline.

## Module 2: Multi-currency engine

The app stores every transaction in its original currency and converts to the user's chosen home currency only for display, using the rate of the transaction date.

**Key facts for the three currencies:**

- **AED and USD are pegged** at 3.6725 AED per USD, so USD↔AED conversion is nearly fixed. Central Bank of UAE data showed USD/AED at 3.6725 in June 2026 ([cbonds, CBUAE rates](https://cbonds.de/indexes/216669/)).
- **INR floats.** The same CBUAE data showed INR/AED at 0.03885 in June 2026, about INR 25.7 per AED, or roughly INR 94.5 per USD ([cbonds, CBUAE rates](https://cbonds.pl/indexes/216645/)). So the main currency risk is INR vs AED/USD.
- When INR weakens, the same AED salary buys more in India, but INR investments are worth less in AED. The app must show both views.

**Data model (per transaction):** original amount, original currency, rate used, rate source, date, converted amount in home currency.

**Exchange-rate sources:** use one free daily-rate API for history (e.g. a free ECB-based API) plus the CBUAE published rates for AED. Cache rates on the phone so the app works offline.

**Remittance cost tracker (a strong feature):** when a transfer SMS is detected (AED debited in UAE, INR credited in India), the app calculates the true cost.

```latex
\text{Total cost} = \text{Fee} + \text{AED sent} \times \left(1 - \frac{\text{Rate received}}{\text{Market rate}}\right)
```

Example: send AED 5,000 with an AED 15 fee. Market rate is 25.70 INR/AED; you receive 25.45. The markup loss is 5,000 × (1 − 25.45/25.70), about AED 48.6. Total cost is about AED 63.6, or 1.3% of the transfer. Over 12 months that is about AED 760 a year — money the simulator can show as an investment instead.

## Global design: statement import, duplicates and any home currency

Anyone can use the app: the user picks a home currency (for example INR), each bank account keeps its own currency, and every import goes through one duplicate check so nothing is counted twice.

**Ways to bring data in (works in every country):**

| Method | How it works | Platforms |
| --- | --- | --- |
| Paste text | Copy statement lines or SMS and paste into the app; the parser reads each line | Android, iOS, web |
| Upload a file | PDF, CSV, Excel, OFX/QIF statements; password-protected PDFs unlocked on the phone | Android, iOS, web |
| Bank SMS | Read automatically after permission | Android only |
| Bank data feeds | Country by country: India Account Aggregator, UAE AlTareq, open-banking APIs elsewhere | Later phases |
| Manual entry | For cash and anything missing | All |

**Accounts.** Each account stores bank, country, currency, and type (savings, current, credit card, NRE/NRO, brokerage, wallet, loan). One user can hold, say, an INR savings account, an AED salary account, a USD card and a GBP account together.

**Why duplicates happen.** The same purchase can arrive as a card SMS, a bank SMS, a line in the bank statement, and a line in the credit card statement. A foreign purchase may show USD 50 in the SMS but AED 189.40 in the statement (converted, plus fee). A card hold can differ from the final amount.

&#91;embedded content: duplicate check · 4 outcomes\]

**How the match score works:**

| Signal | Rule | Weight |
| --- | --- | --- |
| Same account | Same account, or the card linked to it | Required |
| Amount | Equal, or equal after currency conversion within a small tolerance (fees, card markup) | High |
| Date | Within 0–3 days (posting delays) | High |
| Reference | Same UPI/RRN/reference number, or same last 4 card digits | Very high |
| Merchant | Similar names after cleaning ("AMZN MKTP" = "Amazon") | Medium |
| Source | Different sources (SMS vs statement) raise the chance it is the same item | Medium |

A pasted or uploaded statement that overlaps an earlier import is safe: rows already matched are skipped, and the app shows "42 new, 118 already imported". When records merge, the app keeps the most complete fields (exact final amount from the statement, merchant from the SMS) and lists every source, so the user can undo a wrong merge.

**Transfers between your own accounts.** A debit in one account and a matching credit in another (for example AED 5,000 out of a UAE account and about INR 127,000 into an NRE account two days later) are linked as one transfer, not spending plus income. The currency difference becomes the remittance cost from Module 2.

**Home currency and dynamic conversion.**

- The user chooses any home currency and can change it at any time; nothing is lost, because originals are always stored.
- Each transaction shows: original amount, home-currency value on the transaction date (for spending history), and value at today's rate (for net worth).
- An optional second display currency (e.g. show INR and AED side by side).

**Travel mode.** When transactions appear in a new currency, or the user starts a trip, the app opens a trip budget in home currency. It shows each foreign charge in home currency, the card's exchange markup versus the market rate, and a trip total at the end.

**Investments in other countries.** Holdings stay in their own currency; the app shows value in home currency and splits the return into asset growth and currency effect.

```latex
\text{Return in home currency} = (1 + \text{asset return}) \times (1 + \text{currency change}) - 1
```

Example: a US stock gains 10% in USD while USD rises 3% against INR; for an INR-home user the gain is 1.10 × 1.03 − 1 = 13.3%.

**Going global: "country packs".** Each country added needs: SMS and statement formats for its main banks, a bank-feed option where one exists, local investment presets for the simulator (local stocks, foreign stocks, property, deposits, loans), privacy rules (for example GDPR in Europe), and language. Start with India and the UAE, then add countries with large expatriate communities.

## Module 3: Expense analytics and savings detection

The analytics module turns parsed transactions into a monthly picture and finds "leak" money that could be redirected to investment.

**Categories (start with these, user can edit):** salary and income, rent and housing, groceries, food delivery and dining, transport and fuel, utilities and phone, school fees, shopping, subscriptions, EMIs and loans, credit card bill, remittance to India, investments, family support in India, other.

**Dashboards:**

- Monthly income vs spending vs saving, in home currency.
- Spending split by country (UAE vs India) and by currency.
- Savings rate = (income − spending) ÷ income.
- Net worth across both countries: bank balances, investments, property, minus loans.

**Automatic "leak" detectors:**

| Detector | Rule | Example insight |
| --- | --- | --- |
| Subscriptions | Same merchant, similar amount, every \~30 days | "You pay for 3 streaming services: AED 110/month" |
| Food delivery | Delivery-app merchants above a monthly threshold | "AED 1,150 on delivery this month, up 40%" |
| Card fees and interest | SMS mentions fee, interest, late charge, FX markup | "AED 92 in card fees and foreign-currency charges" |
| Remittance cost | Formula from Module 2 | "Transfers cost you 1.3%; cheaper option saves \~AED 400/yr" |
| Idle cash | Balance stays high for 3+ months | "AED 30,000 sitting idle in a 0% current account" |
| EMI load | Total EMIs ÷ income | "EMIs take 38% of income; 30–40% is a common lender ceiling" |

Each insight ends with one button: **"What if I invest this?"**, which opens Module 4 with the amount pre-filled.

## Module 4: "What if" investment simulator

The simulator takes an amount found in Module 3 and projects it across five paths, always in the user's home currency and with currency change included.

**Path A — Indian stocks and mutual funds (Groww and similar).** Groww now opens NRI accounts on the Non-PIS NRO route, covering stocks, F&O, mutual funds, ETFs and IPOs, but not margin trading or commodities ([Groww NRI page](https://groww.in/open-nri-demat-account)). Repatriable stock investing from an NRE account normally needs the RBI's Portfolio Investment Scheme (PIS); mutual funds do not need PIS ([Motilal Oswal, 2026](https://www.motilaloswal.com/learning-centre/2026/3/nri-demat-account-regulations-in-2026-key-changes-to-watch)). The app should show which route the user is on, because it decides whether money can go back to the UAE freely.

**Path B — International stocks via IBKR.** For a UAE resident, USD investing has no currency risk against AED because of the peg. The simulator uses USD returns directly. Interactive Brokers offers a public API (details in Integrations).

**Path C — Land and property in India.** NRIs may buy residential and commercial property and non-agricultural plots, and can take Indian home loans, but cannot buy agricultural land, plantation property or farmhouses ([Housing.com](https://housing.com/news/can-nri-purchase-property-india/), [Assetly, FEMA rule](https://assetlyhq.com/blog/can-nri-buy-agricultural-land-india-fema/)). The app must warn when a user tags a property as "farm" or "agricultural". Model inputs: price, down payment, loan rate and tenure, stamp duty and registration, yearly price growth, rent, maintenance, and TDS on sale.

**Path D — EMI products.** Compare "buy now on EMI" with "save first, then buy". Show total interest and processing fees, and flag "no-cost EMI" offers where the discount is lost.

**Path E — Do nothing / bank deposit.** The baseline every other path is compared against.

**Formulas:**

```latex
FV_{SIP} = P \times \frac{(1+r)^n - 1}{r} \times (1+r)
```

```latex
EMI = L \times \frac{r(1+r)^n}{(1+r)^n - 1}
```

P = monthly amount, L = loan amount, r = monthly rate, n = number of months. For INR assets shown in AED, the yearly return in AED ≈ (1 + INR return) ÷ (1 + yearly INR fall vs AED) − 1.

**Example: AED 1,000 a month for 10 years (AED 120,000 put in).** Illustrative assumptions only, not forecasts.

| Path | Assumed yearly return (in AED) | Value after 10 years (AED) |
| --- | --- | --- |
| US index fund via IBKR | 10% (USD, pegged) | \~206,600 |
| Indian equity mutual fund | 12% in INR, minus \~3%/yr INR fall → \~8.7% | \~191,600 |
| AED fixed deposit | 4% | \~147,700 |
| Cash in current account | 0% | 120,000 |

**EMI example:** an INR 10 lakh loan at 9% for 5 years costs about INR 20,758 a month, or INR 12.46 lakh in total — INR 2.46 lakh in interest. The app shows that interest figure next to what the same EMI would grow to if invested.

Rules for the simulator: show a range (low / middle / high), never a single promised number; show the effect of currency; show fees and taxes; label everything "illustrative".

## Integrations

Start with read-only data and manual imports; live broker links need partner approval and come later.

| Integration | What it gives | Access route | Effort |
| --- | --- | --- | --- |
| Bank SMS (Android) | Live transactions, all banks | READ\_SMS after Google Play review | Low–medium |
| India Account Aggregator | Bank statements, deposits, mutual funds, insurance | Join as FIU or partner with a licensed FIU; integrate through an AA such as Setu or Anumati | Medium–high |
| UAE AlTareq Open Finance | UAE bank account data | Only via a CBUAE-licensed provider (e.g. Pay10) | High, early market |
| [IBKR Web API](https://www.interactivebrokers.com/campus/ibkr-api-page/webapi-doc/) | Positions, balances, performance, transactions | Third-party OAuth 1.0a, after IBKR Compliance due diligence (estimated 3–6 weeks) | Medium |
| IBKR Flex Web Service | Daily statements as XML/CSV | User creates a token and query; app pulls the report | Low (good for MVP) |
| [Groww Trading API](https://docs.openalgo.in/connect-brokers/brokers/groww) | Holdings, orders, market data | Each user generates their own key; subscription about INR 499/month ([AlgoTest](https://docs.algotest.in/broker/groww/)) | Not suitable for mass users |
| Mutual fund CAS (CAMS/KFintech) and CDSL/NSDL statements | All Indian MF and demat holdings | User uploads the PDF; app parses it | Low (good for MVP) |
| Exchange rates | Daily FX history | Free API + CBUAE published rates | Low |

**IBKR detail.** IBKR treats an app reading other people's accounts as a "third-party vendor"; vendors may only use OAuth 1.0a and need Compliance approval first. Vendors offering automated trading are expected to hold the right financial registration in each region served ([IBKR Web API docs](https://www.interactivebrokers.com/campus/ibkr-api-page/webapi-doc/)). So: read-only portfolio sync, no trading from the app.

**Groww detail.** Groww's API is built for a person trading their own account, not for third-party apps. The practical route for Indian holdings is CAS statement upload now, and Account Aggregator later.

### Screenshot import: any investment app

A user can upload a screenshot of the holdings screen from any app — Groww, IBKR, Zerodha, a bank app, a crypto exchange, a PF passbook — and the app turns it into holdings. This needs no partner, API or licence, so it works in every country from day one (Phase 2).

**How it works:**

1. User takes one or more screenshots of the holdings or portfolio screen (or one long scrolling screenshot).
2. On-device text recognition reads the text (Google ML Kit on Android, Apple Vision on iPhone).
3. An AI model maps the text to fields: name or ticker, quantity, average price, current value, profit or loss, currency.
4. The app matches each name to a known stock, fund or ETF so prices can update later.
5. A confirm screen shows what was read; the user fixes anything wrong in one tap.
6. Holdings are saved with the source app and date; the next screenshot updates them, and the duplicate check stops double counting with CAS or broker imports.

| Challenge | Fix |
| --- | --- |
| Only part of the list is visible | Allow several screenshots or a long scrolling screenshot; merge them |
| Short forms like "₹1.2L" or "$3.4K" | Rules that expand lakh, crore, K, M |
| "$" can mean USD, CAD, AUD, SGD | Use the source app's country, ticker exchange, or ask once |
| Hidden values (eye icon) | Detect masked numbers and ask the user to unhide |
| Screenshot is only a snapshot | Show "as of" date; refresh prices from market data where the ticker is known; remind monthly to re-upload |
| Account numbers or names on screen | Blur or crop on the phone before any AI step; never store the image after reading |

**Value:** it is the fastest way to cover apps with no API (like Groww for third parties) and countries with no bank-data feeds, and it turns a one-minute task into a complete multi-country net worth.

## Regulatory, tax and privacy

The safe position is: an education and tracking app that shows scenarios, never personal buy/sell advice, and that keeps financial data on the phone where possible. Get a lawyer's review in both countries before launch.

**Investment advice (India).** SEBI requires Research Analyst or Investment Adviser registration to give stock recommendations or investment advice ([Business Standard](https://www.business-standard.com/markets/news/finfluencers-feel-the-heat-as-market-regulator-sebi-crackdown-looms-124071201160_1.html)). Since January 2025, regulated entities such as brokers and mutual funds may not partner with unregistered persons who give advice or claim returns ([Mondaq](https://webiis08.mondaq.com/india/securities/1726258/sebis-crackdown-on-finfluencers-regulations-and-enforcement)). SEBI also published a draft common advertisement code for investing platforms on 23 June 2026 ([LoansJagat](https://www.loansjagat.com/news/what-is-sebis-new-common-advertisement-code-how-does-it-affect-investing-apps-in-2026)). For this app that means:

- Allowed: "AED 1,000 a month at an assumed 10% would be \~AED 206,600 in 10 years."
- Not allowed without registration: "Buy fund X" or "Sell stock Y now."
- Affiliate links to brokers are risky unless the advice line is kept clean. A later "advice" tier needs a SEBI-registered partner.

**Advice and finance in the UAE.** Financial advice and data-sharing services are licensed activities (SCA / CBUAE). Use the same "scenarios only" rule, and use AlTareq only through a licensed partner.

**Data privacy.**

| Law | Key dates | What it means for the app |
| --- | --- | --- |
| India DPDP Act 2023 + DPDP Rules 2025 | Rules notified 13 Nov 2025; consent-manager rules from Nov 2026; core duties from 13 May 2027 ([Mondaq](https://webiis08.mondaq.com/india/data-protection/1706878/indias-digital-personal-data-protection-act-phased-rollout-and-key-compliance-milestones)) | Clear consent notice, purpose limits, deletion on request, breach reporting, data retention limits |
| UAE Federal Decree-Law 45/2021 (PDPL) | In force; check status of executive regulations before launch | Consent, data-subject rights, cross-border transfer rules |
| Google Play SMS policy | Ongoing | Declaration form; SMS data only for the core budget feature |

**Tax features (information only).**

- UAE has no personal income tax on salary; India taxes NRIs on income earned in India (interest on NRO, rent, capital gains).
- Brokers deduct TDS on NRI capital gains; property buyers deduct TDS when an NRI sells.
- NRE interest is tax-free in India; NRO interest is taxable.
- Residency status depends on days spent in India each year; the app can count days from travel entries and warn when close to the limit.
- The India–UAE tax treaty (DTAA) can reduce double taxation; the app should link to it, not interpret it.

Every projection screen should carry a short disclaimer: illustrative only, not investment, tax or legal advice; past returns do not guarantee future returns.

## Tech architecture and stack

The app is "local-first": SMS parsing, categories, currency conversion and projections run on the phone; the cloud is optional and only stores encrypted data.

&#91;embedded content: app architecture · 3 layers\]

Raw SMS never leaves the device; only parsed transactions move, and only if the user turns on sync.

| Layer | Suggested choice | Why |
| --- | --- | --- |
| Mobile app | Flutter (one codebase for Android and iOS) or Kotlin for Android-first | SMS reading is Android-only; Flutter keeps iOS cheap later |
| Local database | SQLite with SQLCipher encryption | Works offline, encrypted at rest |
| Parsing | Regex templates per bank sender + small AI model for unknown formats | Fast and private for known banks, flexible for new ones |
| Backend (optional) | Node.js or Python (FastAPI) + PostgreSQL | Sync, rates cache, partner APIs |
| Charts | fl\_chart (Flutter) or MPAndroidChart | Native, smooth on low-end phones |
| Auth and security | Phone/email login, biometric app lock, end-to-end encrypted backup | Finance data needs strong protection |
| Hosting | A UAE or India cloud region | Helps with data-residency questions under PDPL/DPDP |

## Future features: the full vision

The long-term app is a "money home" for anyone living across countries: capture everything, understand it in one currency, and plan the future. The Phase column matches the Roadmap below.

| Area | Feature | What it does | Phase |
| --- | --- | --- | --- |
| Capture | Bank SMS reading | Auto-capture on Android | 1 |
| Capture | Paste text | Paste statement lines or SMS from any bank | 1 |
| Capture | Statement upload | PDF, CSV, Excel, OFX; password PDFs unlocked on the phone | 2 |
| Capture | Receipt photo scan | Reads amount, shop and date from a photo | 2 |
| Capture | Voice entry | "Spent 40 dirham on taxi" becomes a transaction | 3 |
| Capture | Email forwarding | Forward e-statements and bills to a private app address | 3 |
| Capture | Bank data feeds | India AA, UAE AlTareq, open banking in other countries | 3–4 |
| Understand | Duplicate check and transfer matching | One record per real transaction; own-account transfers linked | 1–2 |
| Understand | AI categories | Learns from the user's corrections | 1 |
| Understand | Subscriptions and bills calendar | Recurring payments, EMIs and due dates in one calendar | 2 |
| Understand | Unusual-debit alerts | Flags an odd amount, merchant or country | 3 |
| Understand | Split expenses | Share costs with roommates, friends, family | 3 |
| Currency | Any home currency + second display currency | View in INR, AED or any currency; switch any time | 2 |
| Currency | Travel mode | Trip budget, card markup check, trip summary | 2 |
| Currency | Rate alerts | Notify when the rate for sending money home is good | 4 |
| Currency | Remittance comparison | Rank providers by total cost (fee + rate) | 3 |
| Invest | Holdings in many countries | Stocks, funds, ETFs with value in home currency | 2 |
| Invest | Return split | Asset growth vs currency effect | 2 |
| Invest | Imports | Mutual fund CAS, IBKR Flex, broker statements | 2 |
| Invest | Gold, deposits, retirement accounts | Gold, FDs, PF/NPS and similar, plus crypto (optional) | 3 |
| Invest | Property and land | Price, loan, rent, costs; warning on farmland for NRIs | 3 |
| Invest | UAE end-of-service gratuity | Estimate of gratuity from salary and years of service | 3 |
| Plan | What-if simulator | SIP, lump sum, EMI vs cash, rent vs buy | 1–2 |
| Plan | Goals | House, education, wedding, emergency fund, return home | 2 |
| Plan | Retirement and return-home planner | How much is needed to move back, and when | 3 |
| Plan | Debt payoff planner | Order of paying off cards and loans, with dates | 3 |
| Tax | Residency day counter | Days spent in each country vs tax-residency limits | 4 |
| Tax | Yearly reports | Capital gains, interest income, foreign assets summary | 4 |
| Family | Household view | UAE earner and India family see shared budgets | 3 |
| Family | Emergency vault | Accounts, policies, nominees for family in an emergency | 4 |
| AI | Monthly money letter | Plain-language summary of the month | 2 |
| AI | Ask your money | "How much did I spend on travel this year?" | 3 |
| AI | Money coach | Scenarios and habits, never stock tips | 4 |
| Advice | Regulated advice tier | Paid advice through a licensed adviser partner | 4 |
| Platform | Web dashboard, widgets, smartwatch | Same data on every screen | 3 |
| Platform | Languages | English, Hindi, Malayalam, Tamil, Arabic, then more | 4 |
| Platform | Country packs | Bank formats, presets and rules per new country | 4 |
| Platform | Data export and delete | Full export any time; delete account and data | 1 |

## Roadmap

Build the Android SMS tracker and calculator first (about 3 months); bank feeds and broker sync come only after partners and legal review are in place.

&#91;embedded content: roadmap · 4 phases, 3 gates\]

Each phase starts only when its gate is passed; if Google Play refuses SMS access, Phase 2's statement imports move up to Phase 1.

**First steps this month:**

- [ ] Collect 50+ real bank SMS samples (masked) from UAE and Indian banks
- [ ] Write parsers and test them on the samples
- [ ] Build the calculator screens (SIP, EMI, currency)
- [ ] Draft the privacy policy and the Google Play SMS declaration
- [ ] Book a short legal review on the "scenarios, not advice" wording

## Competitors, business model and risks

Indian expense trackers are INR-first and UAE apps are AED-first; the gap is a cross-border NRI view with remittance cost and investment "what if".

| App | Approach | Multi-currency / NRI | Gap this app fills |
| --- | --- | --- | --- |
| [Axio (formerly Walnut)](https://getfinny.app/blog/sms-expense-tracking-app) | SMS parsing, Android; now also lending and FDs | INR-focused | AED/USD, remittance cost |
| [Fold](https://investor-toolkit.pages.dev/free-ai-expense-trackers-india.html) | Account Aggregator bank link | INR-focused | UAE side, SMS for UAE banks |
| [ET Money](https://getfinny.app/blog/best-expense-tracker-apps-india-2026) | Expenses + direct mutual funds | INR-focused | International investing, property |
| INDmoney | Net worth, Indian + US stocks | Partly | UAE bank data, remittance tracking |
| UAE bank apps (ENBD, ADCB, FAB) | Own-bank spending insights | AED only, one bank | Cross-bank, cross-country view |

**Global apps checked (November 2026).** No single app combines bank SMS, statement duplicate removal, any home currency, NRI rules and an investment "what if". Many review sites below are written by competing app makers, so treat rankings with caution.

| App | Strength | Missing compared with this app |
| --- | --- | --- |
| [Wallet by BudgetBakers](https://freenance.io/financial-tools/best-expense-tracking-apps/) | Multi-currency; automatic bank sync in Europe | No SMS; no remittance or NRI features |
| [Spendee](https://getfinny.app/blog/best-multi-currency-expense-tracking-apps-2026) | Shared multi-currency wallets | No SMS; limited investments |
| Toshl | Multi-currency, good for travel | No SMS; no investment simulator |
| [Lunch Money](https://getfinny.app/blog/lunch-money-review-2026) | Net worth across banks, investments, crypto, manual assets | Bank sync built around US aggregators; no SMS |
| [NomadMetrics](https://mwm.ai/apps/nomadmetrics-expense-tracker/6767209647) | Multi-currency tracker for expats and travelers | No investment simulator or remittance cost |
| [Richify](https://www.richify.ai/best/net-worth-trackers) | Markets multi-currency net worth with AI what-if questions | Spending capture not its focus |
| Kubera, Sharesight | Portfolio tracking across countries and currencies | No daily spending |
| [Empower, Monarch, Copilot](https://www.richify.ai/best/net-worth-trackers) | Strong US apps | Single currency (USD) |

**Revenue options (choose ones that keep the "no advice" line clean):**

- Freemium subscription: free tracker; paid tier for net worth, simulator, multi-device sync, family sharing (e.g. AED 15–25 a month).
- Remittance comparison referral fees from licensed exchange houses — show all options ranked by total cost, not by commission.
- B2B: white-label tracker for UAE exchange houses or banks that serve Indian customers.
- Later: a SEBI-registered adviser partner offering paid advice inside the app, clearly separated.

### Pricing: one-month free trial, then a low price

Every new user gets 30 days of the full app free, then chooses a low-cost Premium plan or stays on a free Basic plan. Low prices suit the target users (many earn modest salaries and send most of it home) and make the trial-to-paid step easy.

| Plan | What's included | Price idea |
| --- | --- | --- |
| Free trial (30 days) | Everything in Premium | Free; reminder 3 days before it ends |
| Basic (free forever) | Manual entry, paste import, 2 accounts, monthly dashboard, 3 months of history | Free |
| Premium | Unlimited accounts and currencies, SMS/notification/email capture, statement and screenshot import, duplicate check, investment tracking, what-if simulator, goals, travel mode, full history, export | India ₹99/month or ₹799/year · UAE AED 9.99/month or AED 79/year · USA/Europe USD 2.99/month or USD 24.99/year |
| Family (later) | Premium for up to 4 people, shared household budget | About 1.5× Premium |

Price by country (the stores support local prices), and push the yearly plan: it is about 30% cheaper for the user and gives the app cash up front with fewer cancellations.

**What the app keeps.** On Google Play, subscriptions carry an effective fee of about 15% (10% service plus 5% billing in the US, UK and EEA after June 2026); Apple charges 15% for Small Business Program members ([PricePush](https://pricepush.app/glossary/service-fee)). So a USD 2.99 plan leaves about USD 2.54 before taxes.

**Example year-one revenue (illustrative assumptions only):** 5,000 new trial users a month, average price about USD 2 a month, 15% store fee, 5% of paying users cancel each month.

| Trial-to-paid conversion | Paying users after 12 months | Net revenue per month at month 12 | Net revenue in year one |
| --- | --- | --- | --- |
| 5% | \~2,300 | \~USD 3,900 | \~USD 28,000 |
| 10% | \~4,600 | \~USD 7,800 | \~USD 56,000 |

**Ways to raise trial-to-paid conversion:**

- Show value in week one: a "your first week" summary with one real saving found (a subscription, card fees, remittance cost).
- Make the trial end screen personal: "In 30 days we tracked 3 currencies, 214 transactions and found AED 340 you could save."
- Keep Basic useful but limited, so people stay and upgrade later instead of deleting.
- Referral offer: one free month for both people.
- Never lock a user out of their own data; export stays free.

**Extra revenue that keeps the price low:** remittance-provider referrals (ranked by total cost, not by commission), B2B white-label for exchange houses and banks, and later a paid advice tier through a licensed partner.

**Main risks and fallbacks:**

| Risk | Impact | Fallback |
| --- | --- | --- |
| Google Play rejects SMS permission | No auto-capture on Android | Notification-listener import, SMS share, statement upload, AA |
| Bank SMS formats change | Parsing breaks | AI parser for unknown formats + user correction loop |
| Seen as unregistered advice | SEBI / UAE action | Scenarios only, legal review, registered partner for advice |
| Data breach | Loss of trust, fines under DPDP/PDPL | On-device processing, encryption, store no raw SMS |
| Low trust in a new finance app | Slow growth | Open privacy policy, offline mode, community in UAE Indian groups |

## Sources

Return figures in Module 4 are illustrative assumptions, not sourced forecasts. Laws and platform rules change; recheck before launch.

- [Indian Embassy UAE — India–UAE economic relations](https://www.indembassyuae.gov.in/page/bilateral-economic-and-commercial-relations/)
- [Gulf News — UAE–India money transfers (RBI remittance data)](https://gulfnews.com/gn-focus/how-digital-integration-and-exchange-rates-boost-uae-india-money-transfers-1.500425616)
- [Google Play — SMS and Call Log permissions policy](https://support.google.com/googleplay/android-developer/answer/10208820?hl=en)
- [Bluecoins — removing SMS permissions](https://bluecoinsapp.com/?p=9286)
- [Sahamati — Account Aggregator statistics, June 2025](https://sahamati.org.in/?p=1269258)
- [Facephi — Open Finance in the UAE (AlTareq, Nebras)](https://facephi.com/observatory/en/open-finance-eau-2026/)
- [cbonds — Central Bank of UAE exchange rates](https://cbonds.de/indexes/216669/)
- [Groww — NRI demat account](https://groww.in/open-nri-demat-account)
- [Motilal Oswal — NRI demat regulations 2026](https://www.motilaloswal.com/learning-centre/2026/3/nri-demat-account-regulations-in-2026-key-changes-to-watch)
- [Housing.com — Can an NRI buy property in India](https://housing.com/news/can-nri-purchase-property-india/)
- [Assetly — NRIs and agricultural land under FEMA](https://assetlyhq.com/blog/can-nri-buy-agricultural-land-india-fema/)
- [IBKR — Web API documentation (third-party access)](https://www.interactivebrokers.com/campus/ibkr-api-page/webapi-doc/)
- [OpenAlgo — Groww trading API](https://docs.openalgo.in/connect-brokers/brokers/groww)
- [AlgoTest — Groww API pricing](https://docs.algotest.in/broker/groww/)
- [Mondaq — DPDP Act phased rollout](https://webiis08.mondaq.com/india/data-protection/1706878/indias-digital-personal-data-protection-act-phased-rollout-and-key-compliance-milestones)
- [Mondaq — SEBI crackdown on finfluencers](https://webiis08.mondaq.com/india/securities/1726258/sebis-crackdown-on-finfluencers-regulations-and-enforcement)
- [Business Standard — SEBI registration for advice](https://www.business-standard.com/markets/news/finfluencers-feel-the-heat-as-market-regulator-sebi-crackdown-looms-124071201160_1.html)
- [LoansJagat — SEBI draft advertisement code 2026](https://www.loansjagat.com/news/what-is-sebis-new-common-advertisement-code-how-does-it-affect-investing-apps-in-2026)
- [Finny — SMS expense tracking apps](https://getfinny.app/blog/sms-expense-tracking-app)

* [Freenance — best expense tracking apps](https://freenance.io/financial-tools/best-expense-tracking-apps/)
* [Finny — best multi-currency expense tracking apps 2026](https://getfinny.app/blog/best-multi-currency-expense-tracking-apps-2026)
* [Finny — Lunch Money review 2026](https://getfinny.app/blog/lunch-money-review-2026)
* [NomadMetrics app listing](https://mwm.ai/apps/nomadmetrics-expense-tracker/6767209647)
* [Richify — net worth trackers compared](https://www.richify.ai/best/net-worth-trackers)
