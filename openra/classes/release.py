
class Release:

    mod: str
    version: str
    is_playtest: bool

    def __init__(self, mod: str, version: str, is_playtest: bool):
        self.mod = mod
        self.version = version
        self.is_playtest = is_playtest

    def __repr__(self):
        return f'Release({self.__str__()})'

    def __str__(self):
        is_playtest_text = "Playtest" if self.is_playtest else "Full"
        return f'{self.mod} {self.version} {is_playtest_text}'

    def __eq__(self, other):
        return other.__repr__() == self.__repr__()
