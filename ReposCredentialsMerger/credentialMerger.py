# This script merges multiple JSON files containing credentials, removing duplicate entries.
# It takes one or more JSON file paths as input, merges the credential data under common keys,
# and saves the merged data to a new JSON file in a designated output directory.
#
# Usage:
#   - Pass one or more paths to JSON files to merge using the -i flag.
#     python3 credentialMerger.py -i path/to/file1.json path/to/file2.json path/to/file3.json ...
#   - Example: python3 credentialMerger.py -i file1.json file2.json file3.json

import argparse
import json
import os

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


parser = argparse.ArgumentParser()

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

print("Saving output...")
save_json(merged_json, os.path.join(DEFAULT_DIR_FOR_OUTPUTS, RUN_TIME_STR, f"{RUN_TIME_STR}_credentials.json"))

print("Done!")
