from models.DockerComposeRunInfo import DockerComposeRunInfo
from models.DockerfileRunInfo import DockerfileRunInfo


class DockerRepoRunInfo(dict):
    def __init__(self, repoName: str, repoURL: str, repoPath:str, dockerComposeRuns=[],
                 dockerComposeSuccess=0,
                 dockerComposeTimeout=0,
                 dockerComposeError=0,
                 dockerComposeNotRunning=0,

                 dockerfileRuns=[],
                 dockerfileSuccess=0,
                 dockerfileTimeout=0,
                 dockerfileError=0,
                 dockerfileNotRunning=0):
        dict.__init__(self,
                      repoName=repoName,
                      repoURL=repoURL,
                      repoPath=repoPath,
                      dockerComposeRuns=dockerComposeRuns,
                      dockerComposeSuccess=dockerComposeSuccess,
                      dockerComposeTimeout=dockerComposeTimeout,
                      dockerComposeError=dockerComposeError,
                      dockerComposeNotRunning=dockerComposeNotRunning,

                      dockerfileRuns=dockerfileRuns,
                      dockerfileSuccess=dockerfileSuccess,
                      dockerfileTimeout=dockerfileTimeout,
                      dockerfileError=dockerfileError,
                      dockerfileNotRunning=dockerfileNotRunning
                      )

    def getRepoName(self):
        return self.get('repoName', '')

    def getRepoURL(self):
        return self.get('repoURL', '')

    def getRepoPath(self):
        return self.get('repoPath','')

    def getDockerComposeRuns(self):
        return self.get('dockerComposeRuns', [])

    def getDockerComposeSuccess(self):
        return self.get('dockerComposeSuccess', 0)

    def getDockerComposeTimeout(self):
        return self.get('dockerComposeTimeout', 0)

    def getDockerComposeError(self):
        return self.get('dockerComposeError', 0)

    def getDockerComposeNotRunning(self):
        return self.get('dockerComposeNotRunning', 0)

    def getDockerfileRuns(self):
        return self.get('dockerfileRuns', [])

    def getDockerfileSuccess(self):
        return self.get('dockerfileSuccess', 0)

    def getDockerfileTimeout(self):
        return self.get('dockerfileTimeout', 0)

    def getDockerfileError(self):
        return self.get('dockerfileError', 0)

    def getDockerfileNotRunning(self):
        return self.get('dockerfileNotRunning', 0)

    @classmethod
    def from_json(cls, data):
        data['dockerComposeRuns'] = [DockerComposeRunInfo.from_json(run) for run in data.get('dockerComposeRuns', [])]
        data['dockerfileRuns'] = [DockerfileRunInfo.from_json(run) for run in data.get('dockerfileRuns', [])]
        return cls(**data)

