from collections import OrderedDict

from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination



class CustomPageNumberPagination(PageNumberPagination):
    page_query_param = 'page'
    page_size_query_param = 'limit'

    def get_paginated_response(self, data, count=None):
        count = (count if count is not None and isinstance(count, int) else self.page.paginator.count)
        return Response(OrderedDict([
            ('results', data),
            ('count', count),
            ('page', self.page.number),
            ('next_page', self.page.next_page_number() if self.page.has_next() else None)
        ]))