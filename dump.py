from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://gandalf.lakera.ai/baseline')
    page.wait_for_timeout(3000)
    with open('dump.html', 'w', encoding='utf-8') as f:
        f.write(page.content())
    browser.close()
