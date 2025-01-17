# need to install:
# - pip install playwright
# - playwright install
# then you can use playwright
from time import sleep

from playwright.sync_api import sync_playwright


def takeScreen(targetUrl, savePath):
    with sync_playwright() as playwright:
        # Launch a browser
        browser = playwright.chromium.launch(headless=True)  # Set headless=False to see the browser
        # Open a new browser context
        # context = browser.new_context()
        context = browser.new_context(ignore_https_errors=True)
        # Open a new page
        page = context.new_page()

        # Navigate to the desired website
        page.goto(targetUrl)

        # Wait for the page to load completely
        #page.wait_for_load_state('load')  # default 30 seconds
        waitSec = 30
        print(f'waiting {waitSec} seconds that page loads everything...')
        sleep(waitSec)

        # Take a screenshot and save it
        page.screenshot(path=savePath)

        # Close the context and browser
        context.close()
        browser.close()
