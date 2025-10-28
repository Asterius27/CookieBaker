# python3 extractCredentitalsFromLogs.py -i cookie_hunter/logs/01_flask_dockercompose_incompleto/ -dc inputData/credentials/default_usernames_passwords.csv -g inputData/credentials/only_gemini_from_paper.json -ge inputData/credentials/gemini_paper_plus_gemini_extension.json -cd inputData/credentials/credentialdigger_paper_no_ml.json -cdml inputData/credentials/credentialdigger_with_ml.json

"""
This script does the following:
- extraction of "external" credentials with regex from Cookie Hunter logs
- comparison with a set of input .json files to see if extracted credentials belong to those groups (classification by credential group)
- count of total credentials attempted + average time per credential
"""

import json
import os
import zipfile
import argparse
import re
import csv


from util.fileUtil import deleteDirAndAllContents, getListOfFilnameOfADir
from urllib.parse import urlparse

DEFAULT_FILENAME_FOR_STATS = "STATS"

# Regular expressions for extracting data from log files
PATTERN_LOGINMANAGERCREDENTIALS_LOGGED_IN_WITH_CREDENTIALS = r"\[COOKIEBAKER STATS\]\[DEBUG\] \[LOGINMANAGERCREDENTIALS\]\[LOGGED_IN\] domain=\{(.*)\} lurl=\{(.*)\} success=\{(.*)\} username=\{(.*)\} password=\{(.*)\}"
PATTERN_LOGINMANAGERCREDENTIALS_LOGIN_SUCCESSFUL = "\[LoginWithAllCredentials\] Collected login cookies"

PATTERN_TIMER = "\[COOKIEBAKER STATS\] \[TIMER\] Time taken for this login form: (.*) seconds"


def containsPort(path: str, port: str):
    """Helper method to check if a given path contains a given port"""
    return port == path.split('.')[-2].split(':')[-1]


def extractAllGroupsWithContext(mainPattern, successPattern, text, rangeLow=0, rangeHigh=1):
    """
    Extract all groups from the text using `mainPattern`.
    For each match, check if `successPattern` appears within `-rangeLow` and `+rangeHigh` lines from the line matched.

    Returns: List of tuples:
      (line_number, matched_groups, success_nearby: bool)
    """
    results = []
    lines = text.splitlines()
    totalLines = len(lines)

    for idx, line in enumerate(lines):
        matches = re.findall(mainPattern, line)
        if matches:
            for match in matches:
                # Normalize match into a tuple
                matchedGroups = match if isinstance(match, tuple) else (match,)

                # Check nearby lines for success pattern
                start = max(0, idx - rangeLow)
                end = min(totalLines, idx + rangeHigh + 1)

                successNearby = any(
                    re.search(successPattern, lines[i])
                    for i in range(start, end) if i != idx
                )

                results.append((idx + 1, matchedGroups, successNearby))

    return results


# create a parser
parser = argparse.ArgumentParser()
# and add arguments to the parser
parser.add_argument("-i", "--input",
                    dest="inputPath",
                    help="Path that contains all dirs with cookie hunter results",
                    required=True)

parser.add_argument("-dc", "--defaultcredentials", dest="inputDefaultCredentialsCSV",
                    help="Input Default Credentials CSV", required=True)
parser.add_argument("-g", "--gemini", dest="inputGemini", help="Input Gemini JSON", required=True)
parser.add_argument("-ge", "--geminiextended", dest="inputGeminiExtended", help="Input Gemini Extended JSON",
                    required=True)
parser.add_argument("-cd", "--credentialdigger", dest="inputCredentialDigger", help="Input Credential Digger JSON",
                    required=True)
parser.add_argument("-cdml", "--credentialdiggerml", dest="inputCredentialDiggerML",
                    help="Input Credential Digger with ML JSON", required=True)

args = parser.parse_args()

if args.inputPath is None:
    raise Exception("Argument Path missing!")

base_dir = args.inputPath

repoResults = []

repos = set()
removedRepo = set()

geminiCreds = {}
geminiExtendedCreds = {}
defaultCredentials = set()
credentialDiggerCreds = {}
credentialDiggerWithMLCreds = {}

globalListTimes = []


def loadJson(filePath):
    with open(filePath, 'r') as f:
        return json.load(f)

if args.inputGemini:
    geminiCreds = loadJson(args.inputGemini)

if args.inputGeminiExtended:
    geminiExtendedCreds = loadJson(args.inputGeminiExtended)

if args.inputDefaultCredentialsCSV:
    with open(args.inputDefaultCredentialsCSV, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        defaultCredentials = {
            (row['username'], row['password'])
            for row in reader
            if 'username' in row and 'password' in row
        }

if args.inputCredentialDigger:
    credentialDiggerCreds = loadJson(args.inputCredentialDigger)

if args.inputCredentialDiggerML:
    credentialDiggerWithMLCreds = loadJson(args.inputCredentialDiggerML)


def areUsedDefaultCredentials(credentials):
    usedDefault = credentials.intersection(defaultCredentials)
    if usedDefault:
        return True
    else:
        return False


def areAnyCredentialsUsed(repoName, credentialsSet, credentialsForEachRepo):
    """
    Returns True if any (username, password) in credentialsSet
    is in the credentials for that repoName in credentialsForEachRepo.
    """

    # Get the list of default credentials for this repo
    credslist = credentialsForEachRepo.get(repoName, [])

    # Convert list of lists to set of tuples for fast lookup
    credsSet = set(tuple(pair) for pair in credslist)

    # Check if any of the extracted credentials match
    for cred in credentialsSet:
        if cred in credsSet:
            # print(f"Repo '{repoName}': {cred} found in given list")
            return True

    # print(f"Repo '{repoName}' used no repo-specific credentials.")
    return False


def getCredentialsFromRepoName(credentialsDict, reponame):
    return credentialsDict.get(reponame, [])


def extractAllGroupsFromText(pattern, text):
    """Helper method to extract all groups from a text using a regular expression"""
    """
        Extract all groups from the text using a regular expression.
        Returns a tuple:
            (bool: match_found, list_of_matches_with_line_numbers)
        Each match is returned as a tuple: (line_number, line_text, matched_groups)
        """
    results = []
    lines = text.splitlines()

    for line_number, line in enumerate(lines, start=1):
        matches = re.findall(pattern, line)
        for match in matches:
            # If there's more than one group, match is a tuple; otherwise, it's a string
            matched_groups = match if isinstance(match, tuple) else (match,)
            results.append((line_number, matched_groups))

    if results:
        return True, results
    else:
        return False, []


# Walk through the directory
for root, dirs, files in os.walk(base_dir):
    if root == base_dir:  # skip the root
        continue
    if not os.path.isdir(root):  # skip if not a dir (we have a dir for every repo)
        continue

    print(f"---\nREPO: {root}")
    repoName = root.rsplit('/', 1)[-1]
    zipsResults = []

    statsPath = os.path.join(root, f"{DEFAULT_FILENAME_FOR_STATS}_urls.txt")
    outputFileStats = open(statsPath, "w")

    counts = []

    credentials = set()

    for file in files:
        hasScreensZip = False
        isSignupZip = False
        isLoginZip = False
        logSaysAllGoodZip = False

        if file.endswith('.zip'):
            print(f"ZIP File: {file}")
            zip_path = os.path.join(root, file)
            if not containsPort(file, "27017") and not containsPort(file, "5672"):  # exclude mongo and rabbitmq

                # Open the zip file
                with zipfile.ZipFile(zip_path, 'r') as myzip:
                    # open log
                    if 'out.log' in myzip.namelist():
                        with myzip.open('out.log', 'r') as mylog:
                            logStr = mylog.read().decode('ascii', 'ignore')
                            if 'All good' in logStr:  # ignore the screens, and take priority from logs
                                isSignupZip = True
                                isLoginZip = True

                            matches = extractAllGroupsWithContext(
                                PATTERN_LOGINMANAGERCREDENTIALS_LOGGED_IN_WITH_CREDENTIALS,
                                PATTERN_LOGINMANAGERCREDENTIALS_LOGIN_SUCCESSFUL, logStr, 0, 3)

                            for (lineNumber, lineMatches, isCollectedCookieNearby) in matches:
                                (domain, lurl, success, username, password) = lineMatches
                                print(f"{lineNumber} - {success} - {isCollectedCookieNearby} - {username} - {password}")
                                combo = (username, password)
                                if success and isCollectedCookieNearby and (username, password) not in credentials:
                                    credentials.add(combo)

                            _, lstTimers = extractAllGroupsFromText(PATTERN_TIMER, logStr)
                            repos.add(repoName)
                            if len(lstTimers) > 0:
	                            globalListTimes +=lstTimers
            else:
                removedRepo.add(repoName)

    if len(credentials) > 0:
        areUsedDefaultCreds = areUsedDefaultCredentials(credentials)
        areUsedGeminiCreds = areAnyCredentialsUsed(repoName, credentials, geminiCreds)
        areUsedGeminiExtendedCreds = areAnyCredentialsUsed(repoName, credentials, geminiExtendedCreds)
        areUsedCredentialDiggerCreds = areAnyCredentialsUsed(repoName, credentials, credentialDiggerCreds)
        areUsedCredentialDiggerCredsWithML = areAnyCredentialsUsed(repoName, credentials, credentialDiggerWithMLCreds)

        repoResults.append((repoName, credentials,
                            areUsedDefaultCreds, defaultCredentials,
                            areUsedGeminiCreds, getCredentialsFromRepoName(geminiCreds, repoName),
                            areUsedGeminiExtendedCreds, getCredentialsFromRepoName(geminiExtendedCreds, repoName),
                            areUsedCredentialDiggerCreds, getCredentialsFromRepoName(credentialDiggerCreds, repoName),
                            areUsedCredentialDiggerCredsWithML,
                            getCredentialsFromRepoName(credentialDiggerWithMLCreds, repoName),
                            ))

print(repoResults)

outputGlobalStats = open(f"{DEFAULT_FILENAME_FOR_STATS}_CREDENTIALS.txt", "w")

outputGlobalStats.write(f"RepoName\tCredentials\tDefault\t\tGemini\t\tGeminiExtended\t\tDigger\t\tDigger ML\t\n")

for (repoName, credentials,
     areUsedDefaultCreds, defaultCreds,
     areUsedGeminiCreds, geminiRepoCreds,
     areUsedGeminiExtendedCreds, geminiExtendedRepoCreds,
     areUsedCredentialDiggerCreds, credentialDiggerRepoCreds,
     areUsedCredentialDiggerCredsWithML, credentialDiggerWithMLRepoCreds
     ) in repoResults:
    outputGlobalStats.write(
        f"{repoName}\t{credentials}\t"
        f"{areUsedDefaultCreds}\t{defaultCreds}\t"
        f"{areUsedGeminiCreds}\t{geminiRepoCreds}\t"
        f"{areUsedGeminiExtendedCreds}\t{geminiExtendedRepoCreds}\t"
        f"{areUsedCredentialDiggerCreds}\t{credentialDiggerRepoCreds}\t"
        f"{areUsedCredentialDiggerCredsWithML}\t{credentialDiggerWithMLRepoCreds}\n")

outputGlobalStats.flush()
outputGlobalStats.close()

total = 0
print(globalListTimes)
for (row, time) in globalListTimes:
    timeNum = float(time[0])
    total += timeNum
    
average = total / len(globalListTimes)
print(f"Average time per credential: {average}")
print(f"Num credential attempted: {len(globalListTimes)}")
