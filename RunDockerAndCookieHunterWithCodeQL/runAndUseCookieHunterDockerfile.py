# python3 runAndUseCookieHunterDockerfile.py -i <scraped_repos.json> -l <codeql_login_endpoints.json> -s <codeql_signup_endpoints.json> -c <credentials.json>
# This script automates the process of building and running web applications using Dockerfiles, performing security analysis
# with CookieHunter, code coverage analysis, and vulnerability scanning with Wapiti. It takes a JSON file containing
# repository information as input, along with optional CodeQL login/signup endpoints and credentials.  The script
# iterates through each repository, attempts to build and run its Dockerfile, and if successful, uses CookieHunter to
# extract cookies and perform security analysis. Results, including errors, statistics, and successful runs, are saved
# in designated output directories.
#
# Prerequisites:
#   - Docker installed and running.
#   - MongoDB running at localhost:27123 (configurable in config.py).
#   - NodeJS and npm for code coverage analysis + install node_modules in CoverageAnalysis/package.json
#   - Wapiti for vulnerability scanning.
#   - If you take screenshots here with Playwright, you will also need to install Playwright
#       - Playwright installed:  `pip install playwright`
#       - Playwright browsers installed: `playwright install`
#
# Usage:
#   - Provide the path to the input JSON file containing repository information using the -i flag.
#   - Optionally, provide paths to CodeQL login/signup endpoints and credentials JSONs using -l, -s, and -c flags respectively.
#   - Example: python3 runAndUseCookieHunterDockerfile.py -i scraped_repos.json -l codeql_logins.json -s codeql_signups.json -c credentials.json

import argparse
import json
import os
import sys
import traceback

from config import DEFAULT_DIR_FOR_REPOS, DEFAULT_DIR_FOR_OUTPUTS, DEFAULT_DIR_FOR_LOGS, TOKEN_SEPARATOR, RUN_TIME_STR, \
    DEFAULT_FILENAME_FOR_ERROR, DEFAULT_FILENAME_FOR_STATS, DEFAULT_FILENAME_FOR_OUTPUT, BUILD_IMAGE_NAME_PREFIX
from models.DockerRepoRunInfo import DockerRepoRunInfo
from models.DockerfileRunInfo import DockerfileRunInfo
from models.InjectionInfo import InjectionInfo
from models.RepositoryInfo import RepositoryInfo
from util.Logger import Logger
from util.codeCoveragePuppeteerUtil import runCodeCoverageAnalysis
from util.cookiehunterUtil import runCookieHunter, completeCleanCookieHunterDB, softCleanCookieHunterDB
from util.dockerUtil import cleanEnvironment, getPortsFromContainers, waitWebAppRunning, getContainersStatus, \
    pruneDockerSystem, nextDockerLogin, runDockerfile, buildDockerfile, removeAllImagesWithPrefix
from util.fileUtil import createDirectoryIfNotExists, deleteDirAndAllContents, checkIfDirExists, getAbsolutePath, \
    changeBasePath
from util.mongoUtil import extractCookies, extractCookiesDetailed
from util.playwrightUtil import takeScreen

from util.repoUtil import copyRepository
from util.util import killService, anyEntryHasLoginCookies, hasLoginCookies
from util.wapitiUtil import runWapitiAnalysis

# kill any running nginx processes and clean the CookieHunter database.
killService("nginx")
completeCleanCookieHunterDB()

# initialize counters for tracking Docker pulls, repository processing, and errors.
counterDockerPulls = 0
counterDockerPullsForPrune = 0

counterRepos = 0
counterReposWithDockerfile = 0
counterReposRunning = 0
counterErrorCloneRepos = 0
counterErrorCrashRepos = 0
counterErrorTimeoutRepos = 0
counterErrorDockerCompose = 0

# initialize lists to store information about repositories with errors and successful runs
errorCloneRepos = []
errorCrashRepos = []
errorTimeoutRepos = []
runningDockerfileRepos = []

# redirect standard output to a log file
sys.stdout = Logger(f"{DEFAULT_DIR_FOR_LOGS}{TOKEN_SEPARATOR}{RUN_TIME_STR}", TOKEN_SEPARATOR,
                    f"{RUN_TIME_STR}_terminal")

# create a parser
parser = argparse.ArgumentParser()
# and add arguments to the parser
parser.add_argument("-i", "--input", dest="inputFilename", help="Input File", required=True)
parser.add_argument("-l", "--login", dest="pathLoginEndpoints",
                    help="Path of .json file containing login endpoints of repos from CodeQL",
                    required=False, default=None)
parser.add_argument("-s", "--signup", dest="pathSignupEndpoints",
                    help="Path of .json file containing signup endpoints of repos from CodeQL",
                    required=False, default=None)
parser.add_argument("-c", "--credentials", dest="pathCredentials",
                    help="Path of .json file containing default credentials to try to login",
                    required=False, default=None)

args = parser.parse_args()

if args.inputFilename is None:
    raise Exception("Argument Input file missing!")

inputFilePath = args.inputFilename
inputFileName = inputFilePath.split(TOKEN_SEPARATOR)[-1]

if args.pathLoginEndpoints is None:
    # raise Exception("Argument pathLoginEndpoints file missing!")
    pathLoginEndpoints = ""
else:
    pathLoginEndpoints = getAbsolutePath(args.pathLoginEndpoints)

if args.pathSignupEndpoints is None:
    # raise Exception("Argument pathSignupEndpoints file missing!")
    pathSignupEndpoints = ""
else:
    pathSignupEndpoints = getAbsolutePath(args.pathSignupEndpoints)

if args.pathCredentials is None:
    # raise Exception("Argument pathSignupEndpoints file missing!")
    pathCredentials = ""
else:
    pathCredentials = getAbsolutePath(args.pathCredentials)

cleanEnvironment()  # clean docker environment

f = open(inputFilePath)

# returns JSON object as a dictionary
entryList = json.load(f, object_hook=lambda d: RepositoryInfo(**d))

# delete possibly previous "repos" dir
if checkIfDirExists(DEFAULT_DIR_FOR_REPOS):
    deleteDirAndAllContents(DEFAULT_DIR_FOR_REPOS)

createDirectoryIfNotExists(DEFAULT_DIR_FOR_REPOS)
createDirectoryIfNotExists(DEFAULT_DIR_FOR_OUTPUTS)
createDirectoryIfNotExists(DEFAULT_DIR_FOR_LOGS)

createDirectoryIfNotExists(f"{DEFAULT_DIR_FOR_OUTPUTS}{TOKEN_SEPARATOR}{RUN_TIME_STR}")
createDirectoryIfNotExists(f"{DEFAULT_DIR_FOR_LOGS}{TOKEN_SEPARATOR}{RUN_TIME_STR}")

nextDockerLogin()

print(f"\n\nNEW RUN {RUN_TIME_STR}\n\n")
for repoInfo in entryList:
    print(f"\n\n --- REPO {repoInfo.getRepoName()} ---\n\n")
    counterRepos += 1

    isRepoRunning = False

    repoName = repoInfo.getRepoName()
    repoPath = repoInfo.getRepoPath()
    lstDockerCompose = repoInfo.getMultipleDockerComposePaths()
    lstDockerFile = repoInfo.getMultipleDockerfilePaths()

    print(f"Number of dockerfile to try: {len(lstDockerFile)}")

    logPathForCurrentRepo = f"{DEFAULT_DIR_FOR_LOGS}{TOKEN_SEPARATOR}{RUN_TIME_STR}{TOKEN_SEPARATOR}{repoName}"
    createDirectoryIfNotExists(logPathForCurrentRepo)

    if len(lstDockerFile) == 0:
        print(f"NO dockerfile: skipping repo {repoInfo.getRepoName()} ")
        continue

    if len(lstDockerCompose) > 0:
        print(f"Skipping repo that has docker-compose")
        continue

    try:
        counterReposWithDockerfile += 1
        isCloned = copyRepository(f"{DEFAULT_DIR_FOR_REPOS}{TOKEN_SEPARATOR}{repoName}", repoPath)

        if not isCloned:
            errorCloneRepos.append(repoInfo)
            counterErrorCloneRepos += 1
            print(f"Error cloning the repo {repoPath}!")
        else:
            dockerfileRunsResult = []
            dockerfileSuccess = 0
            dockerfileTimeout = 0
            dockerfileError = 0
            dockerfileNotRunning = 0

            for index, realDockerfilePath in enumerate(lstDockerFile):
                dockerfilePath = changeBasePath(realDockerfilePath,
                                                repoPath,
                                                os.path.join(DEFAULT_DIR_FOR_REPOS, repoName))
                logPathForCurrentDockerfile = f"{logPathForCurrentRepo}{TOKEN_SEPARATOR}{index}"
                createDirectoryIfNotExists(logPathForCurrentDockerfile)

                portsWithHttpResponse = []
                isRunning = False
                isTimeout = False
                timeToGetRunning = 0
                portsExposedManually = False
                envAddedManually = False
                envPathUsed = ""
                addedExternalNetworkManually = False
                useParentOfDockerfileAsWorkingDir = False

                if counterDockerPulls > 25:
                    nextDockerLogin()
                    counterDockerPulls = 0

                if counterDockerPullsForPrune > 70:
                    pruneDockerSystem()
                    counterDockerPullsForPrune = 0

                print(f"Trying to build dockerfile: {dockerfilePath}")
                returnCode, _, imageName = buildDockerfile(index, dockerfilePath, repoName, logPathForCurrentDockerfile)
                print(f"RETURN CODE: {returnCode}\n")  # print the exit code of the command

                if returnCode == 0:
                    print("Build OK")

                    print(f"Trying to run dockerfile: {dockerfilePath}")
                    returnCode, logPath = runDockerfile(index, imageName, repoName, logPathForCurrentDockerfile)
                    print(f"RETURN CODE: {returnCode}\n")  # print the exit code of the command

                    if returnCode == 0:
                        print(getContainersStatus())
                        print()
                        print("Trying to get ports from containers...")
                        ports = getPortsFromContainers()
                        print(f"Ports: {ports}")

                        if len(ports) > 0:  # try to run at first attempt with docker-compose.yml as-provided
                            print(f"There are ports obtained from containers: {ports}")
                            if returnCode == 0:
                                isRunning, portsWithHttpResponse, isTimeout, timeToGetRunning = waitWebAppRunning(ports)
                                if isRunning:
                                    print(f"WEB APP works and responds at {portsWithHttpResponse}")

                        # try again only if docker compose was successful but no ports exposed, or no answer obtained from ports
                        if len(ports) == 0 or len(portsWithHttpResponse) == 0:
                            print("No ports or no one replied to http request")
                            print("Trying to run publishing all ports...\n")
                            # clean environment from containers, and rerun dockerfile with all ports exposed
                            cleanEnvironment(logPathForCurrentDockerfile)
                            logPathForCurrentDockerfilePorts = f"{logPathForCurrentDockerfile}{TOKEN_SEPARATOR}exposedports"
                            createDirectoryIfNotExists(logPathForCurrentDockerfilePorts)
                            returnCode, logPath = runDockerfile(index, imageName, repoName,
                                                                logPathForCurrentDockerfilePorts, exposePorts=True)
                            portsExposedManually = True
                            ports = getPortsFromContainers()
                            print(f"Ports after exposing: {ports}")

                            if returnCode == 0:
                                isRunning, portsWithHttpResponse, isTimeout, timeToGetRunning = waitWebAppRunning(ports)
                                if isRunning:
                                    print(f"WEB APP works and responds (after exposing) at {portsWithHttpResponse}")

                if not isRunning:  # not worked, try to use the dir in which the Dockerfile is as working dir
                    print("Trying to use the dir in which the Dockerfile is as working dir for Docker Build\n")
                    cleanEnvironment(logPathForCurrentDockerfile)
                    logPathForCurrentDockerfile = f"{logPathForCurrentDockerfile}{TOKEN_SEPARATOR}parentdir"
                    createDirectoryIfNotExists(logPathForCurrentDockerfile)
                    useParentOfDockerfileAsWorkingDir = True

                    print("Deleting previous image...")
                    removeAllImagesWithPrefix(BUILD_IMAGE_NAME_PREFIX)

                    print(f"Trying to build dockerfile (using parent of dockerfile as working dir): {dockerfilePath}")
                    returnCode, _, imageName = buildDockerfile(index, realDockerfilePath, repoName,
                                                               logPathForCurrentDockerfile,
                                                               useParentOfDockerfileAsWorkingDir=True)
                    print(f"RETURN CODE: {returnCode}\n")  # print the exit code of the command

                    if returnCode == 0:
                        print("Build OK")

                        print(f"Trying to run dockerfile: {dockerfilePath}")
                        returnCode, logPath = runDockerfile(index, imageName, repoName, logPathForCurrentDockerfile)
                        print(f"RETURN CODE: {returnCode}\n")  # print the exit code of the command

                        if returnCode == 0:
                            print(getContainersStatus())
                            print()
                            print("Trying to get ports from containers...")
                            ports = getPortsFromContainers()
                            print(f"Ports: {ports}")

                            if len(ports) > 0:  # try to run at first attempt with docker-compose.yml as-provided
                                print(f"There are ports obtained from containers: {ports}")
                                if returnCode == 0:
                                    isRunning, portsWithHttpResponse, isTimeout, timeToGetRunning = waitWebAppRunning(
                                        ports)
                                    if isRunning:
                                        print(f"WEB APP works and responds at {portsWithHttpResponse}")

                            # try again only if docker compose was successful but no ports exposed, or no answer obtained from ports
                            if len(ports) == 0 or len(portsWithHttpResponse) == 0:
                                print("No ports or no one replied to http request")
                                print("Trying to run publishing all ports...\n")
                                # clean environment from containers, and rerun dockerfile with all ports exposed
                                cleanEnvironment(logPathForCurrentDockerfile)
                                logPathForCurrentDockerfilePorts = f"{logPathForCurrentDockerfile}{TOKEN_SEPARATOR}exposedports"
                                createDirectoryIfNotExists(logPathForCurrentDockerfilePorts)
                                returnCode, logPath = runDockerfile(index, imageName, repoName,
                                                                    logPathForCurrentDockerfilePorts, exposePorts=True)
                                portsExposedManually = True
                                ports = getPortsFromContainers()
                                print(f"Ports after exposing: {ports}")

                                if returnCode == 0:
                                    isRunning, portsWithHttpResponse, isTimeout, timeToGetRunning = waitWebAppRunning(
                                        ports)
                                    if isRunning:
                                        print(f"WEB APP works and responds (after exposing) at {portsWithHttpResponse}")

                if returnCode == 0:  # try to send requests only if dockerfile run without errors

                    if isRunning:
                        dockerfileSuccess += 1

                        containerInjectionResults = []

                        runInfo = DockerfileRunInfo(realDockerfilePath, portsWithHttpResponse, timeToGetRunning,
                                                    returnCode, isRunning, isTimeout, portsExposedManually,
                                                    useParentOfDockerfileAsWorkingDir,
                                                    InjectionInfo(containerInjectionResults))
                        dockerfileRunsResult.append(runInfo)
                        print("Repo is running")

                        # # Take screenshots with playwright
                        # print("Taking screens...")
                        # i = 0
                        # for (port, protocol) in portsWithHttpResponse:
                        #     print(f"Taking screen at: {protocol}://localhost:{port}")
                        #     takeScreen(f"{protocol}://localhost:{port}",
                        #                f"{DEFAULT_DIR_FOR_OUTPUTS}{TOKEN_SEPARATOR}{RUN_TIME_STR}{TOKEN_SEPARATOR}{repoName}_screen_{i}.png")
                        #     i += 1
                        # print("Finished taking screens")

                        print(f"Running cookie hunter on repo {repoName}...")
                        i = 0
                        domain = "localhost"
                        for (port, protocol) in portsWithHttpResponse:
                            print(f"Trying cookie hunter at: localhost:{port}")
                            softCleanCookieHunterDB()
                            url = f"{domain}:{port}"
                            runCookieHunter(url, repoName, repoPath,
                                            pathLoginEndpoints, pathSignupEndpoints, pathCredentials)

                            # internal credentials CH
                            loginCookiesList, nonLoginCookiesList = extractCookies()

                            # external credentials from static analysis
                            allCookiesData = extractCookiesDetailed()

                            print(loginCookiesList)
                            print(nonLoginCookiesList)
                            print(allCookiesData)
                            isThereInternalCookies = len(loginCookiesList) > 0
                            isThereExternalCookies = anyEntryHasLoginCookies(allCookiesData)

                            # if there are login-cookies (internal and/or external), then do
                            # - coverage without cookie
                            # - coverage with cookie (internal)
                            # - coverage with cookie (external)
                            # - wapiti without cookie
                            # - wapiti with cookie (internal)
                            # - wapiti with cookie (external)

                            if isThereInternalCookies or isThereExternalCookies:
                                # code coverage analysis
                                runCodeCoverageAnalysis(url, repoName, index, domain, port, [], [])
                                if isThereInternalCookies:
                                    runCodeCoverageAnalysis(url, repoName, index, domain, port, loginCookiesList,
                                                            nonLoginCookiesList)
                                else:
                                    print("No login cookies, skipping cookie (internal) code coverage analysis")

                                credentialIndex = 0
                                for cookieData in allCookiesData:
                                    print(f" - [{credentialIndex}] Analyzing user: {cookieData.get('username')}")
                                    loginCookies = cookieData.get('loginCookies', [])
                                    nonLoginCookies = cookieData.get('nonLoginCookies', [])

                                    if hasLoginCookies(loginCookies):
                                        pathCoverage = runCodeCoverageAnalysis(url, repoName, index, domain, port,
                                                                               loginCookies,
                                                                               nonLoginCookies, isExternal=True,
                                                                               credentialIndex=credentialIndex)
                                        with open(os.path.join(pathCoverage, 'credential_data.json'), "w") as f:
                                            f.write(json.dumps(cookieData, indent=4))
                                            f.flush()
                                    else:
                                        print("No login cookies, skipping analysis")
                                    credentialIndex += 1

                                # wapiti analysis
                                runWapitiAnalysis(url, repoName, index, domain, port, [], [])
                                if isThereInternalCookies:
                                    runWapitiAnalysis(url, repoName, index, domain, port, loginCookiesList,
                                                      nonLoginCookiesList)
                                else:
                                    print("No login cookies, skipping cookie (internal) code coverage analysis")

                                credentialIndex = 0
                                for cookieData in allCookiesData:
                                    print(f" - [{credentialIndex}] Analyzing user: {cookieData.get('username')}")
                                    loginCookies = cookieData.get('loginCookies', [])
                                    nonLoginCookies = cookieData.get('nonLoginCookies', [])

                                    if hasLoginCookies(loginCookies):
                                        pathWapiti = runWapitiAnalysis(url, repoName, index, domain, port, loginCookies,
                                                                       nonLoginCookies, isExternal=True,
                                                                       credentialIndex=credentialIndex)
                                        with open(os.path.join(pathWapiti, 'credential_data.json'), "w") as f:
                                            f.write(json.dumps(cookieData, indent=4))
                                            f.flush()
                                    else:
                                        print("No login cookies, skipping analysis")
                                    credentialIndex += 1

                            else:
                                print("No login cookies found! Skipping vuln scan and code coverage analysis.")

                            i += 1
                        print("Finished running cookie hunter")

                    elif isTimeout:
                        dockerfileTimeout += 1
                        print("Not enough time to run repo")
                        runInfo = DockerfileRunInfo(realDockerfilePath, portsWithHttpResponse, timeToGetRunning,
                                                    returnCode, isRunning, isTimeout, portsExposedManually,
                                                    useParentOfDockerfileAsWorkingDir)
                        dockerfileRunsResult.append(runInfo)
                    else:
                        dockerfileError += 1
                        print(f"Error: not running and not timeout {repoInfo.getRepoName()}!")
                        runInfo = DockerfileRunInfo(realDockerfilePath, portsWithHttpResponse, timeToGetRunning,
                                                    returnCode, isRunning, isTimeout, portsExposedManually,
                                                    useParentOfDockerfileAsWorkingDir)
                        dockerfileRunsResult.append(runInfo)
                else:
                    dockerfileNotRunning += 1
                    print("Skipping repo because of return code of dockerfile")
                    runInfo = DockerfileRunInfo(realDockerfilePath, [], -1, returnCode,
                                                isNeededToExposePorts=portsExposedManually,
                                                useParentOfDockerfileAsWorkingDir=useParentOfDockerfileAsWorkingDir)
                    dockerfileRunsResult.append(runInfo)

                print()
                # clean environment to be ready for next docker-compose
                cleanEnvironment(logPathForCurrentDockerfile, portsExposedManually)
                counterDockerPulls += 1
                counterDockerPullsForPrune += 1
                print()

            repoRunInfo = DockerRepoRunInfo(repoName=repoName, repoURL="", repoPath=repoPath,
                                            dockerfileRuns=dockerfileRunsResult,
                                            dockerfileSuccess=dockerfileSuccess,
                                            dockerfileTimeout=dockerfileTimeout,
                                            dockerfileError=dockerfileError,
                                            dockerfileNotRunning=dockerfileNotRunning)
            if dockerfileSuccess > 0:
                counterReposRunning += 1
                isRepoRunning = True

            runningDockerfileRepos.append(repoRunInfo)


    except Exception as err:
        print("An error occurred")
        print(err)
        traceback.print_stack()
        errorCrashRepos.append(repoInfo)
        counterErrorCrashRepos += 1

    finally:  # clean and delete repo
        print("Cleaning environment...")

        # clean environment for next run
        cleanEnvironment()
        removeAllImagesWithPrefix(BUILD_IMAGE_NAME_PREFIX)
        removeAllImagesWithPrefix('<none>')

        deleteDirAndAllContents(f"{DEFAULT_DIR_FOR_REPOS}{TOKEN_SEPARATOR}{repoInfo.getRepoName()}")

        print("Cleaned!")
        print('\n')
        print(f"Number of repos: {counterRepos}")
        print(f"Number of repos with dockerfile: {counterReposWithDockerfile}")
        print(f"Number of repos RUN correctly (with at least a dockerfile): {counterReposRunning}")
        print(f"Number of repos with ERRORS: {counterErrorCrashRepos}")
        print(f"Number of repos with CLONE ERROR {counterErrorCloneRepos}")
        print("\n")

        with open(
                f"{DEFAULT_DIR_FOR_OUTPUTS}{TOKEN_SEPARATOR}{RUN_TIME_STR}{TOKEN_SEPARATOR}{RUN_TIME_STR}_{DEFAULT_FILENAME_FOR_ERROR}_CLONED_{inputFileName}.json",
                "w") as f:
            f.write(json.dumps(errorCloneRepos, indent=4))
            f.flush()

        with open(
                f"{DEFAULT_DIR_FOR_OUTPUTS}{TOKEN_SEPARATOR}{RUN_TIME_STR}{TOKEN_SEPARATOR}{RUN_TIME_STR}_{DEFAULT_FILENAME_FOR_ERROR}_CRASH_{inputFileName}.json",
                "w") as f:
            f.write(json.dumps(errorCrashRepos, indent=4))
            f.flush()

        with open(
                f"{DEFAULT_DIR_FOR_OUTPUTS}{TOKEN_SEPARATOR}{RUN_TIME_STR}{TOKEN_SEPARATOR}{RUN_TIME_STR}_{DEFAULT_FILENAME_FOR_OUTPUT}_{inputFileName}.json",
                "w") as f:
            f.write(json.dumps(runningDockerfileRepos, indent=4))
            f.flush()

        with open(
                f"{DEFAULT_DIR_FOR_OUTPUTS}{TOKEN_SEPARATOR}{RUN_TIME_STR}{TOKEN_SEPARATOR}{RUN_TIME_STR}_{DEFAULT_FILENAME_FOR_STATS}_{inputFileName}.txt",
                "w") as f:
            f.write(f"Number of repos: {counterRepos}\n")
            f.write(f"Number of repos with dockerfile: {counterReposWithDockerfile}\n")
            f.write(f"Number of repos RUN (with at least a dockerfile): {counterReposRunning}\n")
            f.write(f"Number of repos with ERRORS: {counterErrorCrashRepos}\n")
            f.write(f"Number of repos with CLONE ERROR {counterErrorCloneRepos}\n")
            f.flush()
