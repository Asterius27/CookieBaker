# python3 runAndUseCookieHunterDockerCompose.py -i <scraped_repos.json> -l <codeql_login_endpoints.json> -s <codeql_signup_endpoints.json> -c <credentials.json>
# This script automates the process of running web applications using Docker Compose, performing security analysis
# with CookieHunter, code coverage analysis, and vulnerability scanning with Wapiti. It takes a JSON file containing
# repository information as input, along with optional CodeQL login/signup endpoints and credentials.
# The script iterates through each repository, attempts to run its Docker Compose configuration, and if successful,
# uses CookieHunter to extract cookies and subsequently perform security analysis using those cookies.
# Results, including errors, statistics, and successful runs, are saved in designated output directories.
#
# Prerequisites:
#   - Docker and Docker Compose installed and running.
#   - MongoDB running at localhost:27123 (configurable in config.py).
#   - NodeJS and npm for code coverage analysis + install node_modules in CoverageAnalysis/package.json
#   - Wapiti for vulnerability scanning
#   - If you take screenshots here with Playwright, you will also need to install Playwright
#       - Playwright installed:  `pip install playwright`
#       - Playwright browsers installed: `playwright install`
#
# Usage:
#   - Provide the path to the input JSON file containing repository information using the -i flag.
#   - Optionally, provide paths to CodeQL login/signup endpoints and credentials JSONs using -l, -s, and -c flags respectively.
#   - Example: python3 runAndUseCookieHunterDockerCompose.py -i scraped_repos.json -l codeql_logins.json -s codeql_signups.json -c credentials.json

import argparse
import json
import os
import shutil
import sys
import traceback
from time import sleep

from config import DEFAULT_DIR_FOR_REPOS, DEFAULT_DIR_FOR_OUTPUTS, DEFAULT_DIR_FOR_LOGS, TOKEN_SEPARATOR, RUN_TIME_STR, \
    DEFAULT_FILENAME_FOR_ERROR, DEFAULT_FILENAME_FOR_STATS, DEFAULT_FILENAME_FOR_OUTPUT
from models.DockerComposeRunInfo import DockerComposeRunInfo
from models.DockerRepoRunInfo import DockerRepoRunInfo
from models.InjectionInfo import InjectionInfo
from models.RepositoryInfo import RepositoryInfo
from util.Logger import Logger
from util.codeCoveragePuppeteerUtil import runCodeCoverageAnalysis
from util.cookiehunterUtil import runCookieHunter, completeCleanCookieHunterDB, softCleanCookieHunterDB
from util.dockerUtil import cleanEnvironment, getPortsFromContainers, waitWebAppRunning, exposeAllPortsOfContainer, \
    reloadedContainerStatus, getContainersStatus, runDockerCompose, getNameOfNetworkFromLog, \
    createNetwork, pruneDockerSystem, nextDockerLogin
from util.fileUtil import createDirectoryIfNotExists, deleteDirAndAllContents, checkIfDirExists, getAbsolutePath, \
    copyAndRenameFile, changeBasePath
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
counterReposWithDockercompose = 0
counterReposRunning = 0
counterErrorCloneRepos = 0
counterErrorCrashRepos = 0
counterErrorTimeoutRepos = 0
counterErrorDockerCompose = 0

# initialize lists to store information about repositories with errors.
errorCloneRepos = []
errorCrashRepos = []
errorTimeoutRepos = []
errorDockerComposeRepos = []
runningDockerComposeRepos = []
dockerComposeStatusCodes = []

# redirect standard output to a log file.
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

print()

# handle paths for CodeQL endpoints and credentials, printing messages indicating their availability.
if args.pathLoginEndpoints is None:
    # raise Exception("Argument pathLoginEndpoints file missing!")
    pathLoginEndpoints = ""
    print(f"NO CODEQL logins")
else:
    pathLoginEndpoints = getAbsolutePath(args.pathLoginEndpoints)
    print(f"CODEQL logins available at {pathLoginEndpoints}")

if args.pathSignupEndpoints is None:
    # raise Exception("Argument pathSignupEndpoints file missing!")
    pathSignupEndpoints = ""
    print(f"NO CODEQL signups")
else:
    pathSignupEndpoints = getAbsolutePath(args.pathSignupEndpoints)
    print(f"CODEQL signups available at {pathSignupEndpoints}")

if args.pathCredentials is None:
    # raise Exception("Argument pathSignupEndpoints file missing!")
    pathCredentials = ""
    print(f"NO CREDENTIALS available")
else:
    pathCredentials = getAbsolutePath(args.pathCredentials)
    print(f"CREDENTIALS available at {pathCredentials}")

print()

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

createDirectoryIfNotExists(os.path.join(DEFAULT_DIR_FOR_OUTPUTS, RUN_TIME_STR))
createDirectoryIfNotExists(os.path.join(DEFAULT_DIR_FOR_LOGS, RUN_TIME_STR))

nextDockerLogin()

print(f"\n\nNEW RUN {RUN_TIME_STR}\n\n")
for repoInfo in entryList:
    print(f"\n\n --- REPO {repoInfo.getRepoName()} ---\n\n")
    counterRepos += 1

    isRepoRunning = False

    repoName = repoInfo.getRepoName()
    repoPath = repoInfo.getRepoPath()
    lstDockerCompose = repoInfo.getMultipleDockerComposePaths()
    print(f"Number of docker compose to try: {len(lstDockerCompose)}")

    logPathForCurrentRepo = f"{DEFAULT_DIR_FOR_LOGS}{TOKEN_SEPARATOR}{RUN_TIME_STR}{TOKEN_SEPARATOR}{repoName}"
    createDirectoryIfNotExists(logPathForCurrentRepo)

    if len(lstDockerCompose) == 0:
        print(f"NO dockercompose: skipping repo {repoInfo.getRepoName()} ")
        continue

    try:
        counterReposWithDockercompose += 1
        isCloned = copyRepository(f"{DEFAULT_DIR_FOR_REPOS}{TOKEN_SEPARATOR}{repoName}", repoPath)

        if not isCloned:
            errorCloneRepos.append(repoInfo)
            counterErrorCloneRepos += 1
            print(f"Error cloning the repo {repoPath}!")
        else:

            dockerComposeRunsResult = []
            dockerComposeSuccess = 0
            dockerComposeTimeout = 0
            dockerComposeError = 0
            dockerComposeNotRunning = 0

            for index, realDockerComposePath in enumerate(lstDockerCompose):
                dockerComposePath = changeBasePath(realDockerComposePath,
                                                   repoPath,
                                                   os.path.join(DEFAULT_DIR_FOR_REPOS, repoName))
                logPathForCurrentDockerCompose = f"{logPathForCurrentRepo}{TOKEN_SEPARATOR}{index}"
                createDirectoryIfNotExists(logPathForCurrentDockerCompose)

                portsWithHttpResponse = []
                isRunning = False
                isTimeout = False
                timeToGetRunning = 0
                portsExposedManually = False
                envAddedManually = False
                envPathUsed = ""
                addedExternalNetworkManually = False

                if counterDockerPulls > 25:
                    nextDockerLogin()
                    counterDockerPulls = 0

                if counterDockerPullsForPrune > 70:
                    pruneDockerSystem()
                    counterDockerPullsForPrune = 0

                print(f"Trying with docker-compose: {dockerComposePath}")
                returnCode, logPath = runDockerCompose(index, dockerComposePath, repoName,
                                                       logPathForCurrentDockerCompose)
                print(f"RETURN CODE: {returnCode}\n")  # print the exit code of the command

                # create all external networks until log of compose contains a match for that error
                if returnCode == 1:
                    networkName = getNameOfNetworkFromLog(logPath)
                    idNetwork = 1
                    while networkName != "":  # continue until no more networks have to be created
                        print(f"Creating external network {networkName}")
                        # create network
                        createNetwork(networkName)
                        print(f"and re-executing docker compose...")
                        # run docker compose again and check result
                        returnCode, logPath = runDockerCompose(f"network{idNetwork}", dockerComposePath, repoName,
                                                               logPathForCurrentDockerCompose)
                        print(f"RETURN CODE (AFTER EXTERNAL NETWORK CREATION): {returnCode}\n")
                        if returnCode == 1:
                            networkName = getNameOfNetworkFromLog(logPath)
                        else:
                            networkName = ""
                        idNetwork += 1
                        addedExternalNetworkManually = True

                if returnCode == 14:  # file not found error by docker compose
                    # .env file is missing, so, try all the .env file and see what happens
                    lstEnvFiles = repoInfo.getEnvFilePaths()
                    print(f"Env file to try with: {len(lstEnvFiles)}")
                    for indexEnv, realEnvPath in enumerate(lstEnvFiles):
                        envPath = changeBasePath(realEnvPath,
                                                 repoPath,
                                                 os.path.join(DEFAULT_DIR_FOR_REPOS, repoName))

                        print(f"Trying to use .env file at location {envPath}")
                        dirNameEnvLog = f"env{indexEnv:2}"
                        createDirectoryIfNotExists(f"{logPathForCurrentDockerCompose}{TOKEN_SEPARATOR}{dirNameEnvLog}")
                        remainingPath = ""
                        destName = ""
                        try:
                            lastIndexOfSeparator = dockerComposePath.rfind(TOKEN_SEPARATOR)
                            filename = dockerComposePath[lastIndexOfSeparator + 1:]
                            remainingPath = dockerComposePath[:lastIndexOfSeparator + 1]
                            destName = ".env"
                            print(f"Copying {envPath} to {remainingPath} and renaming it into {destName}")
                            print(remainingPath)

                            # copy file in docker compose path and rename it to .env
                            copyAndRenameFile(envPath, remainingPath, destName)
                        except shutil.SameFileError:
                            print(f"ATTENTION: {envPath} and {remainingPath}{destName} are the same file.")
                            print(f".env file is not copied")
                        except Exception as ex:
                            print(f"ERROR while copying .env file: {envPath}")
                            print(ex)
                            traceback.print_stack()
                            continue

                        envAddedManually = True
                        envPathUsed = realEnvPath

                        # run docker compose with --env-file <new-.env-file> and see return status code
                        returnCode, _ = runDockerCompose(index, dockerComposePath, repoName,
                                                         f"{logPathForCurrentDockerCompose}{TOKEN_SEPARATOR}{dirNameEnvLog}")
                        print(f"RETURN CODE (AFTER ADDING ENV): {returnCode}")

                        if returnCode == 0:
                            print(getContainersStatus())
                            print()
                            print("Trying to get ports from containers...")
                            ports = getPortsFromContainers()

                            if len(ports) > 0:  # try to run at first attempt with docker-compose.yml as-provided
                                print(f"There are ports obtained from containers: {ports}")
                                if returnCode == 0:
                                    isRunning, portsWithHttpResponse, \
                                        isTimeout, timeToGetRunning = waitWebAppRunning(ports)
                                    if isRunning:
                                        print(f"WEB APP works and responds at {portsWithHttpResponse}")
                                        break  # not interested to try other .env files

                            # try again only if docker compose was successful but no ports exposed, or no answer obtained from ports
                            if len(ports) == 0 or len(portsWithHttpResponse) == 0:

                                containers = reloadedContainerStatus()
                                for c in containers:
                                    exposeAllPortsOfContainer(c,f"{logPathForCurrentDockerCompose}{TOKEN_SEPARATOR}{dirNameEnvLog}")  # expose all ports

                                portsExposedManually = True
                                ports = getPortsFromContainers()
                                print(f"Ports after exposing: {ports}")

                                if returnCode == 0:
                                    isRunning, portsWithHttpResponse, \
                                        isTimeout, timeToGetRunning = waitWebAppRunning(ports)
                                    if isRunning:
                                        print(
                                            f"WEB APP works and responds (after exposing) at {portsWithHttpResponse}")
                                        break  # not interested to try other .env files

                elif returnCode == 0:
                    print(getContainersStatus())
                    print()
                    print("Trying to get ports from containers...")
                    ports = getPortsFromContainers()

                    if len(ports) > 0:  # try to run at first attempt with docker-compose.yml as-provided
                        print(f"There are ports obtained from containers: {ports}")
                        if returnCode == 0:
                            isRunning, portsWithHttpResponse, isTimeout, timeToGetRunning = waitWebAppRunning(ports)
                            if isRunning:
                                print(f"WEB APP works and responds at {portsWithHttpResponse}")

                    # try again only if docker compose was successful but no ports exposed, or no answer obtained from ports
                    if len(ports) == 0 or len(portsWithHttpResponse) == 0:

                        containers = reloadedContainerStatus()
                        for c in containers:
                            exposeAllPortsOfContainer(c, logPathForCurrentDockerCompose)  # expose all ports

                        portsExposedManually = True
                        ports = getPortsFromContainers()
                        print(f"Ports after exposing: {ports}")

                        if returnCode == 0:
                            isRunning, portsWithHttpResponse, isTimeout, timeToGetRunning = waitWebAppRunning(ports)
                            if isRunning:
                                print(f"WEB APP works and responds (after exposing) at {portsWithHttpResponse}")


                if returnCode == 0:  # try to do analysis only if containers run without errors

                    if isRunning:
                        dockerComposeSuccess += 1

                        containerInjectionResults = []

                        runInfo = DockerComposeRunInfo(realDockerComposePath, portsWithHttpResponse, timeToGetRunning,
                                                       returnCode, isRunning, isTimeout, portsExposedManually,
                                                       envAddedManually, envPathUsed, addedExternalNetworkManually,
                                                       InjectionInfo(containerInjectionResults))
                        dockerComposeRunsResult.append(runInfo)
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
                            softCleanCookieHunterDB()  # clean cookies in misc_cookies collection
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
                                        pathCoverage = runCodeCoverageAnalysis(url, repoName, index, domain, port, loginCookies,
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
                        dockerComposeTimeout += 1
                        print("Not enough time to run repo")
                        runInfo = DockerComposeRunInfo(realDockerComposePath, portsWithHttpResponse, timeToGetRunning,
                                                       returnCode, isRunning, isTimeout, portsExposedManually,
                                                       envAddedManually, envPathUsed, addedExternalNetworkManually)
                        dockerComposeRunsResult.append(runInfo)
                    else:
                        dockerComposeError += 1

                        print(f"Error: not running and not timeout {repoInfo.getRepoPath()}!")
                        runInfo = DockerComposeRunInfo(realDockerComposePath, portsWithHttpResponse, timeToGetRunning,
                                                       returnCode, isRunning, isTimeout, portsExposedManually,
                                                       envAddedManually, envPathUsed, addedExternalNetworkManually)
                        dockerComposeRunsResult.append(runInfo)
                else:
                    dockerComposeNotRunning += 1
                    print("Skipping repo because of return code of docker compose")
                    runInfo = DockerComposeRunInfo(realDockerComposePath, [], -1, returnCode)
                    dockerComposeRunsResult.append(runInfo)


                print()
                # clean environment to be ready for next docker-compose
                cleanEnvironment(logPathForCurrentDockerCompose, portsExposedManually)
                counterDockerPulls += 1
                counterDockerPullsForPrune += 1
                print()

            repoRunInfo = DockerRepoRunInfo(repoName=repoName, repoURL="", repoPath=repoPath,
                                            dockerComposeRuns=dockerComposeRunsResult,
                                            dockerComposeSuccess=dockerComposeSuccess,
                                            dockerComposeTimeout=dockerComposeTimeout,
                                            dockerComposeError=dockerComposeError,
                                            dockerComposeNotRunning=dockerComposeNotRunning)

            if dockerComposeSuccess > 0:
                counterReposRunning += 1
                isRepoRunning = True

            runningDockerComposeRepos.append(repoRunInfo)

    except Exception as err:
        print("An error occurred")
        print(err)
        errorCrashRepos.append(repoInfo)
        counterErrorCrashRepos += 1

    finally:  # clean and delete repo
        print("Cleaning environment...")

        # clean environment for next run
        cleanEnvironment()

        deleteDirAndAllContents(f"{DEFAULT_DIR_FOR_REPOS}{TOKEN_SEPARATOR}{repoInfo.getRepoName()}")

        print("Cleaned!")
        print('\n')
        print(f"Number of repos: {counterRepos}")
        print(f"Number of repos with dockercompose: {counterReposWithDockercompose}")
        print(f"Number of repos RUN correctly (with at least a docker-compose): {counterReposRunning}")
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
            f.write(json.dumps(runningDockerComposeRepos, indent=4))
            f.flush()

        with open(
                f"{DEFAULT_DIR_FOR_OUTPUTS}{TOKEN_SEPARATOR}{RUN_TIME_STR}{TOKEN_SEPARATOR}{RUN_TIME_STR}_{DEFAULT_FILENAME_FOR_STATS}_{inputFileName}.txt",
                "w") as f:
            f.write(f"Number of repos: {counterRepos}\n")
            f.write(f"Number of repos with dockercompose: {counterReposWithDockercompose}\n")
            f.write(f"Number of repos RUN (with at least a docker-compose): {counterReposRunning}\n")
            f.write(f"Number of repos with ERRORS: {counterErrorCrashRepos}\n")
            f.write(f"Number of repos with CLONE ERROR {counterErrorCloneRepos}\n")
            f.flush()
