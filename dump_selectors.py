from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://gandalf.lakera.ai/baseline')
    time.sleep(5)
    
    # send a dummy chat so guess input appears (if it's hidden)
    page.locator('textarea#comment').fill('Hello')
    page.locator('textarea#comment').press('Enter')
    time.sleep(5)
    
    inputs = page.locator('input').all()
    print("INPUTS:")
    for i in inputs:
        print(i.evaluate('el => el.outerHTML'))
        
    buttons = page.locator('button').all()
    print("\nBUTTONS:")
    for b in buttons:
        print(b.evaluate('el => el.outerHTML'))
        
    browser.close()
