from typing import List
from openra.models import Maps

class MapSearch:

    def run(self, query:str):
        return MapSearchResult(
            self._get_maps_matching_map_hash(query),
            self._get_maps_containing_in_title(query),
            self._get_maps_containing_in_info(query),
            self._get_maps_containing_in_description(query),
            self._get_maps_containing_in_author(query)
        )

    def _get_maps_matching_map_hash(self, query:str):
        return Maps.objects.filter(map_hash=query)

    def _get_maps_containing_in_title(self, query:str):
        return Maps.objects.filter(title__icontains=query)

    def _get_maps_containing_in_info(self, query:str):
        return Maps.objects.filter(info__icontains=query)

    def _get_maps_containing_in_description(self, query:str):
        return Maps.objects.filter(description__icontains=query)

    def _get_maps_containing_in_author(self, query:str):
        return Maps.objects.filter(author__icontains=query)

class MapSearchResult:

    map_hash:List[Maps]
    title:List[Maps]
    info:List[Maps]
    description:List[Maps]
    author:List[Maps]
    total:int

    def __init__(
        self,
        map_hash:List[Maps],
        title:List[Maps],
        info:List[Maps],
        description:List[Maps],
        author:List[Maps]
    ):
        self.map_hash = map_hash
        self.title = title
        self.info = info
        self.description = description
        self.author = author

        self.total = self._calculate_total()

    def _calculate_total(self):
        return len(self.map_hash) + len(self.title) + len(self.info) + len(self.description) + len(self.author)

