from models.InjectionContainerInfo import InjectionContainerInfo


class InjectionInfo(dict):
    def __init__(self, containers=[]):
        dict.__init__(self,
                      containers=containers
                      )

    def getContainers(self):
        ris = []
        for info in self.get('containers', []):
            ris.append(InjectionContainerInfo.from_json(info))
        return ris


    @classmethod
    def from_json(cls, data):
        return cls(**data)
