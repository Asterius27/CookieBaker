import os
import signal
import subprocess
import threading

from config import WAPITI_COMMAND, WAPITI_FILENAME_REPORT, WAPITI_FILENAME_LOG, WAPITI_NAMEDIR_SCANFILES, \
    WAPITI_DEFAULT_DIR_FOR_OUTPUTS, RUN_TIME_STR
from util.fileUtil import createDirectoryIfNotExists
from util.util import cookieDictToString, cookieListToCookieDict


def runWapiti(url, baseSavePath, loginCookiesList=[], nonLoginCookiesList=[]):
    """invoke wapiti scanner for code vulnerability analysis"""
    cookiesList = loginCookiesList + nonLoginCookiesList
    cookieString = cookieDictToString(cookieListToCookieDict(cookiesList))

    cmd = WAPITI_COMMAND + \
          ["-u", url] + \
          ["--output", os.path.join(baseSavePath, WAPITI_FILENAME_REPORT)] + \
          ["--log", os.path.join(baseSavePath, WAPITI_FILENAME_LOG)] + \
          ["--store-session", os.path.join(baseSavePath, WAPITI_NAMEDIR_SCANFILES)]

    if len(cookiesList) > 0:
        cmd = cmd + ["--cookie-value", cookieString]

    print(f"Command for Wapiti: {cmd}")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    timeout = 5 * 60 * 60
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


def runWapitiAnalysis(url, repoName, index, domain, port, loginCookiesList, nonLoginCookiesList, isExternal=False,
                      credentialIndex=0):
    """Method for calling wapiti vulnerability scan with right parameters and creating dirs for outputs"""

    prefix = "external_" if isExternal else ""
    cookiesStr = "without_cookies" if len(loginCookiesList) == 0 else "with_cookies"
    pathWapiti = os.path.join(WAPITI_DEFAULT_DIR_FOR_OUTPUTS, RUN_TIME_STR,
                              repoName, str(index),
                              f"{domain}_{port}",
                              cookiesStr,
                              f"{prefix}{str(credentialIndex)}")

    createDirectoryIfNotExists(pathWapiti)
    urlWithProtocol = f"http://{url}"
    print(f"Wapiti {cookiesStr}")
    runWapiti(urlWithProtocol, pathWapiti, loginCookiesList, nonLoginCookiesList)
    return pathWapiti
