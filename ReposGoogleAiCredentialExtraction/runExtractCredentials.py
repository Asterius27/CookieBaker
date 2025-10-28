# This script extracts potential credentials from various files (READMEs and .env) within repositories using
# Google's Gemini AI. It takes a JSON file containing repository information as input.
# The script iterates through each repository, prompts Gemini AI to extract credentials,
# and saves the results in a JSON file. It also keeps track of files that could not be parsed.
#
# Prerequisites:
#   - The config.py file must be correctly set up with necessary API keys and settings.
#
# Usage:
#   - Pass the path to the input JSON file containing repository information using the -i flag.
#   - Example: python3 runExtractCredentials.py -i scraped_repos.json

import argparse
import json
import os
import time

from config import DEFAULT_DIR_FOR_OUTPUTS, RUN_TIME_STR, TIME_SECONDS_BETWEEN_REQUESTS
from models.RepositoryInfo import RepositoryInfo
from util.askToGemini import extractCredentialFromFile
from util.fileUtil import createDirectoryIfNotExists

keywords = [
    "readme",
    "docker",
    "setting",
    "config",
    "environment",
    "makefile",
    "setup",
    "changelog",
    "todo",
    "properties",
    "profile",
    "secrets",
    "credentials",
    "about",
    "notice"
]

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

createDirectoryIfNotExists(DEFAULT_DIR_FOR_OUTPUTS)
createDirectoryIfNotExists(os.path.join(DEFAULT_DIR_FOR_OUTPUTS, RUN_TIME_STR))
results = dict()

wronglyParsedFiles = dict()

for repoInfo in entryList:
    sourcePath = repoInfo.getRepoPath()
    repoName = repoInfo.getRepoName()

    print(f"\n--- REPO: {repoName} at {sourcePath}\n")

    envFiles = repoInfo.getEnvFilePaths()
    mdFiles = repoInfo.getMarkdownFilePaths()
    rstFiles = repoInfo.getRstFilePaths()

    jsonFiles = repoInfo.getJsonFilePaths()
    ymlFiles = repoInfo.getYmlFilePaths()
    iniFiles = repoInfo.getIniFilePaths()

    filesToTest = envFiles + mdFiles + rstFiles + jsonFiles + ymlFiles + iniFiles
    filesToTest = [
       path for path in filesToTest
       if any(keyword in os.path.basename(path).lower() for keyword in keywords)
    ]

    print(f"Files to be tested: {len(filesToTest)}")
    credentials = []
    for file in filesToTest:
        print(f"Asking {file} to Google AI...")

        # Extract credentials using Google Gemini AI
        isOk, jsonOutput = extractCredentialFromFile(file)

        if not isOk:
            # If there was a parsing error, add the file to the wronglyParsedFiles list
            alreadyExistingFileList = wronglyParsedFiles.get(repoName, [])
            alreadyExistingFileList.append(file)
            wronglyParsedFiles[repoName] = alreadyExistingFileList
        else:
            # If parsing was successful, extract credentials from the JSON output
            extractedCredential =  jsonOutput.get("credentials", [])

            print(f"Output: {extractedCredential}")
            if len(extractedCredential) > 0:
                for elem in extractedCredential:
                    username = elem.get("username", "")
                    password = elem.get("password", "")
                    if username != "" and password != "":
                        credentials.append([username, password])
        print(f"Waiting {TIME_SECONDS_BETWEEN_REQUESTS} seconds before next request")
        time.sleep(TIME_SECONDS_BETWEEN_REQUESTS)

    if len(credentials) > 0:
        # If credentials were found, store them in the results dictionary
        results[repoName] = credentials

# save results dictionary to JSON file
print("Saving json output...")
jsonPath = os.path.join(DEFAULT_DIR_FOR_OUTPUTS, RUN_TIME_STR, 'credentials_ai.json')
with open(jsonPath, 'w') as f:
    f.write(json.dumps(results, indent=4))
    f.flush()

print(f"Repo with at least one file with parsing error: {len(wronglyParsedFiles.items())}")
for key, value in wronglyParsedFiles.items():
    print(f"{key}")
    for elem in value:
        print(elem)
    print()


print('Done!')

