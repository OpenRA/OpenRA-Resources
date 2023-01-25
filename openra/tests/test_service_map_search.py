from django.test import TestCase

from openra.services.map_search import MapSearch
from openra.tests.factories import MapsFactory


class TestServiceMapSearch(TestCase):

    def test_get_search_returns_maps_matching_hash(self):
        sample_hash = ''.rjust(40, 'A')
        match = MapsFactory(
            map_hash=sample_hash
        )
        MapsFactory()
        map_search = MapSearch()

        result = map_search.run(sample_hash)

        self.assertEquals(
            1,
            len(result.map_hash)
        )

        self.assertEquals(
            match,
            result.map_hash[0]
        )

    def test_get_search_returns_maps_containing_in_title(self):
        match = MapsFactory(
            title='before searchterm after'
        )
        MapsFactory()
        map_search = MapSearch()

        result = map_search.run('searchterm')

        self.assertEquals(
            1,
            len(result.title)
        )

        self.assertEquals(
            match,
            result.title[0]
        )

    def test_get_search_returns_maps_containing_in_info(self):
        match = MapsFactory(
            info='before searchterm after'
        )
        MapsFactory()
        map_search = MapSearch()

        result = map_search.run('searchterm')

        self.assertEquals(
            1,
            len(result.info)
        )

        self.assertEquals(
            match,
            result.info[0]
        )

    def test_get_search_returns_maps_containing_in_description(self):
        match = MapsFactory(
            description='before searchterm after'
        )
        MapsFactory()
        map_search = MapSearch()

        result = map_search.run('searchterm')

        self.assertEquals(
            1,
            len(result.description)
        )

        self.assertEquals(
            match,
            result.description[0]
        )

    def test_get_search_returns_maps_containing_in_author(self):
        match = MapsFactory(
            author='before searchterm after'
        )
        MapsFactory()
        map_search = MapSearch()

        result = map_search.run('searchterm')

        self.assertEquals(
            1,
            len(result.author)
        )

        self.assertEquals(
            match,
            result.author[0]
        )

    def test_map_search_result_can_total_items(self):
        MapsFactory(
            author='before searchterm after'
        )
        MapsFactory(
            info='before searchterm after'
        )
        MapsFactory(
            description='before searchterm after'
        )
        MapsFactory()
        map_search = MapSearch()

        result = map_search.run('searchterm')

        self.assertEquals(
            3,
            result.total
        )
