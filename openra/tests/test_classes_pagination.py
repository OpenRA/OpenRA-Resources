from openra.classes.pagination import Pagination
from openra.tests.factories import MapsFactory
from openra.models import Maps

from unittest import TestCase


class TestPagination(TestCase):

    def test_it_can_return_a_page(self):

        MapsFactory()
        MapsFactory()
        MapsFactory()

        pagination = Pagination(Maps.objects.filter(), 2)

        self.assertEquals(
            2,
            pagination.get_page(1).count()
        )

        self.assertEquals(
            1,
            pagination.get_page(2).count()
        )

        self.assertEquals(
            0,
            pagination.get_page(3).count()
        )

    def test_it_can_return_early_page_links(self):

        Maps.objects.all().delete()
        for _ in range(0, 20):
            MapsFactory()

        pagination = Pagination(Maps.objects.filter(), 1)

        self.assertEquals([
            {
                'type': 'link',
                'text': 1,
                'href': '?page=1',
                'active': True
            },
            {
                'type': 'link',
                'text': 2,
                'href': '?page=2',
                'active': False
            },
            {
                'type': 'link',
                'text': 3,
                'href': '?page=3',
                'active': False
            },
            {
                'type': 'link',
                'text': 4,
                'href': '?page=4',
                'active': False
            },
            {
                'type': 'link',
                'text': 5,
                'href': '?page=5',
                'active': False
            },
            {
                'type': 'separator',
            },
            {
                'type': 'link',
                'text': 20,
                'href': '?page=20',
                'active': False
            },

        ], pagination.get_links(1, ''))

    def test_it_can_return_semi_early_page_links(self):

        Maps.objects.all().delete()
        for _ in range(0, 20):
            MapsFactory()

        pagination = Pagination(Maps.objects.filter(), 1)

        self.assertEquals([
            {
                'type': 'link',
                'text': 1,
                'href': '?page=1',
                'active': False
            },
            {
                'type': 'link',
                'text': 2,
                'href': '?page=2',
                'active': False
            },
            {
                'type': 'link',
                'text': 3,
                'href': '?page=3',
                'active': False
            },
            {
                'type': 'link',
                'text': 4,
                'href': '?page=4',
                'active': True
            },
            {
                'type': 'link',
                'text': 5,
                'href': '?page=5',
                'active': False
            },
            {
                'type': 'separator',
            },
            {
                'type': 'link',
                'text': 20,
                'href': '?page=20',
                'active': False
            },

        ], pagination.get_links(4, ''))

    def test_it_can_return_middle_page_links(self):

        Maps.objects.all().delete()
        for _ in range(0, 20):
            MapsFactory()

        pagination = Pagination(Maps.objects.filter(), 1)

        self.assertEquals([
            {
                'type': 'link',
                'text': 1,
                'href': '?page=1',
                'active': False
            },
            {
                'type': 'separator',
            },
            {
                'type': 'link',
                'text': 9,
                'href': '?page=9',
                'active': False
            },
            {
                'type': 'link',
                'text': 10,
                'href': '?page=10',
                'active': True
            },
            {
                'type': 'link',
                'text': 11,
                'href': '?page=11',
                'active': False
            },
            {
                'type': 'separator',
            },
            {
                'type': 'link',
                'text': 20,
                'href': '?page=20',
                'active': False
            },

        ], pagination.get_links(10, ''))

    def test_it_can_return_late_page_links(self):

        Maps.objects.all().delete()
        for _ in range(0, 20):
            MapsFactory()

        pagination = Pagination(Maps.objects.filter(), 1)

        self.assertEquals([
            {
                'type': 'link',
                'text': 1,
                'href': '?page=1',
                'active': False
            },
            {
                'type': 'separator',
            },
            {
                'type': 'link',
                'text': 16,
                'href': '?page=16',
                'active': False
            },
            {
                'type': 'link',
                'text': 17,
                'href': '?page=17',
                'active': False
            },
            {
                'type': 'link',
                'text': 18,
                'href': '?page=18',
                'active': False
            },
            {
                'type': 'link',
                'text': 19,
                'href': '?page=19',
                'active': False
            },
            {
                'type': 'link',
                'text': 20,
                'href': '?page=20',
                'active': True
            },

        ], pagination.get_links(20, ''))

    def test_it_can_return_semi_late_page_links(self):

        Maps.objects.all().delete()
        for _ in range(0, 20):
            MapsFactory()

        pagination = Pagination(Maps.objects.filter(), 1)

        self.assertEquals([
            {
                'type': 'link',
                'text': 1,
                'href': '?page=1',
                'active': False
            },
            {
                'type': 'separator',
            },
            {
                'type': 'link',
                'text': 16,
                'href': '?page=16',
                'active': False
            },
            {
                'type': 'link',
                'text': 17,
                'href': '?page=17',
                'active': True
            },
            {
                'type': 'link',
                'text': 18,
                'href': '?page=18',
                'active': False
            },
            {
                'type': 'link',
                'text': 19,
                'href': '?page=19',
                'active': False
            },
            {
                'type': 'link',
                'text': 20,
                'href': '?page=20',
                'active': False
            },

        ], pagination.get_links(17, ''))

    def test_it_can_return_less_page_links_early(self):

        Maps.objects.all().delete()
        for _ in range(0, 3):
            MapsFactory()

        pagination = Pagination(Maps.objects.filter(), 1)

        self.assertEquals([
            {
                'type': 'link',
                'text': 1,
                'href': '?page=1',
                'active': True
            },
            {
                'type': 'link',
                'text': 2,
                'href': '?page=2',
                'active': False
            },
            {
                'type': 'link',
                'text': 3,
                'href': '?page=3',
                'active': False
            },

        ], pagination.get_links(1, ''))

    def test_it_can_return_less_page_links_mid(self):

        Maps.objects.all().delete()
        for _ in range(0, 3):
            MapsFactory()

        pagination = Pagination(Maps.objects.filter(), 1)

        self.assertEquals([
            {
                'type': 'link',
                'text': 1,
                'href': '?page=1',
                'active': False
            },
            {
                'type': 'link',
                'text': 2,
                'href': '?page=2',
                'active': True
            },
            {
                'type': 'link',
                'text': 3,
                'href': '?page=3',
                'active': False
            },

        ], pagination.get_links(2, ''))

    def test_it_can_return_less_page_links_late(self):

        Maps.objects.all().delete()
        for _ in range(0, 3):
            MapsFactory()

        pagination = Pagination(Maps.objects.filter(), 1)

        self.assertEquals([
            {
                'type': 'link',
                'text': 1,
                'href': '?page=1',
                'active': False
            },
            {
                'type': 'link',
                'text': 2,
                'href': '?page=2',
                'active': False
            },
            {
                'type': 'link',
                'text': 3,
                'href': '?page=3',
                'active': True
            },

        ], pagination.get_links(3, ''))

    def test_it_will_merge_the_existing_query_string(self):

        Maps.objects.all().delete()
        MapsFactory()
        MapsFactory()

        pagination = Pagination(Maps.objects.filter(), 1)

        self.assertEquals([
            {
                'type': 'link',
                'text': 1,
                'href': '?page=1&test=123&test2=123',
                'active': True
            },
            {
                'type': 'link',
                'text': 2,
                'href': '?page=2&test=123&test2=123',
                'active': False
            }

        ], pagination.get_links(1, 'test=123&page=1&test2=123'))
