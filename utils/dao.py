from typing import Any, List, Union, Optional
from django.db.models import Q, QuerySet
from django.db.utils import Error
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from utils import get_datetime_with_tz


__all__ = [
    'DAOException',
    'QueryObjectError',
    'CreateObjectError',
    'UpdateObjectError',
    'DeleteObjectError',
    'DAO'
]


class DAOException(Exception):
    """
    DAO 的异常父类，用于异常捕捉
    """
    pass


class QueryObjectError(DAOException):
    """
    查询对象错误
    """
    pass


class CreateObjectError(DAOException):
    """
    创建对象错误
    """
    pass


class UpdateObjectError(DAOException):
    """
    更新对象错误
    """
    pass


class DeleteObjectError(DAOException):
    """
    删除对象错误
    """
    pass


class DAO:
    """
    database access object，数据库访问对象
    """

    def __init__(self, model: type):
        """
        初始化操作模型
        :param model: 模型类
        """
        self._model = model

    def get_obj(self, *args: Q, **kwargs: Any) -> Any:
        """
        过滤获取单个对象
        :param args: 查询对象列表
        :param kwargs: 字段过滤字典
        :return: 模型对象
        """
        try:
            return self._model.objects.get(*args, **kwargs)
        except (ObjectDoesNotExist, MultipleObjectsReturned) as e:
            raise QueryObjectError(*e.args)

    def get_queryset(self, *args: Q, empty: Optional[bool] = True, **kwargs: Any) -> QuerySet:
        """
        过滤获取一个查询集
        :param empty: 是否允许为空
        :param args: 查询对象列表
        :param kwargs: 字段过滤字典
        :return: 查询集
        """
        queryset = self._model.objects.filter(*args, **kwargs)
        if not empty and len(queryset) == 0:
            raise QueryObjectError('None of objects in queryset')
        return queryset

    def get_field_value(self, f: str, *args: Q, **kwargs: Any) -> List[Any]:
        """
        过滤获取包含对象指定字段值的列表
        :param f: 字段名
        :param args: 查询对象列表
        :param kwargs: 字段过滤字典
        :return: 字段值列表
        """
        queryset = self.get_queryset(*args, **kwargs)
        return [getattr(obj, f) for obj in queryset]

    def create_obj(self, **fields: Any) -> Any:
        """
        创建一个对象
        :param fields: 字段对应值字典
        :return: 模型对象
        """
        self._model.pre_create(fields)

        try:
            obj = self._model.objects.create(**fields)
        except Error as e:
            raise CreateObjectError(*e.args)

        obj.post_create()
        return obj

    def bulk_create_obj(self, fields_list: List[dict]) -> Any:
        """
        批量创建对象
        :param fields_list: 字段对应值字典的列表
        :return: 模型对象列表
        """
        objects = []
        for fields in fields_list:
            self._model.pre_create(fields)
            objects.append(self._model(**fields))

        try:
            objects = self._model.objects.bulk_create(objects)
        except Error as e:
            raise CreateObjectError(*e.args)

        for obj in objects:
            obj.post_create()
        return objects

    @staticmethod
    def update_obj(obj, **fields) -> Any:
        """
        修改一个指定对象
        :param obj: 模型对象
        :param fields: 字段对应值字典
        :return: 模型对象
        """
        obj.pre_update(fields)
        for k, v in fields.items():
            setattr(obj, k, v)

        try:
            obj.save()
        except Error as e:
            raise UpdateObjectError(*e.args)

        obj.post_update()
        return obj

    def bulk_update_obj(self, objects: Union[list, QuerySet], **fields) -> Union[list, QuerySet]:
        """
        批量修改指定对象
        :param objects: 模型对象列表
        :param fields: 字段对应值字典
        :return: 模型对象列表或查询集
        """
        for obj in objects:
            obj.pre_update(fields)
            for k, v in fields.items():
                setattr(obj, k, v)

        try:
            self._model.objects.bulk_update(objects, fields.keys())
        except Error as e:
            raise UpdateObjectError(*e.args)

        for obj in objects:
            obj.post_update()
        return objects

    @staticmethod
    def delete_obj(obj) -> None:
        """
        过滤删除一个对象，自动区分并进行软删除
        :param obj: 模型对象
        """
        obj.pre_delete()

        try:
            if hasattr(obj, 'deleted_at'):
                obj.deleted_time = get_datetime_with_tz()
                obj.save()
            else:
                obj.delete()
        except Error as e:
            raise DeleteObjectError(*e.args)
        obj.post_delete()

    def bulk_delete_obj(self, *args: Q, **kwargs: Any) -> int:
        """
        批量过滤删除多个对象，自动区分并进行软删除
        :param args: 查询对象列表
        :param kwargs: 字段过滤字典
        :return: 成功删除对象数
        """
        obj_qs = self.get_queryset(*args, **kwargs)
        for obj in obj_qs:
            self.delete_obj(obj)
        return len(obj_qs)
