from playwright.sync_api import sync_playwright

APP = "https://puntrank-web.preview.emergentagent.com"
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_context(viewport={"width": 390, "height": 844}).new_page()
    page.goto(APP + "/guide", wait_until="networkidle")
    page.click('[data-testid="age-gate-confirm-btn"]')
    page.wait_for_timeout(1500)
    page.goto(APP + "/guide", wait_until="networkidle")
    vid = page.locator('[data-testid="tutorial-video"]')
    vid.scroll_into_view_if_needed()
    page.wait_for_timeout(1200)
    print("video count:", vid.count())
    dur = page.evaluate("document.querySelector('[data-testid=\"tutorial-video\"]').duration || 0")
    print("video duration loaded:", dur)
    page.screenshot(path="/app/scripts/guide_video.png", quality=30, type="jpeg")
    b.close()
