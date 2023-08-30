import math
import re
from django.db.models import QuerySet


class Pagination:

    query_set: QuerySet
    per_page: int
    total: int

    def __init__(self, query_set: QuerySet, per_page: int):
        self.query_set = query_set
        self.per_page = per_page
        self.total = query_set.count()

    def get_page(self, page: int):
        return self.query_set[
            (page - 1) * self.per_page:page * self.per_page
        ]

    def get_links(self, page: int, query_string: str):

        lower_remaining = 3
        higher_remaining = 3
        total = math.ceil(self.total / self.per_page)

        if (total < 2):
            return []

        query_string = re.sub('page=\d+&?', '', query_string)

        start_sep = False
        end_sep = False

        if page < lower_remaining + 1:
            diff = lower_remaining - (page - 1)
            lower_remaining -= diff
            higher_remaining += diff

        if page < total - higher_remaining:
            end_sep = True
            higher_remaining -= 2
        else:
            diff = higher_remaining - (total - page)
            higher_remaining -= diff
            lower_remaining += diff

        if page > lower_remaining + 1:
            start_sep = True
            lower_remaining -= 2

        page_links = []

        if start_sep:
            page_links.append({
                'type': 'link',
                'text': 1,
                'href': '?' + self._merge_query_string(1, query_string),
                'active': page == 1
            })
            page_links.append({
                'type': 'separator',
            })

        for i in range(max(1, page - lower_remaining), page + higher_remaining + 1):
            page_links.append({
                'type': 'link',
                'text': i,
                'href': '?' + self._merge_query_string(i, query_string),
                'active': page == i
            })

        if end_sep:
            page_links.append({
                'type': 'separator',
            })
            page_links.append({
                'type': 'link',
                'text': total,
                'href': '?' + self._merge_query_string(total, query_string),
                'active': page == total
            })

        return page_links

    def _merge_query_string(self, page: int, query_string: str):
        buffer = 'page=' + str(page)
        if len(query_string) > 0:
            buffer += '&' + query_string

        return buffer
