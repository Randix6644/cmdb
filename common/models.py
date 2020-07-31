from django.db import models
from django.db.models.base import ModelBase
from utils import DAO, generate_unique_uuid


__all__ = [
    'BaseModel',
    'DisplayModel',
    'ManageModel'
]


class BaseModelMeta(ModelBase):
    """
    基础抽象元类
    """

    def __new__(mcs, *args, **kwargs):
        mcs = super().__new__(mcs, *args, **kwargs)
        mcs.dao = DAO(mcs)
        return mcs


class BaseModel(models.Model, metaclass=BaseModelMeta):
    """
    基础抽象模型
    """

    class Meta:
        verbose_name = '基础抽象模型'
        abstract = True

    @classmethod
    def pre_create(cls, data: dict):
        """
        创建对象前的操作
        :param data: 创建数据
        """
        pass

    def post_create(self):
        """
        对象创建后的操作
        """
        pass

    def pre_update(self, data: dict):
        """
        对象更新前的操作
        :param data: 更新数据
        """
        pass

    def post_update(self):
        """
        对象更新后的操作
        """
        pass

    def pre_delete(self):
        """
        删除前的操作
        """
        pass

    def post_delete(self):
        """
        删除后的操作
        """
        pass

    @classmethod
    def get_field_names(cls):
        """
        获取所有字段名
        """
        return [fields.name for fields in getattr(cls, '_meta').fields]


class DisplayModel(BaseModel):
    """
    需要展示的抽象模型
    """

    class Meta:
        verbose_name = '展示型抽象模型'
        abstract = True

    # 公共字段
    uuid = models.CharField(max_length=32, unique=True, verbose_name='UUID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    @classmethod
    def pre_create(cls, data: dict):
        """
        创建对象前的检查和操作
        :param data: 创建数据
        """
        if not data.get("uuid"):
            data['uuid'] = generate_unique_uuid()


class ManageModel(DisplayModel):
    """
    需要管理的抽象模型
    """

    class Meta:
        verbose_name = '管理型抽象模型'
        abstract = True

    # 公共字段
    created_by = models.CharField(max_length=32, verbose_name='创建用户UUID')
    updated_by = models.CharField(max_length=32, null=True, verbose_name='更新用户UUID')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
