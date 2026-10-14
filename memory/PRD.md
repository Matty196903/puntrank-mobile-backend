# PuntRank Aus — PRD

## Original problem statement
Build "PuntRank Aus" — full-stack WEB app (target: www.puntrank.com.au). Web version of an existing Expo mobile app (React Native + FastAPI + MongoDB) with same features/design, shared backend + MongoDB so accounts, Pro status and payments sync with mobile. Mobile-first form-analysis tool for Australian thoroughbred racing: today's meetings (Australia/Sydney), ranked runners with win/place probabilities + confidence + plain-English reasoning, Ace's 60-year selections (Winners/Places/Quaddies), exotics + cross-race multis, market movers/plunges, pin favourites + bet slip, A-Grade best bets graded live, results tracking & daily strike-rate, auto-generated PDFs, admin panel. Integrations: Punting Form API (user will supply key), Stripe LIVE web checkout (Monthly A$9.99, Annual A$49.99 recurring, Lifetime A$99 one-off) → webhook sets is_pro. 18+ / gamble responsibly compliant.

## User personas
- Punter (guest): browses rankings, limited free data
- Free account: same as guest, can upgrade to Pro
- Pro subscriber: full reasoning, all A-Grade bets, exotics, quaddies, all PDFs
- Admin: reseed data, manage users, grant/revoke Pro

## Architecture
- FastAPI (port 8001, /api prefix) + MongoDB (motor) + React 19 (CRA/craco, Tailwind, shadcn)
- backend/server.py (routes), engine.py (seed + ranking engine), pdf_reports.py (reportlab)
- Auth: JWT (Bearer + httpOnly cookie), bcrypt, brute-force lockout, admin seeded on startup
- Stripe: Emergent claimable sandbox (test mode) — prices by lookup_key: pro_monthly (A$9.99/mo), pro_annual (A$49.99/yr), pro_lifetime (A$99 one-off), all AUD. Webhook POST /api/stripe/webhook + status-poll fallback GET /api/payments/status/{id}; both grant is_pro. Tax mode: Stripe managed payments (full).
- "Today" computed in Australia/Sydney (zoneinfo)
- Racing data: LIVE via Punting Form API v2 (api.puntingform.com.au, key in PUNTING_FORM_API_KEY env). backend/pf_client.py fetches meetingslist + fields per AEST day, ranks runners via form-based scoring (winPct, placePct, last10, distance/track records, barrier, weight), syncs official results (throttled 3 min) to grade top picks. Mock engine.py remains as automatic fallback if PF is unreachable.

## Implemented (2026-06 update 2)
- Punting Form live data integration (pf_client.py): real AUS TAB meetings, races, runners, official results grading; timezone-safe AEST time display on frontend (lib/time.js)

## Implemented (2026-06 first build)
- 18+ age gate (localStorage) + persistent gamble-responsibly footer
- Auth: register/login/logout/me, guest mode, admin seeding, brute-force protection
- Meetings → races → runners: rankings, win/place %, confidence, reasoning, form, plunge flags
- Pro gating: free users see top-3 reasoning only, 1 exotic, 2 Ace's winners, 1 A-Grade bet
- Ace's selections: Winners / Places / feature-meeting Quaddie (4 legs)
- Exotics: exacta, quinella box, trifecta box, first four box w/ cost + est return
- A-Grade best bets graded live (WON/PLACED/UNPLACED) + cross-race multis (double/treble)
- Market movers / plunges with move % and pulse UI
- Results + daily win/place strike rates
- Pin favourites + bet slip drawer with unit staking calculator (localStorage)
- 6 PDF reports (reportlab): form guide, top10 (free); results wrap, scorecard, staking calc, quaddie ticket (Pro)
- Stripe checkout + webhook + polling fallback → is_pro in users collection
- Admin panel: reseed, user list, toggle Pro
- Testing: 27/27 backend pytest + full Playwright frontend pass (iteration_1)

## Implemented (2026-06 update 3)
- Password reset: POST /api/auth/forgot-password (Emergent-managed Resend email, generic anti-enumeration response, origin allowlist) + /api/auth/reset-password (1h TTL, single-use); frontend forgot mode on AuthPage + /reset-password page
- Free quaddie teaser: guests see leg 1 of Ace's quaddie, ProLock for remaining 3
- Share button on meetings page (navigator.share + clipboard fallback) sharing /guide + today's top pick
- /guide "How it works" page with A/B/C ratings explained; header help icon
- Deployment readiness: PASS (fixed destructive startup deletes — now only in admin reseed; batched N+1 queries; PF results sync moved to background task)
- Testing: iteration_3 100% pass (31/31 backend + all frontend flows)

## Implemented (2026-06 update 3b — mobile parity alignment)
- Tabs restructured: Racing / Market / Exotics / Results / Account (old routes kept as aliases)
- New ExoticsPage (race exotics browser + best-bet shortlist + multis), new AccountPage (profile, subscription, legal links)
- Racing home: "Next to Jump" strip + "Ace's Exotics" / "A-Grade Plays" cards; pages renamed to match mobile
- Routes /pay-success and /pay-cancel added; /auth/me + login already return is_pro + pro_plan
- Pending: user will share GitHub repo with server.py (5325 lines) + pdf_reports.py (1508 lines, WeasyPrint HTML-in-Python, 20 build_*_html fns, NO Jinja2 templates) → merge as-is, switch PDFs fully to WeasyPrint, add /api/guide/*.pdf + /api/billing/config + /api/stripe/* routes. Stripe stays on claimed puntrank-web account. Krok Odds key pending.

- Welcome email on sign-up (branded, today's top pick card, guide CTA), branded reset email, metro-only toggle (meeting.location M/P/C from PF), live next-to-jump countdown (lib/time.js useNow/minsToJump), admin payments view (/api/admin/payments)

## Backlog / remaining
- P0: User pastes existing backend export (server.py, pdf_reports.py, models, Stripe price IDs) → merge/reconcile so mobile app shares this DB
- P1: Deploy to production + custom domain www.puntrank.com.au; user must claim Stripe sandbox + KYC for live payments
- P1: Password reset flow (forgot password email)
- P2: Speed maps / track bias visuals, Recharts strike-rate history graph
- P2: Subscription cancellation handling (customer.subscription.deleted webhook → revoke is_pro for recurring plans)

## Credentials
See /app/memory/test_credentials.md (admin: admin@puntrank.com.au / AcePunter2026!)
