from typing import Optional, Union, Any
from rest_framework.response import Response
from rest_framework.views import set_rollback
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.conf import settings
from rest_framework import exceptions, status
from utils import logger
import sys


__all__ = [
    'ListModelMixin',
    'BulkCreateModelMixin',
    'BulkUpdateModelMixin',
    'BulkDestroyModelMixin',
    'RetrieveModelMixin',
    'CreateModelMixin',
    'UpdateModelMixin',
    'DestroyModelMixin',
    'get_data_response',
    'get_error_response',
    'normalized_exception_handler'
]


def get_data_response(data: Union[dict,
                                  list,
                                  None],
                      code: Optional[int] = 200,
                      **kwargs: Any) -> Response:
    """
    构造返回数据的响应
    :param data: 数据
    :param code: 状态码
    :param kwargs: 包含其他响应参数的字典
    :return: 框架响应类
    """
    return Response({
        'code': code,
        'data': data,
        'message': None
    }, **kwargs)


def get_error_response(message: str, code: int, **kwargs: Any) -> Response:
    """
    构造返回错误的响应
    :param message: 错误信息
    :param code: 状态码
    :param kwargs: 包含其他响应参数的字典
    :return: 框架响应类
    """
    return Response({
        'code': code,
        'data': None,
        'message': message
    }, **kwargs)


def normalized_exception_handler(exc: Exception, context: dict):
    """
    自定义异常处理，主要改变错误响应的格式
    """
    # 转化为 drf 设置的统一异常类
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()
    if not isinstance(exc, exceptions.APIException):
        exc = exceptions.APIException(exc.args)

    # 增加额外的响应头部
    headers = {}
    auth_header = getattr(exc, 'auth_header', None)
    if auth_header:
        headers['WWW-Authenticate'] = auth_header

    wait = getattr(exc, 'wait', None)
    if wait:
        headers['Retry-After'] = wait

    # 构造数据和回滚
    message = exc.detail
    set_rollback()

    # 调试模式则触发异常
    if settings.DEBUG:
        raise exc

    # 记录异常日志
    request = context['request']
    logger.exception(f'"{request.method} {request.get_full_path()}" Interval Server Error:', exc_info=sys.exc_info())

    # 为响应打错误标记，便于记录请求日志
    response = get_error_response(message, code=exc.status_code, headers=headers)
    response.with_exception = exc

    # 返回错误响应
    return response

##### 列表路由的处理混合 #####


class ListModelMixin:
    """
    模型对象列表查询
    """

    def list(self, request, *args, **kwargs):
        # 过滤对象
        queryset = self.filter_queryset(self.get_queryset())

        # 获取分页对象列表
        page = self.paginate_queryset(queryset)

        # 列表不为空则返回分页数据，否则返回包含所有对象的数据
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data

        # 返回响应
        return get_data_response(data)


class BulkCreateModelMixin:
    """
    单个或批量模型对象创建
    """

    def create(self, request, *args, **kwargs):
        # 若为批量操作则使用 many 参数，进行序列化
        bulk = isinstance(request.data, list)
        if not bulk:
            serializer = self.get_serializer(data=request.data)
        else:
            serializer = self.get_serializer(data=request.data, many=True)

        # 验证数据并执行创建
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # 返回响应
        return get_data_response(
            serializer.data,
            status=status.HTTP_201_CREATED)

    @staticmethod
    def perform_create(serializer):
        """
        执行创建
        """
        serializer.save()


class BulkUpdateModelMixin:
    """
    批量模型对象更新
    """

    def bulk_update(self, request, *args, **kwargs):
        """
        批量完整更新入口，同时被部分更新所调用
        区别于批量删除，批量更新此处不检查对象级别权限，因为子序列化验证前再进行检查
        """
        # 确定是完整更新还是部分更新
        partial = kwargs.pop('partial', False)
        queryset = self.filter_queryset(self.get_queryset())
        update_queryset = self.get_update_queryset(queryset)

        # 检查对象级别权限
        for obj in update_queryset:
            self.check_object_permissions(request, obj)

        # 进行自定义列表序列化的序列化
        serializer = self.get_serializer(
            update_queryset,
            data=request.data,
            many=True,
            partial=partial,
        )

        # 验证数据并执行更新
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_update(serializer)

        # 返回响应
        return get_data_response(serializer.data)

    def get_update_queryset(self, queryset):
        """
        获取需要更新的查询集
        """
        # 确认用于定位的关键字参数
        if not self.request.data: return None
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        # 组建参数值的列表
        id_list = []
        for item in self.request.data:
            _id = item.get(lookup_url_kwarg)
            if _id:
                id_list.append(_id)
            else:
                raise ValidationError(
                    f'All objects to update must have `{lookup_url_kwarg}`')

        # 进行查询集过滤
        update_queryset = queryset.filter(**{
            lookup_url_kwarg + '__in': id_list})

        # 检查需找到所有对象
        if len(update_queryset) != len(id_list):
            raise ValidationError('Could not find all objects to update.')

        return update_queryset

    def partial_bulk_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.bulk_update(request, *args, **kwargs)

    @staticmethod
    def perform_update(serializer):
        """
        执行更新
        """
        serializer.save()

    def perform_bulk_update(self, serializer):
        """
        部分更新入口
        """
        return self.perform_update(serializer)


class BulkDestroyModelMixin:
    """
    批量模型对象删除
    """

    def bulk_destroy(self, request, *args, **kwargs):
        """
        批量删除入口
        """
        # 获取批量删除的查询集
        queryset = self.filter_queryset(self.get_queryset())
        del_queryset = self.get_delete_queryset(queryset)

        # 检查对象级别权限
        for obj in del_queryset:
            self.check_object_permissions(request, obj)

        # 执行批量删除
        if del_queryset:
            self.perform_bulk_destroy(del_queryset)

        # 返回响应
        return get_data_response(
            {'count': len(del_queryset)}, code=status.HTTP_204_NO_CONTENT)

    def get_delete_queryset(self, queryset):
        """
        获取需要删除的查询集
        """
        # 确认用于定位的关键字参数
        if not self.request.data: return None
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        # 组建参数值的列表
        id_list = []
        for item in self.request.data:
            v = item.get(lookup_url_kwarg)
            if v:
                id_list.append(v)
            else:
                raise ValidationError(
                    f'All objects to update must have `{lookup_url_kwarg}`')

        # 进行查询集过滤
        filter_kwargs = {lookup_url_kwarg + '__in': id_list}
        del_queryset = queryset.filter(**filter_kwargs)
        return del_queryset

    @staticmethod
    def perform_destroy(instance):
        """
        执行单个对象删除
        """
        instance.pre_delete()
        instance.delete()
        instance.post_delete()

    def perform_bulk_destroy(self, objects):
        """
        执行批量删除
        """
        for obj in objects:
            self.perform_destroy(obj)


##### 详情路由的处理混合 #####


class RetrieveModelMixin:
    """
    单个模型对象查询
    """

    def retrieve(self, request, *args, **kwargs):
        # 获取对象并序列化
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        # 返回响应
        return get_data_response(serializer.data)


class CreateModelMixin:
    """
    单个模型对象创建
    """

    def create(self, request, *args, **kwargs):
        """
        单个对象创建入口
        """
        # 序列化
        serializer = self.get_serializer(data=request.data)

        # 验证数据并执行创建
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # 返回响应
        return get_data_response(serializer.data, code=status.HTTP_201_CREATED)

    @staticmethod
    def perform_create(serializer):
        """
        执行创建
        """
        serializer.save()


class UpdateModelMixin:
    """
    单个模型对象查询完整更新、部分更新
    """

    def update(self, request, *args, **kwargs):
        """
        完整更新入口，同时被部分更新所调用
        """
        # 确定是完整更新还是部分更新
        partial = kwargs.pop('partial', False)

        # 获取对象并进行序列化
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)

        # 验证数据并执行更新
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # 若存在预取，则清空预取缓存，
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        # 返回响应
        return get_data_response(serializer.data)

    @staticmethod
    def perform_update(serializer):
        """
        执行更新
        """
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        """
        部分更新入口
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class DestroyModelMixin:
    """
    单个模型对象删除
    """

    def destroy(self, request, *args, **kwargs):
        """
        单个对象删除入口
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return get_data_response(None, code=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def perform_destroy(instance):
        """
        执行单个对象删除
        """
        instance.pre_delete()
        instance.delete()
        instance.post_delete()
