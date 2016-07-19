from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


class PageNumberPaginationSmall(PageNumberPagination):
    page_size = 15

    def get_paginated_response(self, data):
        return Response({
            'meta': {
                'next': self.page.next_page_number() if self.page.has_next()
                else self.page.paginator.num_pages,
                'previous': self.page.previous_page_number() if self.page.has_previous() else 1,
                'current': self.page.number,
                'count': self.page.paginator.count,
            },
            'results': data
        })


class PageNumberOnlyPagination(PageNumberPagination):
    '''
    Paginates with only a page number (not a URL). Defaults to 15 items.
    '''

    page_size_query_param = 'limit'
    max_page_size = 200
    page_size = 15

    def get_paginated_response(self, data):
        return Response({
            'meta': {
                'pages': self.page.paginator.num_pages,
                'next': self.page.next_page_number() if self.page.has_next()
                else self.page.paginator.num_pages,
                'previous': self.page.previous_page_number() if self.page.has_previous() else 1,
                'current': self.page.number,
                'count': self.page.paginator.count,
            },
            'results': data
        })
