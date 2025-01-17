# This script analyzes a directory of GitHub repositories, extracting various information such as
# the presence of README files, requirements files, Docker configurations, and database-related keywords.
# The script processes each repository concurrently, stores the extracted data in a JSON file,
# and generates a summary report in a text file.
#
# The directory structure expected is a root directory with subdirectories containing repositories.
# Each repository directory must be structured with a "_repo" suffix such as myrepo/myrepo_repo.
#
# Usage:
#   - Pass the path to the root directory of repositories using the -i flag.
#   - Provide the number of cores to use for parallel processing using the -c flag.
#   - Example: python3 main.py -i path/to/repos/rootdir -c 8

import argparse
import os
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from RepositoryInfo import RepositoryInfo

RUN_TIME_STR = time.strftime('%Y-%m-%d_%H-%M-%S')

DEFAULT_DIR_FOR_REPOS = "repos"
DEFAULT_DIR_FOR_OUTPUTS = "outputs"
DEFAULT_FILENAME_FOR_OUTPUT = "OUTPUT"
DEFAULT_FILENAME_FOR_ERROR = "ERROR"
DEFAULT_FILENAME_FOR_STATS = "STATS"

errorCloningRepos = []
errorRepos = []
repoInfoList = []
counterRepos = 0
counterReposErrors = 0
counterWithReadme = 0
counterWithRequirements = 0
counterWithScripts = 0
counterWithSql = 0
counterWithEnv = 0
counterWithEnvAndDockerCompose = 0

counterWithDockerCompose = 0
counterWithDockerfile = 0
counterWithDockerComposeWithoutDockerfile = 0
counterWithDockerfileWithoutDockerCompose = 0
counterWithDockerfileWithDockerCompose = 0

counterWithMultipleDockerComposePaths = 0
counterWithMultipleDockerfilePaths = 0

counterDbInfo = 0
counterDbInfoInDockerfileNotInDockerCompose = 0
counterDbInfoInDockerComposeNotInDockerfile = 0
counterDbInfoInDockerComposeAndInDockerfile = 0
counterWithRequirementAndNotDockerCompose = 0
counterWithRequirementsAndNotDockerfile = 0

counterDbInfoInDockerCompose = 0
counterDbInfoInDockerfile = 0

counterWithDockerfileWithEnvWithoutDockerCompose = 0

counterTotalNumberDockerCompose = 0
counterTotalNumberDockerfile = 0

lock = threading.Lock()

TOKEN_SEPARATOR = "/"  # linux
# TOKEN_SEPARATOR = "\\"  # windows


# create a parser
parser = argparse.ArgumentParser()
# and add arguments to the parser
parser.add_argument("-i", "--input", dest="inputPath", help="Input path of dir with repos", required=True)
parser.add_argument("-c", "--core", dest="numOfCore", help="Number of Core", required=True)
args = parser.parse_args()

if args.inputPath is None:
    raise Exception("Argument Input file missing!")

MAX_WORKERS = os.cpu_count()  # number of concurrent workers for cloning and analyzing repos as default value

if args.numOfCore is None:
    raise Exception("Argument Input file missing!")
else:
    try:
        MAX_WORKERS = int(args.numOfCore)
    except Exception as e:
        print("Core argument is not an integer! ")
        print(f"Use default value: {MAX_WORKERS}")

inputPath = args.inputPath

dbKeywordsFile = open("DBkeywords.json")
dbKeywordsList = json.load(dbKeywordsFile)
print(f"Keywords: {dbKeywordsList}")


def createDirectoryIfNotExists(dirName):
    if not os.path.exists(dirName):
        os.makedirs(dirName)


def findExactFilenameMatchIgnoreCase(paths, filename):
    for item in paths:
        itemFilename = item.split(TOKEN_SEPARATOR)[-1]
        if itemFilename.lower() == filename.lower():
            return item
    return ""


def geAllMatchesIgnoreCase(paths, filename):
    filtered = []
    for item in paths:
        itemFilename = item.split(TOKEN_SEPARATOR)[-1]
        if itemFilename.lower() == filename.lower():
            filtered.append(item)
    return filtered


def isThereMatchOfTextBetweenSymbols(filename, toBeFound):
    # compile the regex pattern
    regex = re.compile(r'\b[._-]?' + re.escape(toBeFound) + r'[._-]?\b')

    # find all matches in the filename
    matches = regex.findall(filename)

    return len(matches) > 0


def getDirsInAPath(path):
    all_items = os.listdir(path)

    # filter out files and keep only directories
    directories = [item for item in all_items if os.path.isdir(os.path.join(path, item))]
    return directories


def getDirsInAPathStartingWithCertainName(path, tail_name):
    directories = getDirsInAPath(path)

    # Filter out directories that start with the given head name
    matching_dirs = [os.path.join(path, dir) for dir in directories if dir.endswith(tail_name)]
    return matching_dirs


def getAllFiles(dirPath):
    listOfFiles = []
    for root, dirs, files in os.walk(dirPath):
        for file in files:
            # get the relative path
            relative_path = os.path.join(root, file)
            listOfFiles.append(relative_path)
    return listOfFiles


def getFilesGroupedByExtensions(listOfAllFiles):
    # print(f"Grouping files...")
    myFilesDict = {}
    for relative_path in listOfAllFiles:
        _, extension = os.path.splitext(relative_path)

        if extension in myFilesDict:
            myFilesDict[extension].append(relative_path)
        else:
            myFilesDict[extension] = [relative_path]
    return myFilesDict


def getExtensionOfFile(path):
    _, extension = os.path.splitext(path)
    return extension


def isThereDbKeywordInFile(filepath):
    with open(filepath, "r") as file:
        lines = file.readlines()
        fileContent = ''.join(lines).lower()
        for keyword in dbKeywordsList:
            if fileContent.find(keyword):
                return True
        return False


def processRepository(repoName, repoPath):
    repoInfo = None
    isThereError = False

    try:
        listOfFiles = getAllFiles(repoPath)
        print(len(listOfFiles))
        print(listOfFiles[0])

        # get dict of files by extension, grouped by extension
        filesByExtension = getFilesGroupedByExtensions(listOfFiles)

        # interesting files/groups
        readmePath = findExactFilenameMatchIgnoreCase(filesByExtension.get(".md", []), "readme.md")
        requirementsPath = findExactFilenameMatchIgnoreCase(filesByExtension.get(".txt", []), "requirements.txt")
        dockerComposePath = findExactFilenameMatchIgnoreCase(filesByExtension.get(".yml", []), "docker-compose.yml")
        dockerfilePath = findExactFilenameMatchIgnoreCase(filesByExtension.get("", []), "dockerfile")
        scriptFilePaths = filesByExtension.get(".sh", [])
        markdownFilePaths = filesByExtension.get(".md", [])
        rstTextFilePaths = filesByExtension.get(".rst", [])
        ymlFilePaths = filesByExtension.get(".yml", [])
        sqlFilePaths = filesByExtension.get(".sql", [])

        envFilePaths = []

        multipleDockerComposePaths = geAllMatchesIgnoreCase(listOfFiles, "docker-compose.yml")
        multipleDockerfilePaths = geAllMatchesIgnoreCase(listOfFiles, "Dockerfile")

        # get all .env and filter them removing those with common extension (.js, .py, .sh, .ts, .txt)
        for path in listOfFiles:
            if isThereMatchOfTextBetweenSymbols(path.lower(), "env") \
                    and getExtensionOfFile(path) not in ['.js', '.py', '.sh', '.ts', '.txt', '.png', '.jpg', '.jpeg']:
                envFilePaths.append(path)
                print(f"ENV: {path}")

        print(f"ENV FILES PATHS: {envFilePaths}")

        dbInfoInDockerCompose = False
        dbInfoInDockerfile = False

        if dockerComposePath != '':
            dbInfoInDockerCompose = isThereDbKeywordInFile(dockerComposePath)

        if dockerfilePath != '':
            dbInfoInDockerfile = isThereDbKeywordInFile(dockerfilePath)

        repoInfo = RepositoryInfo(repoName, "", repoPath, readmePath, requirementsPath, dockerComposePath,
                                  dockerfilePath,
                                  scriptFilePaths, markdownFilePaths, ymlFilePaths, sqlFilePaths, envFilePaths,
                                  rstTextFilePaths,
                                  multipleDockerComposePaths,
                                  dbInfoInDockerCompose,
                                  multipleDockerfilePaths,
                                  dbInfoInDockerfile)

    except Exception as e:
        print("Error while analyzing repo")
        print(e)
        isThereError = True
        repoInfo = RepositoryInfo(repoName)

    with lock:
        global counterRepos
        global counterReposErrors

        counterRepos += 1
        if isThereError:
            counterReposErrors += 1
        print(f"Num of Repos processed: {counterRepos}")
        print(f"Num of Repos with errors: {counterReposErrors}")

    return isThereError, repoInfo


createDirectoryIfNotExists(DEFAULT_DIR_FOR_OUTPUTS)
createDirectoryIfNotExists(os.path.join(DEFAULT_DIR_FOR_OUTPUTS, RUN_TIME_STR))

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # get list of all repos in dir specified
    reposBaseDir = getDirsInAPath(inputPath)
    print(reposBaseDir)

    futures = []
    for repoName in reposBaseDir:
        directories = getDirsInAPathStartingWithCertainName(os.path.join(inputPath, repoName), f"_repo")
        if len(directories) > 0:  # if dir properly configured,it always matches only one dir, so take the first
            futures.append(
                executor.submit(processRepository, repoName, directories[0]))

    for future in as_completed(futures):
        isThereError, repoInfo = future.result()

        if not isThereError and repoInfo:  # save info
            repoInfoList.append(repoInfo)
            if repoInfo.getReadmePath() != "":
                counterWithReadme += 1
            if repoInfo.getRequirementsPath() != "":
                counterWithRequirements += 1
            if len(repoInfo.getScriptFilePaths()) > 0:
                counterWithScripts += 1
            if len(repoInfo.getSqlFilePaths()) > 0:
                counterWithSql += 1
            if len(repoInfo.getEnvFilePaths()) > 0:
                counterWithEnv += 1

            if repoInfo.getDockerComposePath() != "":
                counterWithDockerCompose += 1
            if repoInfo.getDockerfilePath() != "":
                counterWithDockerfile += 1
            if repoInfo.getDockerComposePath() != "" and repoInfo.getDockerfilePath() == "":
                counterWithDockerComposeWithoutDockerfile += 1
            if repoInfo.getDockerComposePath() == "" and repoInfo.getDockerfilePath() != "":
                counterWithDockerfileWithoutDockerCompose += 1
            if repoInfo.getDockerComposePath() != "" and repoInfo.getDockerfilePath() != "":
                counterWithDockerfileWithDockerCompose += 1

            if repoInfo.getDbInfoInDockerCompose():
                counterDbInfoInDockerCompose += 1
            if repoInfo.getDbInfoInDockerfile():
                counterDbInfoInDockerfile += 1

            if repoInfo.getDbInfoInDockerfile() or repoInfo.getDbInfoInDockerCompose():
                counterDbInfo += 1

            if repoInfo.getDbInfoInDockerfile() and not repoInfo.getDbInfoInDockerCompose():
                counterDbInfoInDockerfileNotInDockerCompose += 1

            if not repoInfo.getDbInfoInDockerfile() and repoInfo.getDbInfoInDockerCompose():
                counterDbInfoInDockerComposeNotInDockerfile += 1

            if repoInfo.getDbInfoInDockerfile() and repoInfo.getDbInfoInDockerCompose():
                counterDbInfoInDockerComposeAndInDockerfile += 1

            if repoInfo.getRequirementsPath() != "" and not repoInfo.getDbInfoInDockerCompose():
                counterWithRequirementAndNotDockerCompose += 1

            if repoInfo.getRequirementsPath() != "" and not repoInfo.getDbInfoInDockerfile():
                counterWithRequirementsAndNotDockerfile += 1

            if len(repoInfo.getMultipleDockerComposePaths()) > 0:
                counterWithMultipleDockerComposePaths += 1

            if len(repoInfo.getMultipleDockerComposePaths()) > 0 and len(repoInfo.getEnvFilePaths()) > 0:
                counterWithEnvAndDockerCompose += 1

            if len(repoInfo.getMultipleDockerfilePaths()) > 0:
                counterWithMultipleDockerfilePaths += 1

            if len(repoInfo.getMultipleDockerfilePaths()) > 0 \
                    and len(repoInfo.getEnvFilePaths()) > 0 \
                    and len(repoInfo.getMultipleDockerComposePaths()) == 0:
                counterWithDockerfileWithEnvWithoutDockerCompose += 1

            counterTotalNumberDockerCompose += len(repoInfo.getMultipleDockerComposePaths())
            counterTotalNumberDockerfile += len(repoInfo.getMultipleDockerfilePaths())

        elif isThereError:
            errorRepos.append(f"{repoInfo.getRepoName()},{repoInfo.getRepoURL()}")
        else:
            errorCloningRepos.append(f"{repoInfo.getRepoName()},{repoInfo.getRepoURL()}")

inputFile = inputPath.split(TOKEN_SEPARATOR)[-1]

# save json output to file
with open(os.path.join(DEFAULT_DIR_FOR_OUTPUTS,
                       RUN_TIME_STR,
                       f"{RUN_TIME_STR}_{DEFAULT_FILENAME_FOR_OUTPUT}_{inputFile}.json"), "w") as f:
    f.write(json.dumps(repoInfoList, indent=4))
    f.flush()

# save stats to file
with open(os.path.join(DEFAULT_DIR_FOR_OUTPUTS,
                       RUN_TIME_STR,
                       f"{RUN_TIME_STR}_{DEFAULT_FILENAME_FOR_STATS}_{inputFile}.txt"),
          "w") as f:
    f.write(f"Number of repos in csv: {counterRepos}\n")
    f.write(f"Number of repos with errors: {counterReposErrors}\n")
    f.write(f"Number of repos with readme: {counterWithReadme}\n")
    f.write(f"Number of repos with requirements.txt: {counterWithRequirements}\n")
    f.write(f"\n")
    f.write(f"Number of repos with docker-compose: {counterWithDockerCompose}\n")
    f.write(f"Number of repos with dockerfile: {counterWithDockerCompose}\n")
    f.write(f"Number of repos with docker-compose, without dockerfile: {counterWithDockerComposeWithoutDockerfile}\n")
    f.write(f"Number of repos without docker-compose, with dockerfile: {counterWithDockerfileWithoutDockerCompose}\n")
    f.write(f"Number of repos with both docker-compose and dockerfile: {counterWithDockerfileWithDockerCompose}\n")
    f.write(f"\n")
    f.write(f"Number of repos with multiple docker-compose: {counterWithMultipleDockerComposePaths}\n")
    f.write(f"\n")
    f.write(
        f"Number of repos with requirements.txt and without dockercompose : {counterWithRequirementAndNotDockerCompose}\n")
    f.write(
        f"Number of repos with requirements.txt and without dockerfile : {counterWithRequirementsAndNotDockerfile}\n")
    f.write(f"\n")
    f.write(f"Number of repos with db keywords: {counterDbInfo}\n")
    f.write(f"Number of repos with db keywords in docker-compose: {counterDbInfoInDockerCompose}\n")
    f.write(f"Number of repos with db keywords in dockerfile: {counterDbInfoInDockerfile}\n")
    f.write(
        f"Number of repos with db keywords in dockerfile and NOT in dockercompose : {counterDbInfoInDockerfileNotInDockerCompose}\n")
    f.write(
        f"Number of repos with db keywords in docker-compose and NOT in dockerfile : {counterDbInfoInDockerComposeNotInDockerfile}\n")
    f.write(
        f"Number of repos with db keywords in both docker-compose and dockerfile : {counterDbInfoInDockerComposeAndInDockerfile}\n")
    f.write(f"\n")
    f.write(f"Number of repos with scripts: {counterWithScripts}\n")
    f.write(f"Number of repos with .sql files: {counterWithSql}\n")
    f.write(f"Number of repos with .env files: {counterWithEnv}\n")
    f.write(f"\n")
    f.write(f"Number of repos with multiple dockerfile: {counterWithMultipleDockerfilePaths}\n")
    f.write(
        f"Number of repos with dockerfile and .env file, without docker-compose: {counterWithDockerfileWithEnvWithoutDockerCompose}\n")
    f.write(f"\n")
    f.write(f"Total number of docker compose among all repos: {counterTotalNumberDockerCompose}\n")
    f.write(f"Total number of dockerfile among all repos: {counterTotalNumberDockerfile}\n")
    f.flush()

# save repos with errors to file
with open(os.path.join(DEFAULT_DIR_FOR_OUTPUTS,
                       RUN_TIME_STR,
                       f"{RUN_TIME_STR}_{DEFAULT_FILENAME_FOR_ERROR}_error_{inputFile}.txt"), "w") as f:
    f.write("repo with other errors\n")
for item in errorRepos:
    f.write(f"{item}\n")
    f.flush()

print(f"End.")
