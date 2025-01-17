# This script extracts credentials from Credential Digger CSV log files.
# It takes a parent directory path as input, where a subdirectory named "results"
# is expected to contain CSV log files. The script analyzes each CSV file, extracts
# unique credentials, and saves them into a single JSON output file in the parent directory.
#
# Prerequisites:
#   - Credential Digger must be run to generate CSV output files.
#
# Usage:
#   - Provide the path to the parent directory containing the "results" directory
#     with Credential Digger CSV log files, using the -i flag.
#     python3 runCredentialExtractorFromResults.py -i outputs/<parent-dir-of-results-dir>
#   - Example: python3 runCredentialExtractorFromResults.py -i outputs/2024_05_03

import argparse
import json
import os

from util.credentialsExtraction import analyzeCredentialDiggerLogFile, extractCredentialsFromFileDict

parser = argparse.ArgumentParser()
# and add arguments to the parser
parser.add_argument("-i", "--input", dest="inputPath",
                    help="Input dir path that contains the dir where there are .csv results of Credentials-Digger",
                    required=True)

args = parser.parse_args()

if args.inputPath is None:
    raise Exception("Argument Input Path missing!")

outputPathDir = args.inputPath
pathDirWithResults = os.path.join(outputPathDir, "results") #

allFiles = os.listdir(pathDirWithResults)
csvFiles = [file for file in allFiles if file.endswith(".csv")]
results = dict()

for csvFile in csvFiles:
    repoFilename = os.path.splitext(os.path.basename(csvFile))[0]  # filename without extensions
    print(f"Processing repo: {repoFilename} csv: {csvFile}")

    dictOfResults = analyzeCredentialDiggerLogFile(os.path.join(pathDirWithResults, csvFile))
    credentialsSet = set()  # use set to remove duplicates
    for (filename, fileDict) in dictOfResults.items():
        extractCredentialsSet = extractCredentialsFromFileDict(fileDict)
        credentialsSet = credentialsSet.union(extractCredentialsSet)

    credentialsList = []
    # convert to list of list
    for (username, password) in credentialsSet:
        credentialsList.append([str(username), str(password)])

    # print(credentialsList)
    results[repoFilename] = credentialsList

# save results dictionary to JSON file
print("Saving json output...")
jsonPath = os.path.join(outputPathDir, 'credentials_cd.json')
with open(jsonPath, 'w') as f:
    json.dump(results, f, indent=4)

print("Done!")
