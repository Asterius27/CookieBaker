import json
import os
from itertools import combinations

"""
This script parses the output from the code coverage, comparing results with and without cookies by computing overlaps and the extra code covered by either one
"""

def load_coverage_results(folder_path):
    coverage_data = {}
    for file in os.listdir(folder_path):
        if file.endswith("_coverage-results.json"):
            file_path = os.path.join(folder_path, file)
            with open(file_path, "r") as f:
                data = json.load(f)
                coverage_data[file] = data.get("jsCoverage", [])
    return coverage_data

def unify_ranges(ranges):
    ranges = sorted(ranges, key=lambda x: x["start"])
    
    unified_ranges = []
    current_range = ranges[0]

    for next_range in ranges[1:]:
        if next_range["start"] <= current_range["end"]:
            current_range["end"] = max(current_range["end"], next_range["end"])
        else:
            unified_ranges.append(current_range)
            current_range = next_range
    unified_ranges.append(current_range)

    return unified_ranges

def calculate_overlap(ranges_1, ranges_2):
    total_overlap = 0
    total_non_overlap_1 = 0
    total_non_overlap_2 = 0

    def range_intersection(r1, r2):
        start = max(r1["start"], r2["start"])
        end = min(r1["end"], r2["end"])
        if start < end:
            return {"start": start, "end": end, "size": end - start}
        return None

    i, j = 0, 0
    while i < len(ranges_1) and j < len(ranges_2):
        r1 = ranges_1[i]
        r2 = ranges_2[j]
        intersection = range_intersection(r1, r2)
        if intersection:
            total_overlap += intersection["size"]

        if r1["end"] < r2["end"]:
            total_non_overlap_1 += r1["end"] - r1["start"]
            i += 1
        elif r2["end"] < r1["end"]:
            total_non_overlap_2 += r2["end"] - r2["start"]
            j += 1
        else:
            i += 1
            j += 1

    while i < len(ranges_1):
        total_non_overlap_1 += ranges_1[i]["end"] - ranges_1[i]["start"]
        i += 1
    while j < len(ranges_2):
        total_non_overlap_2 += ranges_2[j]["end"] - ranges_2[j]["start"]
        j += 1

    return {
        "total_overlap": total_overlap,
        "total_non_overlap_1": total_non_overlap_1,
        "total_non_overlap_2": total_non_overlap_2
    }

def total_lines(ranges):
    total = 0
    for range in ranges:
        r = range['end'] - range['start']
        total += r
    return total

def compare_coverage_results(coverage_1, coverage_2):
    result = {
        "missing_in_1": {},
        "missing_in_2": {},
        "overlap_analysis": {}
    }

    urls_1 = {entry["url"]: entry for entry in coverage_1}
    urls_2 = {entry["url"]: entry for entry in coverage_2}
    missing_in_1 = set(urls_2.keys()) - set(urls_1.keys())
    missing_in_2 = set(urls_1.keys()) - set(urls_2.keys())

    for url in missing_in_1:
        entry = urls_2[url]
        unified_ranges = unify_ranges(entry['ranges'])
        result['missing_in_1'][url] = total_lines(unified_ranges)

    for url in missing_in_2:
        entry = urls_1[url]
        unified_ranges = unify_ranges(entry['ranges'])
        result['missing_in_2'][url] = total_lines(unified_ranges)

    common_urls = set(urls_1.keys()) & set(urls_2.keys())
    for url in common_urls:
        entry_1 = urls_1[url]
        entry_2 = urls_2[url]
        unified_ranges_1 = unify_ranges(entry_1["ranges"])
        unified_ranges_2 = unify_ranges(entry_2["ranges"])
        overlap_info = calculate_overlap(unified_ranges_1, unified_ranges_2)
        result["overlap_analysis"][url] = overlap_info

    return result

def save_comparison_results(results, output_path):
    with open(output_path, "w") as f:
        json.dump(results, f, indent=4)

def save_missing_files(missing_files_1, missing_files_2, missing_scripts_coverage, output_path):
    missing_data = {
        "missing_in_folder_2": missing_files_1,
        "missing_in_folder_1": missing_files_2,
        "missing_in_folder_2_coverage": missing_scripts_coverage["missing_in_2"],
        "missing_in_folder_1_coverage": missing_scripts_coverage["missing_in_1"]
    }
    with open(output_path, "w") as f:
        json.dump(missing_data, f, indent=4)

def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            total_size += os.path.getsize(file_path)
    return total_size

def multiaccount_comparison(creds, folder_1, result_parent_folder):
    cred_pairs = list(combinations(creds, 2))
    for pair in cred_pairs:
        cred_1_folder = os.path.join(folder_1, pair[0])
        cred_2_folder = os.path.join(folder_1, pair[1])
        result_folder = os.path.join(result_parent_folder, f"{pair[0]}_{pair[1]}")
        os.makedirs(result_folder, exist_ok=True)
        coverage_data_1 = load_coverage_results(cred_1_folder)
        coverage_data_2 = load_coverage_results(cred_2_folder)

        files_1 = set(coverage_data_1.keys())
        files_2 = set(coverage_data_2.keys())

        missing_in_folder_2 = list(files_1 - files_2)
        missing_in_folder_1 = list(files_2 - files_1)
        missing_scripts_coverage = {}
        missing_scripts_coverage.setdefault('missing_in_2', {})
        missing_scripts_coverage.setdefault('missing_in_1', {})

        for file_name in missing_in_folder_1:
            urls = {entry["url"]: entry for entry in coverage_data_2[file_name]}
            for url in urls.keys():
                entry = urls[url]
                unified_ranges = unify_ranges(entry['ranges'])
                missing_scripts_coverage['missing_in_1'].setdefault(file_name, {})
                missing_scripts_coverage['missing_in_1'][file_name][url] = total_lines(unified_ranges)

        for file_name in missing_in_folder_2:
            urls = {entry["url"]: entry for entry in coverage_data_1[file_name]}
            for url in urls.keys():
                entry = urls[url]
                unified_ranges = unify_ranges(entry['ranges'])
                missing_scripts_coverage['missing_in_2'].setdefault(file_name, {})
                missing_scripts_coverage['missing_in_2'][file_name][url] = total_lines(unified_ranges)


        save_missing_files(missing_in_folder_2, missing_in_folder_1, missing_scripts_coverage, os.path.join(result_folder, "missing_files.json"))

        for file_name in files_1 & files_2:
            result = compare_coverage_results(coverage_data_1[file_name], coverage_data_2[file_name])
            output_file = os.path.join(result_folder, f"comparison_{file_name}")
            save_comparison_results(result, output_file)

if __name__ == "__main__":
    root_folder = "outputsCodeCoverage/..."
    repos = os.listdir(root_folder)
    for repo in repos:
        repo_folder = os.path.join(root_folder, repo)
        if not os.path.isdir(repo_folder):
            continue
        subdirs = os.listdir(repo_folder)
        for subdir in subdirs:
            subdir_folder = os.path.join(repo_folder, subdir)
            ports = os.listdir(subdir_folder)
            for port in ports:
                port_folder = os.path.join(subdir_folder, port)
                folder_size = get_folder_size(port_folder)
                if folder_size > 5 * 1024 * 1024 * 1024:
                    print(f"Skipping {port_folder} (size: {folder_size} bytes)")
                    continue
                folder_1 = os.path.join(port_folder, "with_cookies")
                folder_2 = os.path.join(port_folder, "without_cookies", "0")
                result_parent_folder = os.path.join(port_folder, "comparison_results")
                os.makedirs(result_parent_folder, exist_ok=True)
                
                creds = os.listdir(folder_1)
                multiaccount_comparison(creds, folder_1, result_parent_folder)

                for cred in creds:
                    cred_folder = os.path.join(folder_1, cred)
                    result_folder = os.path.join(result_parent_folder, cred)
                    os.makedirs(result_folder, exist_ok=True)
                    coverage_data_1 = load_coverage_results(cred_folder)
                    coverage_data_2 = load_coverage_results(folder_2)

                    files_1 = set(coverage_data_1.keys())
                    files_2 = set(coverage_data_2.keys())

                    missing_in_folder_2 = list(files_1 - files_2)
                    missing_in_folder_1 = list(files_2 - files_1)
                    missing_scripts_coverage = {}
                    missing_scripts_coverage.setdefault('missing_in_2', {})
                    missing_scripts_coverage.setdefault('missing_in_1', {})

                    for file_name in missing_in_folder_1:
                        urls = {entry["url"]: entry for entry in coverage_data_2[file_name]}
                        for url in urls.keys():
                            entry = urls[url]
                            unified_ranges = unify_ranges(entry['ranges'])
                            missing_scripts_coverage['missing_in_1'].setdefault(file_name, {})
                            missing_scripts_coverage['missing_in_1'][file_name][url] = total_lines(unified_ranges)

                    for file_name in missing_in_folder_2:
                        urls = {entry["url"]: entry for entry in coverage_data_1[file_name]}
                        for url in urls.keys():
                            entry = urls[url]
                            unified_ranges = unify_ranges(entry['ranges'])
                            missing_scripts_coverage['missing_in_2'].setdefault(file_name, {})
                            missing_scripts_coverage['missing_in_2'][file_name][url] = total_lines(unified_ranges)


                    save_missing_files(missing_in_folder_2, missing_in_folder_1, missing_scripts_coverage, os.path.join(result_folder, "missing_files.json"))

                    for file_name in files_1 & files_2:
                        result = compare_coverage_results(coverage_data_1[file_name], coverage_data_2[file_name])
                        output_file = os.path.join(result_folder, f"comparison_{file_name}")
                        save_comparison_results(result, output_file)
