# python3 getStatsFromWapitiReports.py -i path/to/outputsWapiti/<date_time>
# This script navigates through the directory structure of Wapiti security scan reports and extracts various
# statistics, such as the number of crawled pages, vulnerability levels, and aggregated vulnerabilities,
# both with and without cookies. It generates a comprehensive summary of the scan results and saves them
# in both JSON and human-readable formats.
#
# The expected directory structure is:
# <inputPath>/outputsWapiti/<date_time>/<reponame>/<dockerdir>/<localhost_port>/...
#
# Usage:
#   - Run the script by passing the directory path containing the Wapiti scan outputs.
#   - Example: python3 getStatsFromWapitiReports.py -i /path/to/outputsWapiti/2025_01_15


import json
import os
import argparse

DEFAULT_FILENAME_FOR_STATS = "STATS"

# create a parser
parser = argparse.ArgumentParser()
# and add arguments to the parser
parser.add_argument("-i", "--input",
                    dest="inputPath",
                    help="Path that contains all dirs with Wapiti results",
                    required=True)
args = parser.parse_args()

if args.inputPath is None:
    raise Exception("Argument Path missing!")

path = args.inputPath


def getReportDict(numCrawledPagesCookies: int = 0, numCrawledPagesNoCookies: int = 0,
                  vulnLevelDictCookies: dict = {}, vulnLevelDictNoCookies: dict = {},
                  vulnAggregatedNumDictNoCookies: dict = {}, vulnAggregatedNumDictCookies: dict = {}) -> dict:
    """method to generate a report dictionary with default values"""
    ris = {
        'numCrawledPages': {
            'with_cookies': numCrawledPagesCookies,
            'without_cookies': numCrawledPagesNoCookies
        },
        'vulnLevelDict': {
            'with_cookies': vulnLevelDictCookies,
            'without_cookies': vulnLevelDictNoCookies
        },
        'vulnAggregatedNumDict': {
            'with_cookies': vulnAggregatedNumDictNoCookies,
            'without_cookies': vulnAggregatedNumDictCookies
        }
    }
    return ris


def saveReportJson(dict, path, filename):
    """method to save the report as a JSON file"""
    with open(os.path.join(path, filename), "w") as f:
        f.write(json.dumps(dict, indent=4))
        f.flush()


def saveReportHumanReadable(dict, path, filename):
    """method to save the report in a human-readable format"""
    with open(os.path.join(path, filename), "w") as f:
        f.write(getHumanReadableComparison(dict))
        f.flush()


def getListOfDirOfADir(dirName):
    """method to get a list of directories in the specified directory"""
    absolute_path = os.path.abspath(dirName)

    # get all entries in the directory
    entries = os.listdir(absolute_path)

    # filter out directories and return only filenames
    return [entry for entry in entries if os.path.isdir(os.path.join(absolute_path, entry))]


def getHumanReadableComparison(dataDict):
    """method to create a human-readable comparison report from the dict"""
    msg = []

    # number of crawled pages (with and without cookies)
    numCrawledPagesWith = dataDict['numCrawledPages']['with_cookies']
    numCrawledPagesWithout = dataDict['numCrawledPages']['without_cookies']
    msg.append(f"Num Crawled Pages (w/wo cookies): {numCrawledPagesWith}/{numCrawledPagesWithout}")

    msg.append("")
    msg.append("Aggregated Number of Vulnerability Levels:")

    # vulnerability levels counts (with and without cookies)
    for level, countWith in dataDict['vulnLevelDict']['with_cookies'].items():
        countWithout = dataDict['vulnLevelDict']['without_cookies'].get(level, 0)
        msg.append(f"Vuln Level {level} (w/wo cookies): {countWith}/{countWithout}")

    msg.append("")
    msg.append("Aggregated Number of Vulnerabilities:")
    # aggregated vulnerabilities counts (with and without cookies)
    for vuln_type, countWith in dataDict['vulnAggregatedNumDict']['with_cookies'].items():
        countWithout = dataDict['vulnAggregatedNumDict']['without_cookies'].get(vuln_type, 0)
        msg.append(f"{vuln_type} (w/wo cookies): {countWith}/{countWithout}")

    return "\n".join(msg)


def mergeAndSum(dict1, dict2):
    """method to merge and sum two dictionaries with similar structure"""
    result = {}

    # Iterate over the top-level keys in dict1
    for key in dict1:
        result[key] = {}

        # merging for each sub-key ('with_cookies' and 'without_cookies')
        for subkey in dict1[key]:
            # If the subkey exists in both dictionaries, sum the values
            if subkey in dict2.get(key, {}):  # Using .get() to avoid KeyError if key doesn't exist in dict2
                if isinstance(dict1[key].get(subkey, {}), dict) and isinstance(dict2[key].get(subkey, {}), dict):  # Nested dictionary check
                    result[key][subkey] = {}
                    # Handle summing inner dictionaries
                    # Ensure we don't get errors when both sub-dictionaries are empty
                    inner_keys = set(dict1[key][subkey].keys()).union(dict2[key][subkey].keys())
                    for inner_key in inner_keys:
                        result[key][subkey][inner_key] = dict1[key][subkey].get(inner_key, 0) + dict2[key][subkey].get(inner_key, 0)
                else:
                    # If not a dictionary, just sum the values directly
                    result[key][subkey] = dict1[key].get(subkey, 0) + dict2[key].get(subkey, 0)
            else:
                # If subkey is only in dict1, take the value from dict1
                result[key][subkey] = dict1[key].get(subkey, 0)

        # Add subkey values from dict2 if they do not exist in dict1
        for subkey in dict2.get(key, {}):
            if subkey not in dict1[key]:
                result[key][subkey] = dict2[key].get(subkey, 0)

    # Handle cases where a key exists in dict2 but not in dict1
    for key in dict2:
        if key not in dict1:
            result[key] = dict2[key]

    return result



def addMissingInFirstDict(firstDict, secondDict):
    """method to add missing keys from second dictionary to first dictionary"""
    # find keys that are in dict2 but not in dict1
    missingKeyInFirstDict = set(secondDict.keys()) - set(firstDict.keys())
    # add default value 0 for missing keys
    for key in missingKeyInFirstDict:
        firstDict[key] = 0
    return firstDict


def loadJsonFile(filepath) -> dict:
    data = None
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
    except Exception as ex:
        print("Error while parsing json file!")
        print(ex)
        data = None
    return data


def extractImportantInfoFromReport(reportDict: dict):
    """method to extract important information from a Wapiti report (num of crawled pages and vulnerabilities)"""
    infosDict = reportDict.get('infos', {})
    vulnDict = reportDict.get('vulnerabilities', {})

    numCrawledPages = infosDict.get('crawled_pages_nbr', 0)  # number of crawled pages
    vulnLevelDict = {}  # dict of criticality levels associated with number of occurrences
    vulnAggregatedNumDict = {}  # dict of various vulnerability type associated with number of occurrences
    for (vulnType, vulnList) in vulnDict.items():
        numVuln = len(vulnList)
        if numVuln > 0:
            vulnAggregatedNumDict[vulnType] = numVuln

        for vuln in vulnList:
            vulnLevel = vuln.get('level', -1)
            if vulnLevel != -1:
                counter = vulnLevelDict.get(vulnLevel, 0)
                vulnLevelDict[vulnLevel] = counter + 1

    return numCrawledPages, vulnLevelDict, vulnAggregatedNumDict


def extractInfoFromPort(path):
    """method to extract data from the 'with_cookies' and 'without_cookies' directories"""
    # open <path>/with_cookies/report.json
    # open <path>/without_cookies/report.json
    withCookiesJson = loadJsonFile(os.path.join(path, "with_cookies", "0","report.json"))
    withoutCookiesJson = loadJsonFile(os.path.join(path, "without_cookies","0", "report.json"))

    numCrawledPagesCookies = 0  # number of crawled pages
    vulnLevelDictCookies = {}  # dict of criticality levels associated with number of occurrences
    vulnAggregatedNumDictCookies = {}  # dict of various vulnerability type associated with number of occurrences

    numCrawledPagesNoCookies = 0
    vulnLevelDictNoCookies = {}
    vulnAggregatedNumDictNoCookies = {}

    if withCookiesJson and withoutCookiesJson:
        # print(withCookiesJson.keys())
        # print(withoutCookiesJson.keys())

        numCrawledPagesCookies, vulnLevelDictCookies, \
            vulnAggregatedNumDictCookies = extractImportantInfoFromReport(withCookiesJson)
        numCrawledPagesNoCookies, vulnLevelDictNoCookies, \
            vulnAggregatedNumDictNoCookies = extractImportantInfoFromReport(withoutCookiesJson)

        vulnAggregatedNumDictNoCookies = addMissingInFirstDict(vulnAggregatedNumDictNoCookies,
                                                               vulnAggregatedNumDictCookies)
        vulnAggregatedNumDictCookies = addMissingInFirstDict(vulnAggregatedNumDictCookies,
                                                             vulnAggregatedNumDictNoCookies)

    else:
        print("Missing one or both report.json. Analysis not possible!")

    return getReportDict(numCrawledPagesCookies, numCrawledPagesNoCookies,
                         vulnLevelDictCookies, vulnLevelDictNoCookies,
                         vulnAggregatedNumDictCookies, vulnAggregatedNumDictNoCookies)


def extractInfoFromDockerDir(path):
    """method to extract information from Docker directory (per port)"""
    # <path>/<dockerdir>/<localhost_port>/...
    dirPorts = getListOfDirOfADir(path)
    summary = getReportDict()
    for dir in dirPorts:
        dockerDir = os.path.join(path, dir)
        risFromPort = extractInfoFromPort(dockerDir)
        saveReportJson(risFromPort, dockerDir, "report_summary_port.json")
        saveReportHumanReadable(risFromPort, dockerDir, "report_summary_port.txt")
        summary = mergeAndSum(risFromPort, summary)
    return summary


def extractInfoFromRepo(path):
    """method to extract information from repository (per Docker directory)"""
    # <path>/<reponame>/<dockerdir>/<localhost_port>/...
    dirDockers = getListOfDirOfADir(path)
    ris = getReportDict()
    for dir in dirDockers:
        dockerDirPath = os.path.join(path, dir)
        risFromDocker = extractInfoFromDockerDir(dockerDirPath)
        saveReportJson(risFromDocker, dockerDirPath, "report_summary_docker.json")
        saveReportHumanReadable(risFromDocker, dockerDirPath, "report_summary_docker.txt")
        ris = mergeAndSum(risFromDocker, ris)
    return ris


def extractInfo(path):
    """method  to extract overall information (top-level directory containing repos)"""
    # <path>/outputsWapiti/<date>_<time>/<reponame>/<dockerdir>/<localhost_port>/...
    dirRepos = getListOfDirOfADir(path)
    ris = getReportDict()
    for dir in dirRepos:
        repoPath = os.path.join(path, dir)
        print(repoPath)
        risFromDocker = extractInfoFromRepo(repoPath)
        saveReportJson(risFromDocker, repoPath, "report_summary_repo.json")
        saveReportHumanReadable(risFromDocker, repoPath, "report_summary_repo.txt")
        ris = mergeAndSum(risFromDocker, ris)
        print(f"RIS {ris}")

    return ris


globalRis = extractInfo(path)

# save the final aggregated report as both JSON and human-readable format
saveReportJson(globalRis, path, "report_summary.json")
saveReportHumanReadable(globalRis, path, "report_summary.txt")

print(getHumanReadableComparison(globalRis))
print()

print("Done!")
