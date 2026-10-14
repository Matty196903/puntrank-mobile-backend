from playwright.sync_api import sync_playwright

APP = "https://puntrank-web.preview.emergentagent.com"
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_context(viewport={"width": 390, "height": 844}).new_page()
    page.goto(APP, wait_until="networkidle")
    page.click('[data-testid="age-gate-confirm-btn"]')
    page.wait_for_timeout(2500)
    cds = page.locator('[data-testid^="jump-countdown-"]')
    print("countdown chips:", cds.count(), "first:", cds.first.inner_text() if cds.count() else "-")
    toggle = page.locator('[data-testid="metro-toggle"]')
    print("metro toggle:", toggle.count())
    before = page.locator('[data-testid^="meeting-card-"]').count()
    toggle.click()
    page.wait_for_timeout(500)
    after = page.locator('[data-testid^="meeting-card-"]').count()
    print(f"meetings before={before} after metro-only={after}")
    page.screenshot(path="/app/scripts/metro.jpg", quality=30, type="jpeg")
    b.close()
