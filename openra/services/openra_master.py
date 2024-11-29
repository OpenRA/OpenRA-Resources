from typing import List
from openra.models import Maps
import urllib.request
from openra.models import Maps
import json


class OpenraMaster:

    def get_played_count(self, map_hash: str):
        try:
            played_counter = urllib.request.urlopen("http://master.openra.net/map_stats?hash=%s" % map_hash).read().decode()
            played_counter = json.loads(played_counter)
            if played_counter:
                return played_counter["played"]
            else:
                return 0
        except BaseException:
            return None
