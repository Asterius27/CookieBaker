import os
import signal
import subprocess
import threading

from config import CODECOVERAGE_DEFAULT_DIR_FOR_OUTPUTS, RUN_TIME_STR
from util.fileUtil import createDirectoryIfNotExists
from util.util import cookieDictToString, cookieListToCookieDict


def runCodeCoveragePuppeteer(url, baseSavePath, cookieString=""):
    """invoke puppeteer for code coverage analysis"""

    cmd = ["node", "crawler_puppeteer.js"] + \
          [f"--url={url}"] + \
          [f"--resultsPath={os.path.abspath(baseSavePath)}"] + \
          [f"--maxDepth=13"] + \
          [f"--maxPages=140"]

    if len(cookieString) > 0:
        cmd = cmd + [f"--loginCookies={cookieString}"]

    print(f"Command for Puppeteer: {cmd}")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd="coverageAnalysis")

    timeout = 60 * 60  # 60 minutes of timeout
    returnCode = -1

    def read_output(process):
        for line in iter(process.stdout.readline, b''):
            line = line.decode()
            print(line, end='')

    output_thread = threading.Thread(target=read_output, args=(process,))
    output_thread.start()

    # check timeout or process completion
    try:
        process.wait(timeout)
    except Exception:
        print(f"Timeout reached after {timeout} seconds. Stopping process...")
        process.send_signal(signal.SIGINT)
    finally:
        process.terminate()

        # ensure process is terminated and output thread is joined
        if output_thread.is_alive():  # then a timeout happened!
            returnCode = -1
        else:
            returnCode = process.returncode
        output_thread.join()

    return returnCode


def runCodeCoverageAnalysis(url, repoName, index, domain, port, loginCookiesList, nonLoginCookiesList,
                            isExternal=False, credentialIndex=0):
    """Method for calling puppeteer code coverage with right parameters and creating dirs for outputs"""

    prefix = "external_" if isExternal else ""
    areThereLoginCookies = len(loginCookiesList) > 0
    cookiesStr = "without_cookies" if not areThereLoginCookies else "with_cookies"

    pathCoverage = os.path.join(CODECOVERAGE_DEFAULT_DIR_FOR_OUTPUTS, RUN_TIME_STR,
                                repoName, str(index),
                                f"{domain}_{port}",
                                cookiesStr,
                                f"{prefix}{str(credentialIndex)}")

    createDirectoryIfNotExists(pathCoverage)
    urlWithProtocol = f"http://{url}"
    print(f"Code Coverage {cookiesStr}")
    if not areThereLoginCookies:
        runCodeCoveragePuppeteer(urlWithProtocol, pathCoverage)
    else:
        cookiesList = loginCookiesList + nonLoginCookiesList
        cookieString = cookieDictToString(cookieListToCookieDict(cookiesList))

        runCodeCoveragePuppeteer(urlWithProtocol, pathCoverage, cookieString)

    return pathCoverage
