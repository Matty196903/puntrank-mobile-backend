# Auth Testing Playbook — PuntRank Aus

## Credentials
- Admin: admin@puntrank.com.au / AcePunter2026! (role admin, is_pro true)
- Register test users freely via POST /api/auth/register

## Step 1: MongoDB verification
mongosh → use test_database
db.users.find({role: "admin"}).pretty()  # password_hash starts with $2b$
Indexes: users.email (unique), login_attempts.identifier

## Step 2: API testing
curl -c cookies.txt -X POST http://localhost:8001/api/auth/login -H "Content-Type: application/json" -d '{"email":"admin@puntrank.com.au","password":"AcePunter2026!"}'
curl -b cookies.txt http://localhost:8001/api/auth/me
# Token also returned in body as access_token — Bearer header supported.

## Notes
- Brute force: 5 failed logins per ip:email → 429 for 15 min
- Guest access: no auth needed for GET /api/meetings, /races, /movers, /results, /reports (free ones)
- Pro gating: non-pro users get truncated data on /api/best-bets, /api/selections/aces, /api/races/{id}/exotics, reasoning hidden for rank>3 runners
