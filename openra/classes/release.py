
class Release:

    mod: str
    version: str
    playtest: bool

    def __init__(self, mod: str, version: str, playtest: bool):
        self.mod = mod
        self.version = version
        self.playtest = playtest

    def __repr__(self):
        return f'Release({self.__str__()})'

    def __str__(self):
        playtest_text = "Playtest" if self.playtest else "Full"
        return f'{self.mod} {self.version} {playtest_text}'

    def __eq__(self, other):
        return other.__repr__() == self.__repr__()
