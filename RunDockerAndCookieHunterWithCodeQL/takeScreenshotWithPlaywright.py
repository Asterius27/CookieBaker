# This script captures a screenshot of a given URL using Playwright and saves it to a specified path.
#
# Prerequisites:
#   - Playwright installed:  `pip install playwright`
#   - Playwright browsers installed: `playwright install`
#
# Usage:
#   python3 takeScreenshotWithPlaywright.py -u <url> -p <path/to/save/screenshot.png>
#   Example: python3 takeScreenshotWithPlaywright.py -u "https://www.google.com" -p "google_screenshot.png"

import argparse

from util.playwrightUtil import takeScreen

# create a parser
parser = argparse.ArgumentParser()
# and add arguments to the parser
parser.add_argument("-u", "--url", dest="url", help="Input File", required=True)
parser.add_argument("-p", "--path", dest="path", help="Path in which save screenshot", required=False, default=False)

args = parser.parse_args()

if args.url is None:
    raise Exception("Argument Input file missing!")

if args.path is None:
    raise Exception("Argument pathLoginEndpoints file missing!")

url = args.url
path = args.path

# playwright screenshots
print("Taking screen...")
takeScreen(url, path)
print("Done!")
