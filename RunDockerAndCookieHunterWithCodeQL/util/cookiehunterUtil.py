import signal
import subprocess


def handler(signum, frame):
    raise Exception("Signal killed the request: taking too long")


def completeCleanCookieHunterDB():
    """remove all collections created by Cookie Hunter from DB"""
    MONGO_HOST = "localhost"
    MONGO_PORT = "27123"
    MONGO_DB = "framework_db"
    runMongoShell = "/usr/local/mongodb/bin/mongo"
    collections = ['account_info', 'attempted_values', 'domain_info', 'misc_cookies', 'module_times', 'credentials_and_cookies']

    print("Cleaning Cookie Hunter DB...")
    for coll in collections:
        command = f'{runMongoShell} --host {MONGO_HOST} --port {MONGO_PORT} {MONGO_DB} --eval "db.{coll}.drop()"'
        try:
            result = subprocess.run(command, shell=True)
            print(f"Is cookie hunter OK? {result}")
        except Exception as ex:
            print(f"ERROR: can not run command {command}")
            print(ex)


def softCleanCookieHunterDB():
    """ust delete collections that are used by a repo run"""
    MONGO_HOST = "localhost"
    MONGO_PORT = "27123"
    MONGO_DB = "framework_db"
    runMongoShell = "/usr/local/mongodb/bin/mongo"
    collections = ['domain_info', 'misc_cookies', 'credentials_and_cookies']

    print("Cleaning Cookie Hunter DB...")
    for coll in collections:
        command = f'{runMongoShell} --host {MONGO_HOST} --port {MONGO_PORT} {MONGO_DB} --eval "db.{coll}.drop()"'
        try:
            result = subprocess.run(command, shell=True)
            print(f"Is cookie hunter OK? {result}")
        except Exception as ex:
            print(f"ERROR: can not run command {command}")
            print(ex)


def runCookieHunter(url, repoName, repoURL, pathLoginEndpoints, pathSignupEndpoints, pathCredentials):
    """use subprocess to run cookie hunter with custom parameters"""
    signal.signal(signal.SIGALRM, handler)

    signal.alarm(2 * 60 * 60)  # 60 minutes to execute the command, then trigger

    command = f"python2 cookie_hunter/runCookieHunter.py -u {url} -n {repoName} -r {repoURL}"

    if pathLoginEndpoints and pathLoginEndpoints != "":
        command = f"{command} -l {pathLoginEndpoints}"

    if pathSignupEndpoints and pathSignupEndpoints != "":
        command = f"{command} -s {pathSignupEndpoints}"

    if pathCredentials and pathCredentials != "":
        command = f"{command} -c {pathCredentials}"

    try:
        result = subprocess.run(command, shell=True)
        print(f"Is cookie hunter OK? {result}")
    except Exception as ex:
        print(f"ERROR: can not run command {command}")
        print(ex)
    finally:
        signal.alarm(0)
