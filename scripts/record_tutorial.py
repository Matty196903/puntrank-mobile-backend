import time
from playwright.sync_api import sync_playwright

APP = "https://puntrank-web.preview.emergentagent.com"
marks = []


def mark(label):
    marks.append((label, time.time()))
    print(f"MARK {time.time():.1f} {label}")


with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                              record_video_dir="/app/video_out",
                              record_video_size={"width": 390, "height": 844})
    page = ctx.new_page()
    t0 = time.time()

    # Section 1: age gate + sign up
    page.goto(APP, wait_until="networkidle")
    mark("agegate")
    page.wait_for_timeout(2500)
    page.click('[data-testid="age-gate-confirm-btn"]')
    page.wait_for_timeout(1500)
    page.goto(APP + "/auth", wait_until="networkidle")
    mark("signup")
    page.wait_for_timeout(1000)
    page.click('[data-testid="auth-switch-mode"]')
    page.wait_for_timeout(800)
    email = f"demo{int(time.time())}@puntrank.demo"
    page.type('[data-testid="auth-name-input"]', "Demo Punter", delay=60)
    page.type('[data-testid="auth-email-input"]', email, delay=40)
    page.type('[data-testid="auth-password-input"]', "punter123", delay=60)
    page.wait_for_timeout(600)
    page.click('[data-testid="auth-submit-btn"]')
    page.wait_for_timeout(2500)

    # Section 2: meetings -> race card -> expand runner
    mark("meetings")
    page.wait_for_timeout(2500)
    page.locator('[data-testid^="meeting-card-"]').first.click()
    page.wait_for_timeout(2500)
    mark("runners")
    page.locator('[data-testid^="runner-expand-"]').first.click()
    page.wait_for_timeout(3000)
    page.mouse.wheel(0, 300)
    page.wait_for_timeout(2000)

    # Section 3: guide A/B/C grades
    page.goto(APP + "/guide", wait_until="networkidle")
    mark("grades")
    page.wait_for_timeout(1500)
    page.locator('[data-testid="guide-grade-A"]').scroll_into_view_if_needed()
    page.wait_for_timeout(2500)
    page.locator('[data-testid="guide-grade-C"]').scroll_into_view_if_needed()
    page.wait_for_timeout(2500)

    # Section 4: Ace's selections + quaddie
    page.goto(APP + "/aces", wait_until="networkidle")
    mark("aces")
    page.wait_for_timeout(2500)
    page.click('[data-testid="tab-quaddie"]')
    mark("quaddie")
    page.wait_for_timeout(3500)

    # Section 5: reports / download PDF
    page.goto(APP + "/reports", wait_until="networkidle")
    mark("reports")
    page.wait_for_timeout(2000)
    with page.expect_download(timeout=30000) as dl:
        page.click('[data-testid="report-download-form_guide"]')
    page.wait_for_timeout(2500)
    mark("downloaded")
    page.wait_for_timeout(2500)

    # Section 6: go pro
    page.goto(APP + "/pricing", wait_until="networkidle")
    mark("pricing")
    page.wait_for_timeout(3500)
    mark("end")

    ctx.close()
    browser.close()

print("OFFSETS")
for label, t in marks:
    print(f"{label}\t{t - t0:.1f}")
