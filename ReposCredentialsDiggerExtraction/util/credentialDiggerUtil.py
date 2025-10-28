import subprocess
import time


def execute_cmd(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    for line in process.stdout:
        print(line, end='')

    for line in process.stderr:
        print(line, end='')


def handler(signum, frame):
    raise Exception("Signal killed the request: taking too long")


def turnOnCredentialsDigger():
    # docker compose up of credential digger docker container with rules and

    docker_stop_cred_dig_cmd = 'cd credential-digger-main/; docker compose down'
    docker_prune_cmd = 'docker system prune -a --volumes -f'
    docker_start_cred_dig_cmd = 'cd credential-digger-main/; docker compose up -d'
    load_rules_cmd = 'docker exec -it credential_digger_sqlite sh -c "credentialdigger add_rules --sqlite /credential-digger-ui/data.db /credential-digger-ui/vol/rules_for_passwords_from_paper.yml"'

    execute_cmd(docker_stop_cred_dig_cmd)
    execute_cmd(docker_prune_cmd)
    execute_cmd(docker_start_cred_dig_cmd)
    time.sleep(20)
    execute_cmd(load_rules_cmd)


def scanRepoCredentialsDigger(repoPath, outputName):
    # run scan of local repo

    # scan_repo_cmd = 'docker exec -it credential_digger_sqlite sh -c "credentialdigger scan_path ' + repoPath + ' --sqlite /credential-digger-ui/data.db"'
    scan_repo_cmd = 'docker exec -it credential_digger_sqlite sh -c "credentialdigger scan_path ' + repoPath + ' --sqlite /credential-digger-ui/data.db --similarity --models PathModel PasswordModel"'

    results_cmd = 'docker exec -it credential_digger_sqlite sh -c "credentialdigger get_discoveries ' + repoPath + ' --sqlite /credential-digger-ui/data.db --save ./vol/results/' + \
                  outputName + '.csv --state new --with_rules"'
    execute_cmd(scan_repo_cmd)
    execute_cmd(results_cmd)
    print(f"REPO {repoPath} SCANNED!\n")
