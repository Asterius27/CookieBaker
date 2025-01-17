const puppeteer = require('puppeteer');
const fs = require('fs');
const url = require('url');
const minimist = require('minimist');

// A simple crawler used to measure client-side code coverage

const args = minimist(process.argv.slice(2));
const visited = new Set();
let pageCounter = 0;

async function crawl(page, currentUrl, depth, coverageResults, maxPages, maxDepth, startUrl, outputFile, resultsPath, loginCookies) {
    if (depth > maxDepth || pageCounter >= maxPages) return;
    if (visited.has(currentUrl)) return;

    let jsCoverageStarted = false;

    try {
        console.log(`Visiting: ${currentUrl} | Depth: ${depth}`);
        visited.add(currentUrl);
        pageCounter++;

        try {
            await page.coverage.startJSCoverage();
            jsCoverageStarted = true;
        } catch (coverageError) {
        }

        try {

            await page.goto(currentUrl, { waitUntil: 'networkidle2', timeout: 60000 });

            const links = await page.$$eval('a[href]', anchors =>
                anchors.map(anchor => anchor.href)
            );

            const normalizedLinks = links
                .map(href => url.resolve(currentUrl, href))
                .filter(href => {
                    let startUrlObj = url.parse(startUrl);
                    let domain = startUrlObj.hostname;
                    return href.startsWith("http://" + domain) || href.startsWith("https://" + domain);
                })
                .filter(href => {
                    return !href.toLowerCase().includes("logout");
                });

            let jsCoverageTaken = false;
            let jsCoverage = null;
            if (jsCoverageStarted) {
                try {
                    jsCoverage = await page.coverage.stopJSCoverage();
                    jsCoverageTaken = true;
                } catch (stopError) {
                }
            }

            if (jsCoverageTaken) {
                if (!fs.existsSync(resultsPath)) {
                    fs.mkdirSync(resultsPath, { recursive: true });
                }
                fs.writeFileSync(resultsPath + "/" + currentUrl.replaceAll(':', '').replaceAll('/', '-') + "_" + outputFile, JSON.stringify({ jsCoverage }, null, 2));
            }

            const pageCoverage = {
                url: currentUrl,
                timestamp: new Date().toISOString()
            };
            coverageResults.push(pageCoverage);

            for (const link of normalizedLinks) {
                if (!visited.has(link)) {
                    await crawl(page, link, depth + 1, coverageResults, maxPages, maxDepth, startUrl, outputFile, resultsPath, loginCookies);
                }
                if (pageCounter >= maxPages) break;
            }
        } finally {
            if (jsCoverageStarted) {
                try {
                    await page.coverage.stopJSCoverage();
                } catch (stopError) {
                }
            }
        }
    } catch (error) {
        console.error(`Error visiting ${currentUrl}: ${error.message}`);
    }
}

(async () => {
    const url = args.url || 'https://x.com';
    const loginCookies = args.loginCookies || "";
    const resultsPath = args.resultsPath || url.replaceAll(':', '').replaceAll('/', '-');
    const maxDepth = args.maxDepth ? parseInt(args.maxDepth) : 5;
    const maxPages = args.maxPages ? parseInt(args.maxPages) : 50;

    console.log('Parameters:');
    console.log(`URL: ${url}`);
    console.log(`Login Cookies: ${loginCookies}`);
    console.log(`Results Path: ${resultsPath}`);
    console.log(`Max Depth: ${maxDepth}`);
    console.log(`Max Pages: ${maxPages}`);

    const output_file = 'coverage-results.json';

    const browser = await puppeteer.launch({
        headless: false,
        ignoreHTTPSErrors: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors']
    });
    if (loginCookies.length > 0) {
        let cookies_string = loginCookies.split(";")
        for (let cookie of cookies_string) {
            console.log(cookie)
            await browser.setCookie({
                name: cookie.split("=")[0].replaceAll(" ", ""),
                value: cookie.split("=")[1].replaceAll(" ", ""),
                domain: 'localhost',
            });
        }
    }
    const page = await browser.newPage();

    const coverageResults = [];

    await crawl(page, url, 0, coverageResults, maxPages, maxDepth, url, output_file, resultsPath, loginCookies);

    await browser.close();

})();
