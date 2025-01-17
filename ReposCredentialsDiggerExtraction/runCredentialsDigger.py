# This script automates the process of scanning GitHub repositories for credentials using Credential Digger.
# It takes a JSON file containing repository information as input, clones each repository,
# scans it using Credential Digger, and stores the results in a designated output directory.
#
# Prerequisites:
#   - Credential Digger source code must be present in a directory named "credential-digger-main"
#     within the same directory as this script. (Download it from https://github.com/SAP/credential-digger)
#   - Docker must be installed and running.
#   - The config.py file must be correctly set up with necessary API keys and settings.
#
# Usage:
#   - Provide the path to the input JSON file containing repository information using the -i flag.
#     python3 runCredentialsDigger.py -i <json-with-scraping-of-repos-created-by-scraper.json>
#   - Example: python3 runCredentialsDigger.py -i scraped_repos.json

import argparse
import json
import os
import sys

from config import DEFAULT_DIR_FOR_LOGS, RUN_TIME_STR, DEFAULT_DIR_FOR_REPOS, DEFAULT_DIR_FOR_OUTPUTS
from models.RepositoryInfo import RepositoryInfo
from util.Logger import Logger
from util.credentialDiggerUtil import turnOnCredentialsDigger, scanRepoCredentialsDigger
from util.fileUtil import checkIfDirExists, deleteDirAndAllContents, createDirectoryIfNotExists, copyDir, removeSymlinks


# do NOT change! strictly related with docker compose and docker exec commands
WHERE_RESULTS_ARE_GENERATE = os.path.join("credentials_digger", "results")
WHERE_RESULTS_ARE_MOVED = os.path.join(DEFAULT_DIR_FOR_OUTPUTS, RUN_TIME_STR)

sys.stdout = Logger(os.path.join(DEFAULT_DIR_FOR_LOGS, RUN_TIME_STR), f"{RUN_TIME_STR}_terminal")

print(f"\n\nNEW RUN {RUN_TIME_STR}\n\n")

parser = argparse.ArgumentParser()
# and add arguments to the parser
parser.add_argument("-i", "--input", dest="inputFilename", help="Input File", required=True)

args = parser.parse_args()

if args.inputFilename is None:
    raise Exception("Argument Input file missing!")

inputFilePath = args.inputFilename

f = open(inputFilePath)

# returns JSON object as a dictionary
entryList = json.load(f, object_hook=lambda d: RepositoryInfo(**d))

# delete possibly previous "repos" dir
if checkIfDirExists(DEFAULT_DIR_FOR_REPOS):
    deleteDirAndAllContents(DEFAULT_DIR_FOR_REPOS)

# some dirs for outputs, logs and temp location of local repos
createDirectoryIfNotExists(DEFAULT_DIR_FOR_REPOS)
createDirectoryIfNotExists(DEFAULT_DIR_FOR_OUTPUTS)
createDirectoryIfNotExists(DEFAULT_DIR_FOR_LOGS)

createDirectoryIfNotExists(os.path.join(DEFAULT_DIR_FOR_OUTPUTS, RUN_TIME_STR))
createDirectoryIfNotExists(os.path.join(DEFAULT_DIR_FOR_LOGS, RUN_TIME_STR))

createDirectoryIfNotExists(WHERE_RESULTS_ARE_GENERATE)
createDirectoryIfNotExists(WHERE_RESULTS_ARE_MOVED)

turnOnCredentialsDigger()

for repoInfo in entryList:
    sourcePath = repoInfo.getRepoPath()
    repoName = repoInfo.getRepoName()

    print(f"\n--- REPO: {repoName} at {sourcePath}\n")

    localRepoCopy = os.path.join(DEFAULT_DIR_FOR_REPOS, repoName)
    copyDir(sourcePath, localRepoCopy)
    removeSymlinks(localRepoCopy)

    mountedPath = os.path.join('/repos', repoName)
    # run credential digger in the local copy of the repo
    scanRepoCredentialsDigger(mountedPath, repoName)

    print("Cleaning for next repo...")
    deleteDirAndAllContents(localRepoCopy)

print("All repos scanned!")
print(f"Moving all results from {WHERE_RESULTS_ARE_GENERATE} to {WHERE_RESULTS_ARE_MOVED}")
copyDir(WHERE_RESULTS_ARE_GENERATE, WHERE_RESULTS_ARE_MOVED)
deleteDirAndAllContents(WHERE_RESULTS_ARE_GENERATE)
print("DONE!")
