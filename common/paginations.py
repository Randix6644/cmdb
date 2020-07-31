from typing import Optional
from django.views import View
from rest_framework.request import Request
from rest_framework.pagination import PageNumberPagination, replace_query_param
from rest_framework.exceptions import NotFound
from django.core.paginator import InvalidPage
from django.db.models import QuerySet
from collections import OrderedDict


class PagePagesizePagination(PageNumberPagination):
    """
    基于页的分页器
    """

    # 页大小参数
    page_size_query_param = 'pagesize'
    # 无参数时的页大小，即不分页
    page_size = 0
    # 分页时的默认页大小
    default_page_size = 20
    # 最大页大小，即无限制
    max_page_size = 0
    # 末尾页字符
    last_page_strings = ('last', 'end')

    def __init__(self) -> None:
        self.page = None
        self.request = None

    def paginate_queryset(self,
                          queryset: QuerySet,
                          request: Request,
                          view: Optional[View] = None) -> Optional[list]:
        """
        对查询集进行分页，成功返回数据列表，否则返回 None
        """
        # 存在 page 或 page_size 参数则启用分页
        page_number = request.query_params.get(self.page_query_param)

        # 兼容页面用数字、字符 和不指定页数的情况
        if page_number and page_number.isdigit():
            page_number = int(page_number)
        elif page_number in self.last_page_strings:
            page_number = -1
        else:
            page_number = 0

        page_size = self.get_page_size(request)

        if page_number:
            if not page_size:
                page_size = self.default_page_size
        else:
            if page_size:
                page_number = 1
            else:
                return None

        # 调用 django 的分页类得到分页器
        paginator = self.django_paginator_class(queryset, page_size)
        if page_number == -1:
            page_number = paginator.num_pages

        # 获取并设定指定的页面数据，无效页面则触发异常
        try:
            page = paginator.page(page_number)
        except InvalidPage:
            raise NotFound(f'Invalid page，the page is {page_number}')

        # api 界面显示页面控制条
        if paginator.num_pages > 1 and self.template is not None:
            self.display_page_controls = True

        # 设置请求和页面属性，并返回页面数据列表
        self.request = request
        self.page = page
        return list(page)

    def get_paginated_response(self, data: list) -> OrderedDict:
        """
        得到分页后的响应数据
        """
        return OrderedDict([
            ('total', self.page.paginator.count),
            ('current', len(data)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('data', data)
        ])

    def get_previous_link(self):
        """
        获取上页链接
        """
        if not self.page.has_previous():
            return None
        url = self.request.build_absolute_uri()
        page_number = self.page.previous_page_number()
        return replace_query_param(url, self.page_query_param, page_number)
