# Cookie Baker

This document provides instructions for setting up the environment and running the Cookie Baker project.

## 0. Code Structure

The Cookie Baker codebase is divided into 6 main directories, according to a different phase of the project:
-   **`CodeQL`**: for running the CodeQL analysis, extracing signup and login URLs from the applications' source code.
-   **`RepoConfigScraper`**: for scraping local repositories and extracing paths of configuration files, script files and documentation files.
-   **`ReposCredentialsDiggerExtraction`**: for extracting credentials from codebase of local repositories using Credential Digger logs.
-   **`ReposGoogleAiCredentialExtraction`**: for extracting credentials from human-languages files such as READMEs by using Google's Gemini AI.
-   **`ReposCredentialsMerger`**: for merging extracted credentials (from Credential Digger and from Google Gemini) 
-   **`RunDockerAndCookieHunterWithCodeQL`**: to handle dynamic analysis by running docker containers and Cookie Hunter

## 1. Prerequisites

- Use a Linux environment.
- Use Python 3.10 (because Wapiti currently works only with Python 3.10 or 3.11).
- Install Docker and Docker Compose, since we use the Docker CLI. Follow official documentation at https://docs.docker.com/
- Since Cookie Baker is an extension of Cookie Hunter, you need Cookie Hunter's source code. Ask the original author to obtain it and then follow its instruction for installation.
- Install Wapiti Scanner (https://wapiti-scanner.github.io/)
  - it needs Firefox Browser to do the crawling, so install Firefox as you wish (Official Website, Snap, etc.)
  - then, you need to install GeckoDriver since it is used by Wapiti:
  ```bash
    export GECKO_DRIVER_VERSION='v0.24.0'
    wget https://github.com/mozilla/geckodriver/releases/download/$GECKO_DRIVER_VERSION/geckodriver-$GECKO_DRIVER_VERSION-linux64.tar.gz
    tar -xvzf geckodriver-$GECKO_DRIVER_VERSION-linux64.tar.gz
    rm geckodriver-$GECKO_DRIVER_VERSION-linux64.tar.gz
    chmod +x geckodriver
    sudo cp geckodriver /usr/local/bin/
  ```
  - then, install Wapiti:
  ```bash
    pip3 install wapiti3
  ```
- Install Node.js for Code Coverage Analysis. Follow official documentation at https://nodejs.org/en/download:
  - then, from inside the `coverageAnalysis` folder, install the dependencies:
  ```bash
  npm install
  ```
- Install Playwright
  - Playwright:  `pip3 install playwright`
  - Playwright browsers: `playwright install`
- Install CodeQL CLI. Follow official documentation at https://docs.github.com/en/code-security/codeql-cli/getting-started-with-the-codeql-cli/setting-up-the-codeql-cli
  - then, from inside the `CodeQL` folder, install dependencies:
  ```bash
  codeql pack install
  ```


## 2. Setting the environment

- `requirements.txt`: every directory has its own requirements that specifies required python packages. If no requirements.txt is present, then it means that only standard libraries are used.
  ```
  pip3 install -r requirements.txt
  ```
- MongoDB service must run on port 27123 (if you want to change it, you need to edit config.py files and util/cookiehunterUtil.py). 
  In particular, you have to set in the mongod.conf the port to 27123 (usually it is located at /usr/local/mongodb)
  ```
    [... other configuration ...]
    net:
      bindIp: 127.0.0.1
      port: 27123
  ```
- `config.py` files contains constants, api keys and credentials used by the scripts. You need to check and fill them. These files are located in the root of the following folders: `RepoConfigScraper`, `ReposCredentialsDiggerExtraction`, `ReposGoogleAiCredentialExtraction`, `ReposCredentialsMerger`, `RunDockerAndCookieHunterWithCodeQL`


### 3. Downloading repositories

Before starting the analysis, you must have the repositories cloned locally.
-   The directory structure must be a root directory with subdirectories containing repositories.
-   Each repository directory must be structured with a `_repo` suffix such as `myrepo/myrepo_repo`.
-   For example, the source code of repository `owner_webapp` will be in `path-to-repos/owner_webapp/owner_webapp_repo`

## 4. Running the scripts and executing the queries

After completing the setup, you can now execute the CodeQL queries and run the following scripts in the order described below:

## 4.1. Execute the CodeQL queries and generate the endpoints list (`CodeQL` dir)

Use the following commands to execute the queries:
  1. create the database:
  ```bash
  codeql database create <database> --language=<language-identifier> [--threads=<num>] --source-root <application>
  codeql database create ./FlaskApp-database --language=python --source-root ./FlaskApp
  ```
  2. run the query:
  ```bash
  codeql query run (--database=<database> | --dataset=<dataset>) [--output=<file.bqrs>] [--threads=<num>] <file.ql>
  codeql query run --database=FlaskApp-database --output=example_query_output.bqrs ./example_query.ql
  ```
  3. decode the result:
  ```bash
  codeql bqrs decode [--output=<file>] [--result-set=<name>] [--sort-key=<col>[,<col>...]] <file>
  codeql bqrs decode --output=example_query_results.txt --format=text ./example_query_output.bqrs
  ```

Then run the `merge_results_django.py` and `merge_results_flask.py` scripts for django and flask repositories respectively.
Once that's done run the `generate_endpoints_list_json.py` script to generate the json files containing the list of login and signup endpoints for each repository, which are then feeded to the `runAndUseCookieHunterDockerCompose.py` and `runAndUseCookieHunterDockerfile.py` scripts.

### 4.2. Repo Data Collection and Analysis (`RepoConfigScraper` dir)

1.  **Scan your repositories:** Use `reposScraper.py` to analyze the repositories.
    ```bash
    python reposScraper.py -i <path/to/repos> -c <numOfCores>
    ```
    -   `<path/to/repos>`: The path to the root directory containing all repositories with the `_repo` suffix (e.g. `myrepo/myrepo_repo`).
    -   `<numOfCores>`: The number of cores to use for parallel processing.
    -   **Output**: The JSON output will be saved inside the `outputs/<date_time>` directory. This output will be used in the next steps.

### 4.3. Credential Harvesting (`ReposCredentialsMerger` and `RunDockerAndCookieHunterWithCodeQL`)

1.  **Launch Credential Digger:** Use `runCredentialsDigger.py` to run Credential Digger and scan repositories for leaked credentials.
    ```bash
    python3 runCredentialsDigger.py -i <json-created-by-scraper.json>
    ```
    -  `<json-created-by-scraper.json>`: The JSON file containing repository information created by `reposScraper.py` in the previous step.
    -  **Output**: This will produce CSV files that are located in the `outputs/<date_time>/results` directory.

2.  **Launch script to extract credentials from the Credential Digger logs:** Use `runCredentialExtractorFromResults.py` to extract the credentials from the Credential Digger's output.
    ```bash
    python3 runCredentialExtractorFromResults.py -i outputs/<date_time>
    ```
    -   `<date_time>`: the directory where the output of `runCredentialsDigger.py` is located, under the `outputs` folder
    -  **Output:** This will produce the `credentials_cd.json` file that contains all extracted credentials, and that is located in `outputs/<date_time>`.

3.  **Extract potential credentials with Google Gemini AI:**  Use `runExtractCredentials.py` to analyze human language files (like README files) and identify potential credentials using Google Gemini AI.
    ```bash
    python3 runExtractCredentials.py -i  <json-created-by-scraper.json>
    ```
    - `<json-created-by-scraper.json>`: The JSON file containing repository information created by `reposScraper.py` in the first step.
    -  **Output:** This will produce the `credentials_ai.json` file that contains all extracted credentials, and that is located in `outputs/<date_time>`.

4.  **Merge candidate credentials:** Use the `credentialMerger.py` script to merge default and extracted credentials in a single JSON file.
    ```bash
     python credentialMerger.py [-d defaultcreds.csv] -i <path/to/file1.json> <path/to/file2.json> ...
    ```
    -   `-i <path/to/file1.json> <path/to/file2.json> ...`: One or more paths to JSON files containing credentials to be merged, for example `outputs/<date_time>/credentials_ai.json` and `outputs/<date_time>/credentials_cd.json`
    - **Output**: A merged `credentials.json` file.

### 4.4. Dynamic Analysis (`RunDockerAndCookieHunterWithCodeQL`)

The analysis will be performed by the `runAndUseCookieHunterDockerCompose.py` script or by the `runAndUseCookieHunterDockerfile.py` script, depending on whether you want to run `docker-compose` or `Dockerfile` configurations respectively.

-  **`runAndUseCookieHunterDockerCompose.py`**: Runs web applications via Docker Compose, performs dynamic analysis using CookieHunter (which extracts cookies), code coverage analysis and vulnerability analysis using Wapiti.
    ```bash
    python3 runAndUseCookieHunterDockerCompose.py -i <scraped_repos.json> -l <codeql_login_endpoints.json> -s <codeql_signup_endpoints.json> -c <credentials.json>
    ```
    -  `-i <scraped_repos.json>`: JSON file with repository information.
    -  `-l <codeql_login_endpoints.json>`: *(Optional)* JSON file with login endpoints from CodeQL.
    -  `-s <codeql_signup_endpoints.json>`: *(Optional)* JSON file with signup endpoints from CodeQL.
    -  `-c <credentials.json>`: *(Optional)* JSON file with the default credentials to try and login with.

  -   **`runAndUseCookieHunterDockerfile.py`**: Runs web applications via Dockerfile, performs dynamic analysis using CookieHunter, code coverage analysis and vulnerability analysis using Wapiti.
    ```bash
    python3 runAndUseCookieHunterDockerfile.py -i <scraped_repos.json> -l <codeql_login_endpoints.json> -s <codeql_signup_endpoints.json> -c <credentials.json>
    ```
        -  `-i <scraped_repos.json>`: JSON file with repository information.
        -  `-l <codeql_login_endpoints.json>`: *(Optional)* JSON file with login endpoints from CodeQL.
        -  `-s <codeql_signup_endpoints.json>`: *(Optional)* JSON file with signup endpoints from CodeQL.
        -  `-c <credentials.json>`: *(Optional)* JSON file with the default credentials to try and login with.

  
- NOTE that:
  - the outputs from docker run are available at `outputs/<date_time>`
  - the outputs from Wapiti are available at `outputsWapiti/<date_time>`
  - the outputs from the Code Coverage analysis are available at `outputsCodeCoverage/<date_time>`
  - `runAndUseCookieHunterDockerCompose.py` will try to run the repo only if there is at least one docker-compose
  - `runAndUseCookieHunterDockerfile.py` will try to run the repo only if there is at least one dockerfile and no docker-compose

### 4.5 Extracting Stats from Cookie Hunter logs, Wapiti and Code Coverage

Logs generated by Cookie Hunter are available at `cookie_hunter/logs`.
To avoid running the analysis multiple times on the same set of repositories, 5 different scripts to extract stats from Cookie Hunter logs are available: 
- Stats only Cookie Hunter (no codeql, no credentials, just like the original Cookie Hunter)
  - `python3 getStatsFromZipLog_only_ch.py -i <path/to/cookie_hunter_logs>`
  - output file is `STATS_global_only_CH.txt`
- Stats Cookie Hunter + CodeQL
  - `python3 getStatsFromZipLog_ch_codeql.py -i <path/to/cookie_hunter_logs>`
  - output file is `STATS_global_CH_CODEQL.txt`
- Stats Cookie Hunter + Credentials
  - `python3 getStatsFromZipLog_ch_credentials.py -i <path/to/cookie_hunter_logs>`
  - output file is `STATS_global_CH_CREDENTIALS.txt`
- Stats Cookie Baker (CodeQL + Credentials)
  - `python3 getStatsFromZipLog.py -i <path/to/cookie_hunter_logs>`
  - output file is `STATS_global.txt`
- Stats for the credentials, i.e., how many were tested, how many were working and where they were found (default credentials, credential digger...)
  - `python3 extractCredentitalsFromLogs.py -i <path/to/cookie_hunter_logs> -dc <path/to/default_credentials_list> -g <path/to/gemini_credentials_list> -ge <path/to/gemini_extended_credentials_list> -cd <path/to/credential_digger_credentials_list> -cdml <path/to/credential_digger_with_ml_credentials_list>`
  - output file is `STATS_CREDENTIALS.txt`

Results generated by Wapiti are available at `outputsWapiti/<date_time>`.
To parse the results use the following script: `python3 getStatsFromWapitiReports.py -i path/to/outputsWapiti/<date_time>`.

Results generated by the Code Coverage are available at `outputsCodeCoverage/<date_time>`.
To parse the results use the following scripts: 
1. `python3 compare_puppeteer.py`
2. `python3 compare_puppeteer_graph.py`
3. `python3 compare_puppeteer_total.py`
