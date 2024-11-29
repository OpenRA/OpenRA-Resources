from typing import Union


class FakeOpenraMaster:

    played_count = 123

    def get_played_count(self, map_hash: str):
        return self.played_count
