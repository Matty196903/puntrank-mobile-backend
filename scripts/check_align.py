from playwright.sync_api import sync_playwright

APP = "https://puntrank-web.preview.emergentagent.com"
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844})
    page = ctx.new_page()
    page.goto(APP, wait_until="networkidle")
    page.click('[data-testid="age-gate-confirm-btn"]')
    page.wait_for_timeout(2500)
    for tid in ["nav-racing", "nav-market", "nav-exotics", "nav-results", "nav-account", "next-to-jump", "home-aces-card", "home-agrade-card"]:
        print(tid, page.locator(f'[data-testid="{tid}"]').count())
    page.screenshot(path="/app/scripts/home.jpg", quality=30, type="jpeg")
    page.click('[data-testid="nav-exotics"]')
    page.wait_for_timeout(2500)
    print("exotics cards:", page.locator('[data-testid^="exotic-card-"]').count())
    page.screenshot(path="/app/scripts/exotics.jpg", quality=30, type="jpeg")
    page.click('[data-testid="nav-account"]')
    page.wait_for_timeout(1500)
    print("account page:", page.locator('[data-testid="account-page"]').count())
    page.screenshot(path="/app/scripts/account.jpg", quality=30, type="jpeg")
    page.goto(APP + "/pay-cancel", wait_until="networkidle")
    print("pay-cancel redirects to:", page.url)
    b.close()
