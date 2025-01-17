from models.InjectionInfo import InjectionInfo


class DockerfileRunInfo(dict):
    def __init__(self, dockerfilePath: str = "", ports=[], timeToGetRunning=-1, dockerfileStatusCode=-1,
                 isRunning=False, isTimeout=False, isNeededToExposePorts=False,
                 useParentOfDockerfileAsWorkingDir=False, injection=InjectionInfo()):
        dict.__init__(self,
                      dockerfilePath=dockerfilePath,
                      ports=ports,
                      timeToGetRunning=timeToGetRunning,
                      dockerfileStatusCode=dockerfileStatusCode,
                      isRunning=isRunning,
                      isTimeout=isTimeout,
                      isNeededToExposePorts=isNeededToExposePorts,
                      useParentOfDockerfileAsWorkingDir=useParentOfDockerfileAsWorkingDir,
                      injection=injection
                      )

    def getDockerfilePath(self):
        return self.get('dockerfilePath', '')

    def getPorts(self):
        return self.get('ports', [])

    def getTimeToGetRunning(self):
        return self.get('timeToGetRunning', -1)

    def getDockerfileStatusCode(self):
        return self.get("dockerfileStatusCode", -1)

    def isRunning(self):
        return self.get("isRunning", False)

    def isTimeout(self):
        return self.get("isTimeout", False)

    def isNeededToExposePorts(self):
        return self.get("isNeededToExposePorts", False)

    def useParentOfDockerfileAsWorkingDir(self):
        return self.get("useParentOfDockerfileAsWorkingDir", False)

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
