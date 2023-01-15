
class Release:

    mod:str
    version:str

    def __init__(self, mod:str, version):
        self.mod = mod
        self.version = version

    def __repr__(self):
        return f'Release({self.mod} {self.version})'

    def __str__(self):
        return f'{self.mod} {self.version}'

    def __eq__(self, other):
        return other.__repr__() == self.__repr__()
