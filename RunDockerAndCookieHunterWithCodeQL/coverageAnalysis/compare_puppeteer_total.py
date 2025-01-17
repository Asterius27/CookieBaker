import json
import os

"""
This script takes the aggregate results computed by compare_puppeteer_graph.py, adds them up, and computes the overall results (for all repos)
"""

if __name__ == "__main__":
    root_folder = "outputsCodeCoverage/..."
    grand_grand_total = {}
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
                        grand_total_path = os.path.join(result_folder, "grand_total.json")
                        with open(grand_total_path, "r") as f:
                            grand_total = json.load(f)
                        grand_grand_total[f"{repo}_{subdir}_{port}_{cred}"] = grand_total
    with open(f"{root_folder}/grand_grand_total.json", "w") as f:
        json.dump(grand_grand_total, f, indent=4)
