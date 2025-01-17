import csv
import re
import sys

RESERVED_CHARS = "<>()[]{},;-:\'\"`="

REGEXP_WORDS_USERNAME = r"(user|username|user_name|user-name)"
REGEXP_WORDS_PASSWORD = r"(password|pwd|passwd|new_password)"
REGEXP_WORDS_EMAIL = r"(e-mail|email|mail)"

# match strings like password:pass
REGEXP_COMMON_CASE_01 = r"(?:[\"'])*([a-zA-Z-_]*)(?:[\"'])*\s*:\s*(?:[\"'])*([^\"',\^\[\] :]*)(?:[\"'])*"
# match strings like password=pass
REGEXP_COMMON_CASE_02 = r"(?:[\"'])*([a-zA-Z-_]*)(?:[\"'])*\s*=\s*(?:[\"'])*([^\"',\^\[\] :]*)(?:[\"'])*"

REGEXP_COMMON_CASE_03 = r"CREATE USER\s+(?:[\"'])*([a-zA-Z-_]*)(?:[\"'])*\s+WITH PASSWORD\s+(?:[\"'])*([^\"'\^\[\]]*)(?:[\"'])*"

REGEXP_URL_USER_PASSWORD_01 = r"\/\/([a-z-Z]*):([a-z-Z]*)@"


def contains_any_char(mystring, substring):
    return any(char in mystring for char in substring)


def is_there(string, pattern):
    match = re.findall(pattern, string, re.IGNORECASE)
    return len(match) > 0


def extractCredentialsFromFileDict(fileDict):
    #
    result = set()
    usernames = []
    passwords = []

    for (rowNumber, credentialsSet) in sorted(fileDict.items()):
        # print(f"ROW: {rowNumber} - Credentials: {credentialsSet}")

        usernames = [value for key, value in credentialsSet if key == 'USERNAME' or key == 'EMAIL'] \
                    + usernames  # keep previous row usernames if they are not matched
        passwords = [value for key, value in credentialsSet if key == 'PASSWORD']

        if len(usernames) > 0 and len(passwords) > 0:
            # try all combinations of username/password in the same row
            for username in usernames:
                for password in passwords:
                    result.add((username, password))
            if len(passwords) > 0:  # we used all usernames here and we do not need to search for passwords in next row
                usernames = []

    return result


def analyzeCredentialDiggerLogFile(filepath):
    # extract dict of usernames, email, and passwords together with rownumber, per file, from log file

    dictOfResults = dict()
    with open(filepath, mode='r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        csv.field_size_limit(sys.maxsize) # allow csv module to accept very large fields
        for row in reader:
            row_id = row['id']
            file_name = row['file_name']
            commit_id = row['commit_id']
            line_number = int(row['line_number'])
            snippet = row['snippet']
            repo_url = row['repo_url']
            rule_id = row['rule_id']
            state = row['state']
            timestamp = row['timestamp']
            rule_regex = row['rule_regex']
            rule_category = row['rule_category']
            rule_description = row['rule_description']

            match_01 = re.findall(REGEXP_COMMON_CASE_01, snippet, re.IGNORECASE)
            match_02 = re.findall(REGEXP_COMMON_CASE_02, snippet, re.IGNORECASE)
            match_03 = re.findall(REGEXP_COMMON_CASE_03, snippet, re.IGNORECASE)
            match_url_01 = re.findall(REGEXP_URL_USER_PASSWORD_01, snippet, re.IGNORECASE)

            rowDictOfFile = dictOfResults.get(file_name, dict())

            for (first_match, second_match) in match_01 + match_02 + match_03:
                second_match = second_match if not contains_any_char(second_match, RESERVED_CHARS) else ""

                if len(second_match) > 0:
                    if is_there(first_match, REGEXP_WORDS_USERNAME):
                        rowValues = rowDictOfFile.get(line_number, set())
                        rowValues.add(('USERNAME', second_match))
                        rowDictOfFile[line_number] = rowValues


                    elif is_there(first_match, REGEXP_WORDS_PASSWORD):
                        rowValues = rowDictOfFile.get(line_number, set())
                        rowValues.add(('PASSWORD', second_match))
                        rowDictOfFile[line_number] = rowValues

                    elif is_there(first_match, REGEXP_WORDS_EMAIL):
                        rowValues = rowDictOfFile.get(line_number, set())
                        rowValues.add(('EMAIL', second_match))
                        rowDictOfFile[line_number] = rowValues

            for (username, password) in match_url_01:
                rowValues = rowDictOfFile.get(line_number, set())
                rowValues.add(('USERNAME', username))
                rowValues.add(('PASSWORD', password))
                rowDictOfFile[line_number] = rowValues

            if len(rowDictOfFile) > 0:
                dictOfResults[file_name] = rowDictOfFile

    return dictOfResults
