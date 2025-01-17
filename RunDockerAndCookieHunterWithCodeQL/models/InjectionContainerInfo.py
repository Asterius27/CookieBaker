class InjectionContainerInfo(dict):

    def __init__(self, name: str, osVersion: str, isRunning: bool,
                 isContainerForInstallation: bool, pythonCommand: str, pipCommand: str,
                 isOkPackageInstallation: bool,
                 isOkPipPyrasiteInstallation: bool, isOkFileCreation: bool, isOkPtrace: bool, isPyrasiteTestRun: bool):
        dict.__init__(self,
                      name=name,
                      osVersion=osVersion,
                      isRunning=isRunning,
                      isContainerForInstallation=isContainerForInstallation,
                      pythonCommand=pythonCommand,
                      pipCommand=pipCommand,
                      isOkPackageInstallation=isOkPackageInstallation,
                      isOkPipPyrasiteInstallation=isOkPipPyrasiteInstallation,
                      isOkFileCreation=isOkFileCreation,
                      isOkPtrace=isOkPtrace,
                      isPyrasiteTestRun=isPyrasiteTestRun
                      )

    def getName(self):
        return self.get('name', "")

    def getOsVersion(self):
        return self.get("osVersion", "")

    def getIsRunning(self):
        return self.get('isRunning', False)

    def getIsContainerForInstallation(self):
        return self.get('isContainerForInstallation', False)

    def getIsOkPackageInstallation(self):
        return self.get('isOkPackageInstallation', False)

    def getIsOkPipPyrasiteInstallation(self):
        return self.get('isOkPipPyrasiteInstallation', False)

    def getIsOkFileCreation(self):
        return self.get('isOkFileCreation', False)

    def getIsOkPtrace(self):
        return self.get('isOkPtrace', False)

    def getIsPyrasiteTestRun(self):
        return self.get('isPyrasiteTestRun', False)

    @classmethod
    def from_json(cls, data):
        return cls(**data)
