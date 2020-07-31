from rest_framework.filters import BaseFilterBackend
from django.db import models
import re


class QueryFilterBackend(BaseFilterBackend):
    """
    查询参数过滤器
    """

    _query_param = 'query'
    _query_types = {
        '>:': 'gte',
        '<:': 'lte',
        ':': '',
        '>': 'gt',
        '<': 'lt',
        '@': 'contains',
        '^': 'istartswith',
        '$': 'iendswith'
    }

    def filter_queryset(self, request, queryset, view):
        """
        过滤器的入口
        """
        query_fields = self._get_query_fields(view, request)
        query_terms = self._get_query_terms(request)

        if not query_fields or not query_terms:
            return queryset

        q = self._construct_query(query_fields, query_terms.pop())
        while query_terms:
            if query_terms.pop() == ',':
                q &= self._construct_query(query_fields, query_terms.pop())
            else:
                q |= self._construct_query(query_fields, query_terms.pop())

        return queryset.filter(q)

    @ staticmethod
    def _get_query_fields(view, request):
        """
        模型的所有字段
        """
        model = getattr(getattr(view, 'queryset', None), 'model', None)
        fields = getattr(model, 'get_field_names')()
        fields.remove('id')
        return fields

    def _get_query_terms(self, request):
        """
        分离查询的条目
        """
        params = request.query_params.get(self._query_param, None)
        if not params: return []
        params = params.replace('\x00', '')
        params_list = re.split(r'(,|`)', params)
        params_list.reverse()
        return params_list

    def _construct_query(self, get_query_fields, query_term) -> models.Q:
        """
        构造一个查询条目的对应查询对象
        :param get_query_fields: 查询字段
        :param query_term: 查询条目
        :return: 查询对象
        """
        q = models.Q()

        # 确认查询类型，分离键值
        lookup = None
        for flag in self._query_types:
            if flag in query_term:
                lookup = flag
                break

        if lookup is None:
            return q
        t = self._query_types[lookup]

        key, values_str = query_term.split(lookup, 1)

        # 从键中记录并去除取反标记
        negative = False
        if key[0] == '!':
            key = key[1:]
            negative = True

        # 根据查询类型生成查询对象
        if key in get_query_fields and values_str:
            if t != '':
                key += f'__{t}'
            values = values_str.split('|')
            for value in values:
                q |= models.Q(**{key: value})

        # 确定是否取反
        if negative:
            return ~q
        else:
            return q
