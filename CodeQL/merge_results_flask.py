from pathlib import Path
import os
import csv

"""
This script merges the results of the queries for Flask
"""

path = Path(__file__).parent / './merged_results/flask_dockercompose'
path.mkdir(exist_ok=True)
dockerset = "dockercompose"

def loadCSV(csvFile):
    repos = {}
    with csvFile.open(encoding="utf8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            repo = row["repo_url"].split("/")[4]
            owner = row["repo_url"].split("/")[3]
            repos[owner + "_" + repo] = row["repo_url"]
    return repos

def extractResults(reposDir, queryDir, queryName, result, csvDict):
    output_results = {}
    path = Path(__file__).parent / '../../../../../media/simone/Data/repositories'
    repos = os.listdir(str(path.absolute()) + "/" + reposDir)
    for repo in repos:
        if os.path.isdir(os.path.join(str(path.absolute()) + "/" + reposDir, repo)):
            dirs = os.listdir(str(path.absolute()) + "/" + reposDir + "/" + repo)
            for dir in dirs:
                if os.path.isdir(os.path.join(str(path.absolute()) + "/" + reposDir + "/" + repo, dir)) and dir.endswith("-results"):
                    queryFile = str(path.absolute()) + "/" + reposDir + "/" + repo + "/" + dir + "/" + queryDir + "/" + queryName + ".txt"
                    if os.path.isfile(queryFile):
                        with open(queryFile, "r") as output:
                            if len(output.readlines()) <= 2 and not result:
                                output.seek(0)
                                output_results[repo] = {}
                                if repo in csvDict:
                                    output_results[repo]["url"] = csvDict[repo]
                                output_results[repo]["file"] = queryFile
                                output_results[repo]["result"] = queryName + ":\n"
                                output_results[repo]["result"] += output.read()
                            output.seek(0)
                            if len(output.readlines()) > 2 and result:
                                output.seek(0)
                                output_results[repo] = {}
                                if repo in csvDict:
                                    output_results[repo]["url"] = csvDict[repo]
                                output_results[repo]["file"] = queryFile
                                output_results[repo]["result"] = queryName + ":\n"
                                output_results[repo]["result"] += output.read()
    return output_results

def saveDictsToFile(fileNames, sets, dicts):
    for i, set in enumerate(sets):
        with open(str(path.absolute()) + "/" + fileNames[i] + '.txt', 'w', encoding='UTF8') as file:
            for key in set:
                flag = False
                for dct in dicts[i]:
                    if key in dct:
                        if not flag:
                            if "url" in dct[key]:
                                file.write("URL: " + str(dct[key]["url"]) + "\n")
                            file.write("FILE: " + str(dct[key]["file"]) + "\n")
                            flag = True
                        file.write(str(dct[key]["result"]) + "\n")
                file.write("\n\n")

csv_dict = loadCSV(Path(__file__).parent / './flask_q3_whitelist_filtered.csv')
class_creating_user = extractResults(f"Flask_{dockerset}", "models", "un_extract_class_creating_user", True, csv_dict)
class_writing_to_db = extractResults(f"Flask_{dockerset}", "models", "un_extract_class_writing_to_db", True, csv_dict)
function_creating_user = extractResults(f"Flask_{dockerset}", "models", "un_extract_function_creating_user", True, csv_dict)
function_writing_to_db = extractResults(f"Flask_{dockerset}", "models", "un_extract_function_writing_to_db", True, csv_dict)
models = extractResults(f"Flask_{dockerset}", "models", "un_extract_models", True, csv_dict)
user_models = extractResults(f"Flask_{dockerset}", "models", "un_extract_user_model", True, csv_dict)
class_creating_user_field_based = extractResults(f"Flask_{dockerset}", "models", "un_extract_class_creating_user_field_based", True, csv_dict)
function_creating_user_field_based = extractResults(f"Flask_{dockerset}", "models", "un_extract_function_creating_user_field_based", True, csv_dict)
user_model_field_based = extractResults(f"Flask_{dockerset}", "models", "un_extract_user_model_field_based", True, csv_dict)

leftover_endpoints_classes = extractResults(f"Flask_{dockerset}", "endpoints", "un_extract_leftover_endpoints_classes", True, csv_dict)
leftover_endpoints = extractResults(f"Flask_{dockerset}", "endpoints", "un_extract_leftover_endpoints", True, csv_dict)
leftover_non_prefixed_endpoints_classes = extractResults(f"Flask_{dockerset}", "endpoints", "un_extract_leftover_non_prefixed_endpoints_classes", True, csv_dict)
leftover_prefixed_endpoints_classes = extractResults(f"Flask_{dockerset}", "endpoints", "un_extract_leftover_prefixed_endpoints_classes", True, csv_dict)
login_view_class = extractResults(f"Flask_{dockerset}", "endpoints", "un_extract_login_view_class", True, csv_dict)
login_view = extractResults(f"Flask_{dockerset}", "endpoints", "un_extract_login_view", True, csv_dict)
non_prefixed_endpoints_classes = extractResults(f"Flask_{dockerset}", "endpoints", "un_extract_non_prefixed_endpoints_classes", True, csv_dict)
non_prefixed_endpoints = extractResults(f"Flask_{dockerset}", "endpoints", "un_extract_non_prefixed_endpoints", True, csv_dict)
prefixed_endpoints_classes = extractResults(f"Flask_{dockerset}", "endpoints", "un_extract_prefixed_endpoints_classes", True, csv_dict)
prefixed_endpoints = extractResults(f"Flask_{dockerset}", "endpoints", "un_extract_prefixed_endpoints", True, csv_dict)
no_prefixed_endpoints = extractResults(f"Flask_{dockerset}", "endpoints", "un_extract_prefixed_endpoints", False, csv_dict)
signup_view_class = extractResults(f"Flask_{dockerset}", "endpoints", "un_extract_signup_view_class", True, csv_dict)
signup_view = extractResults(f"Flask_{dockerset}", "endpoints", "un_extract_signup_view", True, csv_dict)
all_endpoints = extractResults(f"Flask_{dockerset}", "endpoints", "un_extract_all_function_endpoints", True, csv_dict)

keys_class_creating_user = set(class_creating_user)
keys_class_writing_to_db = set(class_writing_to_db)
keys_function_creating_user = set(function_creating_user)
keys_function_writing_to_db = set(function_writing_to_db)
keys_models = set(models)
keys_user_models = set(user_models)
keys_class_creating_user_field_based = set(class_creating_user_field_based)
keys_function_creating_user_field_based = set(function_creating_user_field_based)
keys_user_model_field_based = set(user_model_field_based)
keys_leftover_endpoints_classes = set(leftover_endpoints_classes)
keys_leftover_endpoints = set(leftover_endpoints)
keys_leftover_non_prefixed_endpoints_classes = set(leftover_non_prefixed_endpoints_classes)
keys_leftover_prefixed_endpoints_classes = set(leftover_prefixed_endpoints_classes)
keys_login_view_class = set(login_view_class)
keys_login_view = set(login_view)
keys_non_prefixed_endpoints_classes = set(non_prefixed_endpoints_classes)
keys_non_prefixed_endpoints = set(non_prefixed_endpoints)
keys_prefixed_endpoints_classes = set(prefixed_endpoints_classes)
keys_prefixed_endpoints = set(prefixed_endpoints)
keys_no_prefixed_endpoints = set(no_prefixed_endpoints)
keys_signup_view_class = set(signup_view_class)
keys_signup_view = set(signup_view)
keys_all_endpoints = set(all_endpoints)

repos = keys_prefixed_endpoints.union(keys_no_prefixed_endpoints, keys_all_endpoints)

repos_without_endpoints = repos.difference(keys_prefixed_endpoints.union(keys_prefixed_endpoints_classes, keys_non_prefixed_endpoints, keys_non_prefixed_endpoints_classes, keys_leftover_endpoints, keys_leftover_endpoints_classes, keys_leftover_prefixed_endpoints_classes, keys_leftover_non_prefixed_endpoints_classes, keys_all_endpoints))
repos_without_login = repos.difference(keys_login_view.union(keys_login_view_class))
repos_without_signup = repos.difference(keys_signup_view.union(keys_signup_view_class))

repos_with_login = keys_login_view.union(keys_login_view_class)
repos_with_signup = keys_signup_view.union(keys_signup_view_class, keys_function_creating_user, keys_function_creating_user_field_based, keys_class_creating_user, keys_class_creating_user_field_based)
repos_with_endpoints = repos.difference(repos_without_endpoints)

saveDictsToFile(["class_creating_user", "class_writing_to_db", "function_creating_user", "function_writing_to_db", "models", "user_models", "class_creating_user_field_based", "function_creating_user_field_based", "user_model_field_based"],
                [keys_class_creating_user, keys_class_writing_to_db, keys_function_creating_user, keys_function_writing_to_db, keys_models, keys_user_models, keys_class_creating_user_field_based, keys_function_creating_user_field_based, keys_user_model_field_based],
                [[class_creating_user], [class_writing_to_db], [function_creating_user], [function_writing_to_db], [models], [user_models], [class_creating_user_field_based], [function_creating_user_field_based], [user_model_field_based]])

saveDictsToFile(["leftover_endpoints_classes", "leftover_endpoints", "leftover_non_prefixed_endpoints_classes", "leftover_prefixed_endpoints_classes", "login_view_class", "login_view", "non_prefixed_endpoints_classes", "non_prefixed_endpoints", "prefixed_endpoints_classes", "prefixed_endpoints", "signup_view_class", "signup_view"],
                [keys_leftover_endpoints_classes, keys_leftover_endpoints, keys_leftover_non_prefixed_endpoints_classes, keys_leftover_prefixed_endpoints_classes, keys_login_view_class, keys_login_view, keys_non_prefixed_endpoints_classes, keys_non_prefixed_endpoints, keys_prefixed_endpoints_classes, keys_prefixed_endpoints, keys_signup_view_class, keys_signup_view],
                [[leftover_endpoints_classes], [leftover_endpoints], [leftover_non_prefixed_endpoints_classes], [leftover_prefixed_endpoints_classes], [login_view_class], [login_view], [non_prefixed_endpoints_classes], [non_prefixed_endpoints], [prefixed_endpoints_classes], [prefixed_endpoints], [signup_view_class], [signup_view]])

saveDictsToFile(["repos", "repos_without_endpoints", "repos_without_login_views", "repos_without_signup_views"],
                [repos, repos_without_endpoints, repos_without_login, repos_without_signup],
                [[prefixed_endpoints, no_prefixed_endpoints], [prefixed_endpoints, no_prefixed_endpoints], [prefixed_endpoints, no_prefixed_endpoints], [prefixed_endpoints, no_prefixed_endpoints]])

saveDictsToFile(["repos_endpoints_list", "repos_login_view_list", "repos_signup_view_list", "all_endpoints"],
                [repos_with_endpoints, repos_with_login, repos_with_signup, keys_all_endpoints],
                [[prefixed_endpoints, prefixed_endpoints_classes, non_prefixed_endpoints, non_prefixed_endpoints_classes, leftover_endpoints, leftover_endpoints_classes, leftover_prefixed_endpoints_classes, leftover_non_prefixed_endpoints_classes, all_endpoints], 
                 [login_view, login_view_class], [signup_view, signup_view_class, function_creating_user, function_creating_user_field_based, class_creating_user, class_creating_user_field_based], [all_endpoints]])
