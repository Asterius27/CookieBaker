# This script merges multiple JSON files containing credentials, removing duplicate entries.
# It takes one or more JSON file paths as input, merges the credential data under common keys,
# and saves the merged data to a new JSON file in a designated output directory.
#
# Usage:
#   - Pass one or more paths to JSON files to merge using the -i flag, and a optional defaul credential csv file using -d flag
#     python3 credentialMerger.py -i path/to/file1.json path/to/file2.json path/to/file3.json ...
#   - Example: python3 credentialMerger.py [-d defaultcreds.csv] -i file1.json file2.json file3.json

import argparse
import json
import os
import csv

from config import RUN_TIME_STR, DEFAULT_DIR_FOR_OUTPUTS



def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)


def create_directory_if_not_exists(dirName):
    if not os.path.exists(dirName):
        os.makedirs(dirName)


def merge_without_duplicates(json1, json2):
    merged_json = {}
    # create a set to track unique elements (converted to a tuple for immutability)
    seen = set()

    for key in json1:
        if key in json2:
            # combine the lists, but only add unique items
            for item in json1[key] + json2[key]:
                # Convert list to tuple to make it hashable for set comparison
                if tuple(item) not in seen:
                    seen.add(tuple(item))
                    if key not in merged_json:
                        merged_json[key] = []
                    merged_json[key].append(item)
        else:
            merged_json[key] = json1[key]

    # if json2 has keys not present in json1
    for key in json2:
        if key not in merged_json:
            merged_json[key] = []
            for item in json2[key]:
                if tuple(item) not in seen:
                    seen.add(tuple(item))
                    merged_json[key].append(item)

    return merged_json


def add_default_credentials(path, merged_json):
    default_credentials = []
    with open(args.defaultCredentialCsv, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        default_credentials = [row for row in reader]

    if len(default_credentials) > 0:
        # Convert list of dicts from CSV to list of tuples
        default_cred_tuples = [tuple(row.values()) for row in default_credentials]

        for key in merged_json:
            # Convert existing credentials to set of tuples for de-duplication
            existing_creds = {tuple(cred) for cred in merged_json[key]}

            for default_cred in default_cred_tuples:
                if default_cred not in existing_creds:
                    merged_json[key].append(list(default_cred))
                    existing_creds.add(default_cred)


parser = argparse.ArgumentParser()

# deafult credentials
parser.add_argument("-d", "--default", dest="defaultCredentialCsv", help="Default Credential CSV", required=False)
# add argument for input files (allowing multiple input files: nargs='+')
parser.add_argument("-i", "--input", dest="inputFiles", help="Input Files", required=True, nargs='+')

args = parser.parse_args()

if not args.inputFiles:
    raise Exception("At least one input file is required!")

print(f"\n\nNEW RUN {RUN_TIME_STR}\n\n")

create_directory_if_not_exists(DEFAULT_DIR_FOR_OUTPUTS)
create_directory_if_not_exists(os.path.join(DEFAULT_DIR_FOR_OUTPUTS, RUN_TIME_STR))

# load and merge jsons
merged_json = {}
for inputFilePath in args.inputFiles:
    print(f"Merging {inputFilePath}")
    json_data = load_json(inputFilePath)
    merged_json = merge_without_duplicates(merged_json, json_data)

# add default credentials to every repo in merged_json dict
if args.defaultCredentialCsv:
    add_default_credentials(args.defaultCredentialCsv, merged_json)

print("Saving output...")
save_json(merged_json, os.path.join(DEFAULT_DIR_FOR_OUTPUTS, RUN_TIME_STR, f"{RUN_TIME_STR}_credentials.json"))

print("Done!")
