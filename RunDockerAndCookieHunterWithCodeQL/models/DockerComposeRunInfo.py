from models.InjectionInfo import InjectionInfo


class DockerComposeRunInfo(dict):
    def __init__(self, dockerComposePath: str = "", ports=[], timeToGetRunning=-1, dockercomposeStatusCode=-1,
                 isRunning=False, isTimeout=False, isNeededToExposePorts=False, envAddedManually=False, envPath="",
                 addedExternalNetworkManually=False, injection=InjectionInfo()):
        dict.__init__(self,
                      dockerComposePath=dockerComposePath,
                      ports=ports,
                      timeToGetRunning=timeToGetRunning,
                      dockercomposeStatusCode=dockercomposeStatusCode,
                      isRunning=isRunning,
                      isTimeout=isTimeout,
                      isNeededToExposePorts=isNeededToExposePorts,
                      envAddedManually=envAddedManually,
                      envPath=envPath,
                      addedExternalNetworkManually=addedExternalNetworkManually,
                      injection=injection
                      )

    def getDockerComposePath(self):
        return self.get('dockerComposePath', '')

    def getPorts(self):
        return self.get('ports', [])

    def getTimeToGetRunning(self):
        return self.get('timeToGetRunning', -1)

    def getDockercomposeStatusCode(self):
        return self.get("dockercomposeStatusCode", -1)

    def isRunning(self):
        return self.get("isRunning", False)

    def isTimeout(self):
        return self.get("isTimeout", False)

    def isNeededToExposePorts(self):
        return self.get("isNeededToExposePorts", False)

    def isEnvAddedManually(self):
        return self.get("envAddedManually", False)

    def getEnvPath(self):
        return self.get("envPath", "")

    def isAddedExternalNetworkManually(self):
        return self.get("addedExternalNetworkManually", False)

    def getInjectionInfo(self):
        data = self.get("injection", "")
        if data == "":
            return InjectionInfo()
        else:
            return InjectionInfo.from_json(data)

    @classmethod
    def from_json(cls, data):
        data['injection'] = InjectionInfo.from_json(data['injection'])
        return cls(**data)
