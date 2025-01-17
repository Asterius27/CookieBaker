import json
import matplotlib.pyplot as plt
from pathlib import Path
import os

"""
This script aggregates the results from the compare_puppeteer.py script and generates some graphs (useful to better understand the code coverage results)
"""

def sum_nested_values(data):
    total = 0
    if isinstance(data, dict):
        for value in data.values():
            total += sum_nested_values(value)
    elif isinstance(data, (int, float)):
        total += data
    return total

def load_comparison_results(results_path):
    with open(results_path, "r") as f:
        return json.load(f)

def aggregate_overlap_data(comparison_results, missing_scripts_aggregates, overlap_aggregates, comparison_file, gt):
    site_aggregates = {}
    file_site = comparison_file.stem.split("--")[1].split("_")[0]

    missing_scripts_aggregates.setdefault(file_site, {})
    missing_scripts_aggregates[file_site].setdefault("extra_scripts_in_1", 0)
    missing_scripts_aggregates[file_site].setdefault("extra_scripts_in_2", 0)
    missing_scripts_aggregates[file_site].setdefault("extra_scripts_in_1_coverage", 0)
    missing_scripts_aggregates[file_site].setdefault("extra_scripts_in_2_coverage", 0)
    overlap_aggregates.setdefault(file_site, {})
    overlap_aggregates[file_site].setdefault("total_overlap", 0)
    overlap_aggregates[file_site].setdefault("total_non_overlap_1", 0)
    overlap_aggregates[file_site].setdefault("total_non_overlap_2", 0)
    missing_scripts_aggregates[file_site]["extra_scripts_in_1"] += len(comparison_results['missing_in_2'].keys())
    missing_scripts_aggregates[file_site]["extra_scripts_in_2"] += len(comparison_results['missing_in_1'].keys())
    missing_scripts_aggregates[file_site]["extra_scripts_in_1_coverage"] += sum(comparison_results['missing_in_2'].values())
    missing_scripts_aggregates[file_site]["extra_scripts_in_2_coverage"] += sum(comparison_results['missing_in_1'].values())
    gt["with_cookies_extra_coverage"] += sum(comparison_results['missing_in_2'].values())
    gt["without_cookies_extra_coverage"] += sum(comparison_results['missing_in_1'].values())

    for site, overlap_data in comparison_results['overlap_analysis'].items():
        if site not in site_aggregates:
            site_aggregates[site] = {
                "total_overlap": 0,
                "total_non_overlap_1": 0,
                "total_non_overlap_2": 0
            }
        
        site_aggregates[site]["total_overlap"] += overlap_data["total_overlap"]
        site_aggregates[site]["total_non_overlap_1"] += overlap_data["total_non_overlap_1"]
        site_aggregates[site]["total_non_overlap_2"] += overlap_data["total_non_overlap_2"]
        overlap_aggregates[file_site]["total_overlap"] += overlap_data["total_overlap"]
        overlap_aggregates[file_site]["total_non_overlap_1"] += overlap_data["total_non_overlap_1"]
        overlap_aggregates[file_site]["total_non_overlap_2"] += overlap_data["total_non_overlap_2"]
        gt["total_overlap"] += overlap_data["total_overlap"]
        gt["with_cookies_extra_coverage"] += overlap_data["total_non_overlap_1"]
        gt["without_cookies_extra_coverage"] += overlap_data["total_non_overlap_2"]

    return site_aggregates

def aggregate_missing_files(missing_files, gt):
    missing_aggregate_dict = {}
    missing_aggregate_dict["extra_urls_with_cookies"] = len(missing_files["missing_in_folder_2"])
    missing_aggregate_dict["extra_urls_without_cookies"] = len(missing_files["missing_in_folder_1"])
    missing_aggregate_dict["extra_urls_with_cookies_coverage"] = sum_nested_values(missing_files["missing_in_folder_2_coverage"])
    missing_aggregate_dict["extra_urls_without_cookies_coverage"] = sum_nested_values(missing_files["missing_in_folder_1_coverage"])
    gt["with_cookies_extra_coverage"] += sum_nested_values(missing_files["missing_in_folder_2_coverage"])
    gt["without_cookies_extra_coverage"] += sum_nested_values(missing_files["missing_in_folder_1_coverage"])
    return missing_aggregate_dict

def plot_overlap_data(site_aggregates, output_path="overlap_analysis.png"):
    sites = list(site_aggregates.keys())
    total_overlap = [site_aggregates[site]["total_overlap"] for site in sites]
    total_non_overlap_1 = [site_aggregates[site]["total_non_overlap_1"] for site in sites]
    total_non_overlap_2 = [site_aggregates[site]["total_non_overlap_2"] for site in sites]
    x = range(len(sites))
    width = 0.25

    plt.figure(figsize=(10, 6))
    plt.bar(x, total_overlap, width=width, label="Total Overlap", color="green")
    plt.bar([i + width for i in x], total_non_overlap_1, width=width, label="Non-Overlap Folder With Cookies", color="red")
    plt.bar([i + 2 * width for i in x], total_non_overlap_2, width=width, label="Non-Overlap Folder Without Cookies", color="blue")
    plt.xlabel("Sites")
    plt.ylabel("Coverage (Number of Bytes)")
    plt.title("Overlap and Non-Overlap Analysis per Site")
    plt.xticks([i + width for i in x], sites, rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def plot_missing_scripts_common_sites(aggregates, key1, key2, title="", output_path="missing_scripts_analysis.png", title_name=" Scripts"):
    sites = list(aggregates.keys())
    total_missing_1 = [aggregates[site][key1] for site in sites]
    total_missing_2 = [aggregates[site][key2] for site in sites]
    x = range(len(sites))
    width = 0.25

    plt.figure(figsize=(10, 6))
    plt.bar(x, total_missing_1, width=width, label=f"Extra{title_name} in Run With Cookies{title}", color="green")
    plt.bar([i + width for i in x], total_missing_2, width=width, label=f"Extra{title_name} in Run Without Cookies{title}", color="red")
    plt.xlabel("Sites")
    plt.ylabel(f"Extra{title_name}{title}")
    plt.title(f"Extra{title_name}{title} Analysis per Site")
    plt.xticks([i + width for i in x], sites, rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

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
                result_parent_folder = os.path.join(port_folder, "comparison_results")

                if not os.path.isdir(result_parent_folder):
                    print(f"Skipping empty folder: {result_parent_folder}")
                    continue

                if not os.listdir(result_parent_folder):
                    print(f"Skipping empty folder: {result_parent_folder}")
                    continue

                creds = os.listdir(result_parent_folder)
                for cred in creds:
                    result_folder = os.path.join(result_parent_folder, cred)
                    if os.path.isdir(result_folder):
                        grand_total = {
                            "total_overlap": 0,
                            "with_cookies_extra_coverage": 0,
                            "without_cookies_extra_coverage": 0
                        }
                        missing_scripts_aggregates = {}
                        overlap_aggregates = {}
                        for comparison_file in Path(result_folder).glob("comparison_*.json"):
                            overlap_output_path = f"{result_folder}/overlap_{comparison_file.stem}.png"
                            comparison_results = load_comparison_results(comparison_file)
                            site_aggregates = aggregate_overlap_data(comparison_results, missing_scripts_aggregates, overlap_aggregates, comparison_file, grand_total)
                            plot_overlap_data(site_aggregates, overlap_output_path)

                        plot_overlap_data(overlap_aggregates, f"{result_folder}/overlap_aggregates_analysis.png")
                        plot_missing_scripts_common_sites(missing_scripts_aggregates, "extra_scripts_in_1", "extra_scripts_in_2", output_path=f"{result_folder}/missing_scripts_analysis.png")
                        plot_missing_scripts_common_sites(missing_scripts_aggregates, "extra_scripts_in_1_coverage", "extra_scripts_in_2_coverage", " Coverage", f"{result_folder}/missing_scripts_coverage_analysis.png")
                        
                        missing_files_path = f"{result_folder}/missing_files.json"
                        missing_files = load_comparison_results(missing_files_path)
                        missing_urls_dict = aggregate_missing_files(missing_files, grand_total)

                        with open(f"{result_folder}/missing_urls_analysis.json", "w") as f:
                            json.dump(missing_urls_dict, f, indent=4)

                        with open(f"{result_folder}/grand_total.json", "w") as f:
                            json.dump(grand_total, f, indent=4)
