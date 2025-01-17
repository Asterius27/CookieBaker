import json

"""
This script takes the merged results and for each login and signup function/class found it matches its corresponding URL, giving in output a list of signup and login endpoints
"""

LIST_NAME = "login"
FRAMEWORK = "flask"

# LIST_NAME = "login"
# FRAMEWORK = "django"

# LIST_NAME = "signup"
# FRAMEWORK = "flask"

# LIST_NAME = "signup"
# FRAMEWORK = "django"

DOCKERSET = "_dockerfile"
# DOCKERSET = "_dockercompose"

file_path = "merged_results/" + FRAMEWORK + DOCKERSET + "/repos_" + LIST_NAME + "_view_list.txt"
endpoints_path = "merged_results/" + FRAMEWORK + DOCKERSET + "/repos_endpoints_list.txt"
if FRAMEWORK == "django":
    leftover_path = "merged_results/" + FRAMEWORK + DOCKERSET + "/all_endpoints.txt"
if FRAMEWORK == "flask":
    leftover_path = "merged_results/" + FRAMEWORK + DOCKERSET + "/repos_endpoints_list.txt"
endpoints_dict = {}
file_dict = {}
result_dict = {}
leftover_urls = {}
leftover_login_dict = {}
leftover_signup_dict = {}
leftover_no_url = {}

def contains_substrs(string, substr1, substr2):
    substrings = string.split('/')
    for substring in substrings:
        if substr1 in substring and substr2 in substring:
            return True
    return False

def clean_up_url(url):
    return url.replace("^", "").replace("$", "").replace("//", "/")

def generate_dict(dct, leftover_dct, path):
    with open(path, "r") as f:
        previous_line = None
        for line in f:
            l = line.strip()
            if l.startswith("URL: "):
                url = l.split(" ")[1]
                repo_name = url.split("/")[3] + "_" + url.split("/")[4]
            if l.startswith("| ") and (previous_line.startswith("| ") or previous_line.startswith("+-")):
                info = list(filter(None, l.replace(" ", "").split("|")))
                if len(info) == 3 and clean_up_url(info[2]):
                    dct.setdefault(repo_name, []).append((info[0] + info[1], clean_up_url(info[2])))
                if len(info) == 2 and LIST_NAME in path:
                    dct.setdefault(repo_name, []).append(info[0] + info[1])
                if len(info) == 1 and LIST_NAME not in path and clean_up_url(info[0]):
                    dct.setdefault(repo_name, []).append(("No Function", clean_up_url(info[0])))
                if len(info) == 1 and LIST_NAME in path and clean_up_url(info[0]):
                    leftover_dct.setdefault(repo_name, []).append(clean_up_url(info[0]))
            previous_line = line

def generate_leftover_dict(dct_login, dct_signup, path):
    with open(path, "r") as f:
        previous_line = None
        for line in f:
            l = line.strip()
            if l.startswith("URL: "):
                url = l.split(" ")[1]
                repo_name = url.split("/")[3] + "_" + url.split("/")[4]
            if l.startswith("| ") and (previous_line.startswith("| ") or previous_line.startswith("+-")):
                info = list(filter(None, l.replace(" ", "").split("|")))
                if len(info) == 3 and "login" in info[2].lower():
                    dct_login.setdefault(repo_name, []).append(clean_up_url(info[2]))
                if len(info) == 3 and ("signup" in info[2].lower() or "register" in info[2].lower() or contains_substrs(info[2].lower(), "add", "user")):
                    dct_signup.setdefault(repo_name, []).append(clean_up_url(info[2]))
                if len(info) == 1 and "login" in info[0].lower():
                    dct_login.setdefault(repo_name, []).append(clean_up_url(info[0]))
                if len(info) == 1 and ("signup" in info[0].lower() or "register" in info[0].lower() or contains_substrs(info[0].lower(), "add", "user")):
                    dct_signup.setdefault(repo_name, []).append(clean_up_url(info[0]))
            previous_line = line

def merge_dicts(dict1, dict2):
    for url in dict1:
        if url in dict2:
            dict2[url] += dict1[url]
        else:
            dict2[url] = dict1[url]

generate_dict(endpoints_dict, {}, endpoints_path)
generate_dict(file_dict, leftover_urls, file_path)
generate_leftover_dict(leftover_login_dict, leftover_signup_dict, leftover_path)

for url in file_dict:
    for identifier in file_dict[url]:
        if url in endpoints_dict:
            for first, second in endpoints_dict[url]:
                if first == identifier:
                    result_dict.setdefault(url, []).append(second)
        else:
            leftover_no_url.setdefault(url, []).append(identifier)

merge_dicts(leftover_urls, result_dict)
print(len(result_dict))
if LIST_NAME == "signup":
    print(len(leftover_signup_dict))
    merge_dicts(leftover_signup_dict, result_dict)
if LIST_NAME == "login":
    print(len(leftover_login_dict))
    merge_dicts(leftover_login_dict, result_dict)

for url in result_dict:
    result_dict[url] = list(set(result_dict[url]))

filtered_dict = {
    key: [item for item in value if ("<" not in item or ">" not in item) and ("(" not in item or ")" not in item)]
    for key, value in result_dict.items()
}

filtered_dict = {key: value for key, value in filtered_dict.items() if value}

print(len(filtered_dict))

with open("extracted_endpoints/" + FRAMEWORK + DOCKERSET + "_" + LIST_NAME + "_endpoints.json", "w") as json_file:
    json.dump(filtered_dict, json_file, indent=4)

with open("extracted_endpoints/" + FRAMEWORK + DOCKERSET + "_" + LIST_NAME + "_no_endpoints.json", "w") as json_file:
    json.dump(leftover_no_url, json_file, indent=4)
