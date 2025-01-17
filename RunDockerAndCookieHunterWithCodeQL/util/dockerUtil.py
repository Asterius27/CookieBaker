import os
import re
import signal
import subprocess
import threading
import time

import docker
import requests

from config import TIMEOUT_MINUTES_CONTAINER_OPS, TIMEOUT_MINUTES_PORTS, DOCKER_ACCOUNT_LIST, TOKEN_SEPARATOR, \
    RUN_TIME_STR, TIME_SECONDS_BETWEEN_PORT_ATTEMPTS, IS_PARALLEL_PULL, DEFAULT_DIR_FOR_REPOS, BUILD_IMAGE_NAME_PREFIX

client = docker.from_env()
indexLogin = 0


def handler(signum, frame):
    raise Exception("Signal killed the request: taking too long")


def nextDockerLogin():
    """Login to next Docker Hub account"""
    global indexLogin, client
    dockerLogout()
    indexLogin = (indexLogin + 1) % len(DOCKER_ACCOUNT_LIST)
    [user, password, email] = DOCKER_ACCOUNT_LIST[indexLogin][0:3]
    print(f"Changing Docker Hub account to {user}")
    result = subprocess.run(f"docker login --username {user} --password {password}", shell=True)
    print(f"Is logged in in Docker? {result}")


def dockerLogout():
    """Logout from current docker hub account"""
    result = subprocess.run("docker logout", shell=True)
    print(f"Logout result: {result}")


def saveContainerLog(container, pathForLog):
    """Extract log of given container and save it to given path"""
    try:
        with open(pathForLog, "wb") as outFile:
            outFile.write(container.logs(timestamps=True))
            outFile.flush()
    except Exception as e:
        print(f"Error while saving logs for container {container.name}")
        print(e)


def saveLogsOfAllContainers(pathForLog, exposedPorts=False):
    containers = reloadedContainerStatus()
    for container in containers:
        if exposedPorts:
            logpath = f"{pathForLog}{TOKEN_SEPARATOR}exposed_{container.name}.log"
        else:
            logpath = f"{pathForLog}{TOKEN_SEPARATOR}{container.name}.log"
        saveContainerLog(container, logpath)


def stopAllContainers():
    containers = client.containers.list(all=True)
    for container in containers:
        container.stop()


def removeAllContainers():
    result = subprocess.run("docker container prune -f", shell=True)
    print(f"Prune result: {result}")


def removeAllVolumes():
    result = subprocess.run("docker volume prune -f", shell=True)
    print(f"Prune result: {result}")


def removeAllImages():
    result = subprocess.run(f"docker rmi $(docker images)", shell=True)
    print(f"Remove all images result: {result}")


def removeAllImagesWithPrefix(prefix: str):
    result = subprocess.run(f"docker rmi $(docker images | grep '{prefix}')", shell=True)
    print(f"Remove all images with prefix {prefix} result: {result}")


def removeAllNetworks():
    result = subprocess.run("docker network prune -f", shell=True)
    print(f"Prune result: {result}")


def removeAllCache():
    result = subprocess.run("docker builder prune -f -a", shell=True)
    print(f"Prune result: {result}")


def pruneDockerSystem():
    result = subprocess.run("docker system prune -a --volumes -f", shell=True)
    print(f"Prune result: {result}")


def createNetwork(networkName):
    result = subprocess.run(f"docker network create {networkName}", shell=True)
    print(f"Network creation result: {result}")


def reloadedContainerStatus():
    """force update of container status taking info from docker engine"""
    containers = client.containers.list(all=True)
    for container in containers:
        container.reload()
    return containers


def getContainersStatus():
    """Return a string with status of running container, one per line"""
    log = ""
    containers = reloadedContainerStatus()
    for container in containers:
        log += f"Container: {container.name} - Status: {container.status}\n"
    return log


def exposeAllPortsOfContainer(container, logPathForCurrentDockerCompose=""):
    # Force to publish all port of the container (mapped to random ports of the host) automatically
    # 1. docker stop id-container
    # 2. docker commit id-container image-new-new
    # 3. docker rm id-container
    # 4. docker run -d -P --name image-original-name image-new-name
    idContainer = container.id
    containerName = container.name
    newImageName = f"exposed-{containerName}"
    print(f"Exposing ports of container {containerName} ...")
    result = subprocess.run(f"docker stop {idContainer}", shell=True)
    print(f"Is container stopped? {result}")

    print(f"Save log of stopped container {containerName}")

    # save logs of original container before being exposed
    saveContainerLog(container, f"{logPathForCurrentDockerCompose}{TOKEN_SEPARATOR}{container.name}.log")

    result = subprocess.run(f"docker commit {idContainer} {newImageName}", shell=True)
    print(f"Is commit ok? {result}")

    result = subprocess.run(f"docker rm {idContainer}", shell=True)
    print(f"Is remove ok?{result}")

    result = subprocess.run(f"docker run -d -P --name {containerName} {newImageName}", shell=True)
    print(f"Is docker run ok? {result}")
    print()


def getPortsFromContainers():
    """get list of ports from containers"""
    ports = []
    containers = reloadedContainerStatus()
    for c in containers:
        dictPorts = c.ports
        print(dictPorts)
        # example: {'8983/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '32769'}, {'HostIp': '::', 'HostPort': '32769'}]}

        # extract list of host ports
        for key, value in dictPorts.items():
            # print(f"Key {key} - Mapped to Host ports {value}")
            if value:  # i.e. not None
                lstOfDictOfHostPorts = value
                for dictMapping in lstOfDictOfHostPorts:
                    # print(dictMapping)
                    hostIp = dictMapping.get('HostIp', '')
                    hostPort = dictMapping.get('HostPort', '')
                    # print(f"{hostIp}:{hostPort}")
                    if hostPort != '' and hostPort not in ports:
                        ports.append(hostPort)

    return ports


def cleanEnvironment(pathForLogs="", exposedPorts=False):
    print("Stopping all containers...")
    stopAllContainers()

    if pathForLogs != "":
        print("Saving logs...")
        saveLogsOfAllContainers(pathForLogs, exposedPorts)

    print("Removing all containers...")
    removeAllContainers()

    print("Removing all volumes...")
    removeAllVolumes()

    print("Removing all networks...")
    removeAllNetworks()

    # if exposedPorts:
    #     print("Delete temporary images created for exposing ports")
    #     removeAllImagesWithPrefix('exposed')

    print("Removing build cache...")
    removeAllCache()

    # print("Removing all images...")
    # removeAllImages()
    # print("All images REMOVED")

    # print("Pruning docker system...")
    # pruneDockerSystem()
    # print("Prune done")


def getNameOfNetworkFromLog(logPath):
    pattern = r"network (.+) declared as external"
    try:
        with open(logPath, 'r') as f:
            allContents = f.read()
            matches = re.findall(pattern, allContents)
            if len(matches) > 0:
                return matches[0]
    except Exception as e:
        print("Error while finding name of network from log")
        print(e)

    return ""


def isLocalhostReachableAt(port, protocol='http', domain='localhost', verifySSLCertificate=False):
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(10)
    try:
        url = f"{protocol}://{domain}:{port}"
        response = requests.get(url, verify=verifySSLCertificate, timeout=10)
        # print(f"RESPONSE from {protocol}://{domain}:{port} -> {response.status_code}")
        return response.status_code < 400
    except Exception as err:
        # print(f"Error while creating requests: {protocol}://{domain}:{port}")
        # print(err)
        return False
    finally:
        signal.alarm(0)


def runDockerCompose(identifier, dockerComposePath, repoName, logSavePath):
    """Use docker compose to run a docker-compose.yml file and start containers """

    commands = ['docker', 'compose']
    if IS_PARALLEL_PULL: # parallel pull of docker images
        commands = commands + ['--parallel', '1']

    commands = commands + ['--file', dockerComposePath]
    commands = commands + ['up', '-d']

    print(f"Docker compose command: {commands}")

    process = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    logPath = f"{logSavePath}{TOKEN_SEPARATOR}{RUN_TIME_STR}_dockercompose_{repoName}_{identifier}.log"

    timeout = 25 * 60  # 20 minutes of timeout
    returnCode = -1

    def read_output(process, log_file):
        for line in iter(process.stdout.readline, b''):
            line = line.decode()
            print(line, end='')
            log_file.write(line)

    with open(logPath, 'w') as file:
        output_thread = threading.Thread(target=read_output, args=(process, file))
        output_thread.start()

        # check timeout or process completion
        try:
            process.wait(timeout)
        except Exception:
            print(f"Timeout reached after {timeout} seconds. Stopping process...")
            process.send_signal(signal.SIGINT)
        finally:
            process.terminate()

            # ensure process is terminated and output thread is joined
            if output_thread.is_alive():  # then a timeout happened!
                returnCode = -1
            else:
                returnCode = process.returncode
            output_thread.join()

    # print(f"RETURN CODE: {returnCode}")  # print the exit code of the command
    return returnCode, logPath

# 1. build the image
def buildDockerfile(identifier, dockerfilePath, repoName, logSavePath, useParentOfDockerfileAsWorkingDir=False):
    """Build dockerfile image specified in dockerfilePath"""

    imageName = f"{BUILD_IMAGE_NAME_PREFIX}-{repoName}".lower()

    lastIndexOfSeparator = dockerfilePath.rfind(TOKEN_SEPARATOR)
    filename = dockerfilePath[lastIndexOfSeparator + 1:]
    remainingPath = dockerfilePath[:lastIndexOfSeparator]

    commands = ["docker", "build"]
    if useParentOfDockerfileAsWorkingDir:
        commands = commands + [remainingPath]
    else:
        commands = commands + [f"{DEFAULT_DIR_FOR_REPOS}{TOKEN_SEPARATOR}{repoName}"]
    commands = commands + ["-t", imageName, "-f", dockerfilePath]

    print(f"Build Dockerfile command: {commands}")

    process = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    logPath = f"{logSavePath}{TOKEN_SEPARATOR}{RUN_TIME_STR}_dockerfile_{repoName}_{identifier}.log"

    timeout = 25 *60 # 20 minutes of timeout
    returnCode =-1

    def read_output(process, log_file):
        for line in iter(process.stdout.readline, b''):
            line = line.decode()
            print(line, end='')
            log_file.write(line)


    with open(logPath, 'w') as file:
        output_thread = threading.Thread(target=read_output, args=(process, file))
        output_thread.start()

        # check timeout or process completion
        try:
            process.wait(timeout)  # Wait for output thread, with timeout
        except Exception:
            print(f"Timeout reached after {timeout} seconds. Stopping process...")
            process.send_signal(signal.SIGINT)
        finally:
            process.terminate()

            # ensure process is terminated and output thread is joined
            if output_thread.is_alive():  # then a timeout happened!
                returnCode = -1
            else:
                returnCode = process.returncode
            output_thread.join()

    # print(f"RETURN CODE: {returnCode}")  # print the exit code of the command
    return returnCode, logPath, imageName


# 2. docker run
def runDockerfile(identifier, imageName, repoName, logSavePath, exposePorts=False):
    """Run dockerfile using the image previously builded"""

    # commands = ["docker", "run", "-d", imageName]
    commands = ["docker", "run", "-d"]
    if exposePorts:
        commands = commands + ['-P']
    commands = commands + [imageName]

    print(f"Run Dockerfile command: {commands}")

    process = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    logPath = f"{logSavePath}{TOKEN_SEPARATOR}{RUN_TIME_STR}_run_dockerfile_{repoName}_{identifier}.log"

    with open(logPath, 'w') as file:
        for line in iter(process.stdout.readline, b''):
            line = line.decode()
            print(line, end='')  # print to stdout
            file.write(line)  # write to file

        process.stdout.close()
        process.wait()
        returnCode = process.returncode

        # print(f"RETURN CODE: {returnCode}")  # print the exit code of the command
    return returnCode, logPath

def isWebAppWorking(ports):
    """Check if a web app is running, has at least 1 container running, and which ports are reachable"""
    containers = reloadedContainerStatus()
    runningContainers = [container for container in containers if container.status == 'running']
    print(f"Checking... Num Container: {len(containers)}, Num Running Containers: {len(runningContainers)}")

    isAtLeast1ContainerRunning = False
    portsWithHttpResponse = []

    if len(runningContainers) > 0:  # at least one container is running
        isAtLeast1ContainerRunning = True
        print("Doing GET requests to ports..")
        for port in ports:  # try all ports
            if isLocalhostReachableAt(protocol='http', port=port):
                portsWithHttpResponse.append((port, 'http'))
            if isLocalhostReachableAt(protocol='https', port=port):
                portsWithHttpResponse.append((port, 'https'))

    isRunning = isAtLeast1ContainerRunning and len(portsWithHttpResponse) > 0
    return isRunning, isAtLeast1ContainerRunning, portsWithHttpResponse
    # return len(runningContainers) == len(containers) and len(containers) != 0 # at least a container is running


def waitWebAppRunning(ports):
    """Check if a webapp is running, attempting for a certain max amount of time"""
    # wait for the services to start
    timeoutWaitContainerOperations = TIMEOUT_MINUTES_CONTAINER_OPS * 60  # minutes in seconds
    timeoutCheckPorts = TIMEOUT_MINUTES_PORTS * 60  # TIMEOUT_MINUTES minutes in seconds

    print()
    print(
        f"Waiting {timeoutWaitContainerOperations} seconds that containers do their possible initialization things...\n")
    time.sleep(timeoutWaitContainerOperations)  # wait that containers do their things...
    print(f"Starting checking ports: {ports}")
    startTime = time.time()
    # then start checking ports
    while time.time() - startTime < timeoutCheckPorts:
        print(getContainersStatus())
        isRunning, isAtLeast1ContainerRunning, portsWithHttpResponse = isWebAppWorking(ports)
        if isRunning:
            print("Web App is running!")
            print(f"Ports: {portsWithHttpResponse}")
            return isRunning, portsWithHttpResponse, False, time.time() - startTime

        time.sleep(TIME_SECONDS_BETWEEN_PORT_ATTEMPTS)  # Check every TIME_SECONDS_BETWEEN_PORT_ATTEMPTS seconds

    print(f"ERROR: Containers failed to respond to a port within {TIMEOUT_MINUTES_PORTS} minutes.\n")
    return False, [], True, -1
