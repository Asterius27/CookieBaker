class RepositoryInfo(dict):
    def __init__(self, repoName: str, repoURL: str = "", repoPath: str = "",
                 readmePath: str = "", requirementsPath: str = "", dockerComposePath: str = "",
                 dockerfilePath: str = "",
                 scriptFilePaths=[], markdownFilePaths=[],
                 ymlFilePaths=[], sqlFilePaths=[], envFilePaths=[], rstTextFilePaths=[], multipleDockerComposePaths=[],
                 dbInfoInDockerCompose=False, multipleDockerfilePaths=[], dbInfoInDockerfile=False, ):
        dict.__init__(self,
                      repoName=repoName,
                      repoURL=repoURL,
                      repoPath=repoPath,
                      readmePath=readmePath,
                      requirementsPath=requirementsPath,
                      dockerComposePath=dockerComposePath,
                      dockerfilePath=dockerfilePath,
                      scriptFilePaths=scriptFilePaths,
                      markdownFilePaths=markdownFilePaths,
                      ymlFilePaths=ymlFilePaths,
                      sqlFilePaths=sqlFilePaths,
                      envFilePaths=envFilePaths,
                      rstTextFilePaths=rstTextFilePaths,
                      multipleDockerComposePaths=multipleDockerComposePaths,
                      dbInfoInDockerCompose=dbInfoInDockerCompose,
                      multipleDockerfilePaths=multipleDockerfilePaths,
                      dbInfoInDockerfile=dbInfoInDockerfile
                      )

    def getRepoName(self):
        return self.get('repoName', '')

    def getRepoURL(self):
        return self.get('repoURL', '')

    def getRepoPath(self):
        return self.get('repoPath', '')

    def getReadmePath(self):
        return self.get('readmePath', '')

    def getRequirementsPath(self):
        return self.get('requirementsPath', '')

    def getDockerComposePath(self):
        return self.get('dockerComposePath', '')

    def getDockerfilePath(self):
        return self.get('dockerfilePath', '')

    def getScriptFilePaths(self):
        return self.get('scriptFilePaths', [])

    def getMarkdownFilePaths(self):
        return self.get('markdownFilePaths', [])

    def getRstFilePaths(self):
        return self.get('rstTextFilePaths', [])

    def getYmlFilePaths(self):
        return self.get('ymlFilePaths', [])

    def getSqlFilePaths(self):
        return self.get('sqlFilePaths', [])

    def getEnvFilePaths(self):
        return self.get('envFilePaths', [])

    def getMultipleDockerComposePaths(self):
        return self.get('multipleDockerComposePaths', [])

    def getDbInfoInDockerCompose(self):
        return self.get('dbInfoInDockerCompose', [])

    def getMultipleDockerfilePaths(self):
        return self.get('multipleDockerfilePaths', [])

    def getDbInfoInDockerfile(self):
        return self.get('dbInfoInDockerfile', [])
