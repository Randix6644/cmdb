from rest_framework.serializers import ModelSerializer, CharField
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ListSerializer
from rest_framework.settings import api_settings
from rest_framework.utils import html
from common.models import BaseModel


__all__ = [
    'BaseSerializer',
    'DisplaySerializer',
    'ManageSerializer',
    'BulkSerializerMixin',
    'BulkListSerializer'
]


class BaseSerializer(ModelSerializer):
    """
    基础序列化器
    """

    def save(self, **kwargs):
        """
        重写保存逻辑，加入基础模型中的预处理和后处理
        :param kwargs: 额外数据
        """
        # 断言模型是基础模型
        assert issubclass(self.Meta.model, BaseModel), (
            'Serializer `%s.%s.Meta.model` is subclass of BaseModel' %
            (self.__class__.__module__, self.__class__.__name__)
        )

        # 断言不存在老版本的保存对象方法
        assert not hasattr(self, 'save_object'), (
            'Serializer `%s.%s` has old-style version 2 `.save_object()` '
            'that is no longer compatible with REST framework 3. '
            'Use the new-style `.create()` and `.update()` methods instead.' %
            (self.__class__.__module__, self.__class__.__name__)
        )

        # 断言已经完成了数据验证
        assert hasattr(self, '_errors'), (
            'You must call `.is_valid()` before calling `.save()`.'
        )

        # 断言数据验证时没有发生错误
        assert not self.errors, (
            'You cannot call `.save()` on a serializer with invalid data.'
        )

        # 断言没有错误使用 commit 关键字参数到额外数据中
        assert 'commit' not in kwargs, (
            "'commit' is not a valid keyword argument to the 'save()' method. "
            "If you need to access data before committing to the database then "
            "inspect 'serializer.validated_data' instead. "
            "You can also pass additional keyword arguments to 'save()' if you "
            "need to set extra attributes on the saved model instance. "
            "For example: 'serializer.save(owner=request.user)'.'"
        )

        # 断言对象保存之前没有进行数据访问，保证数据和对象的一致性
        assert not hasattr(self, '_data'), (
            "You cannot call `.save()` after accessing `serializer.data`."
            "If you need to access data before committing to the database then "
            "inspect 'serializer.validated_data' instead. "
        )

        # 合并验证后数据和额外数据
        validated_data = dict(
            list(self.validated_data.items()) +
            list(kwargs.items())
        )

        # 更新操作，插入预处理和后处理
        if self.instance is not None:
            self.instance.pre_update(validated_data)
            self.instance = self.update(self.instance, validated_data)
            assert self.instance is not None, (
                '`update()` did not return an object instance.'
            )
            self.instance.post_update()

        # 创建操作，进行预处理和后处理
        else:
            self.Meta.model.pre_create(validated_data)
            self.instance = self.create(validated_data)
            assert self.instance is not None, (
                '`create()` did not return an object instance.'
            )
            self.instance.post_create()

        return self.instance


class DisplaySerializer(BaseSerializer):
    """
    展示型序列器
    """

    uuid = CharField(max_length=32, read_only=True)


class ManageSerializer(DisplaySerializer):
    """
    管理型序列器
    """

    created_by = CharField(max_length=32, read_only=True)
    updated_by = CharField(max_length=32, read_only=True)

    def validate(self, data: dict) -> dict:
        """
        全局数据认证
        :param data: 序列化传入数据
        """
        user_uuid = self.context.get('request').user.uuid

        # 创建则填充创建用户，否则填充修改用户
        if not self.instance:
            data['created_by'] = user_uuid
        else:
            data['updated_by'] = user_uuid

        return data


class BulkSerializerMixin(object):
    """
    序列器支持批量操作的混合类
    """

    def to_internal_value(self, data):
        """
        重写序列化数据逻辑，增加了防止子序列器验证后丢失 id_attr 字段的逻辑
        """
        ret = super(BulkSerializerMixin, self).to_internal_value(data)
        view = self.context.get('view')
        id_attr = view.lookup_url_kwarg or view.lookup_field
        request_method = getattr(view.request, 'method', '')

        # 防止子序列器验证后 id_attr 字段由于其 read_only 属性而丢失的逻辑
        if all((isinstance(self.root, BulkListSerializer),
                id_attr,
                request_method in ('PUT', 'PATCH'))):
            id_field = self.fields[id_attr]
            id_value = id_field.get_value(data)
            ret[id_attr] = id_value

        return ret


class BulkListSerializer(ListSerializer):
    """
    支持批量操作的列表序列化器，主要是：
    1、修复了 rest_framework_bulk 模块 无法处理批量更新的问题
    2、保存逻辑中加入基础模型中的预处理和后处理
    """

    def to_internal_value(self, data):
        """
        各个数据放入子序列化器中验证
        """
        # 解析 html 输入数据
        if html.is_html_input(data):
            data = html.parse_html_list(data)

        # 确认数据是列表
        if not isinstance(data, list):
            message = self.error_messages['not_a_list'].format(
                input_type=type(data).__name__
            )
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [message]
            }, code='not_a_list')

        # 确认非允许空的情况下数据不为空
        if not self.allow_empty and len(data) == 0:
            message = self.error_messages['empty']
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [message]
            }, code='empty')

        # 将各个数据放入子序列化器中验证
        ret = []
        errors = []
        for item in data:
            try:
                # 区分是否当前是否为更新操作
                if self.instance is not None:
                    view = self.context.get('view')
                    id_attr = view.lookup_url_kwarg or view.lookup_field
                    instance = self.instance.get(**{id_attr: item[id_attr]})
                    self.child.instance = instance
                validated = self.child.run_validation(item)
            except ValidationError as exc:
                errors.append(exc.detail)
            else:
                ret.append(validated)
                errors.append({})

        if any(errors):
            raise ValidationError(errors)

        # 还原子序列化器对象的 instance 属性
        self.child.instance = self.instance

        return ret

    def save(self, **kwargs):
        """
        加入对子序列器模型是基础模型的断言
        :param kwargs: 额外数据
        """
        assert issubclass(self.child.Meta.model, BaseModel), (
            'Serializer `%s.%s.Meta.model` is subclass of BaseModel' %
            (self.__class__.__module__, self.__class__.__name__)
        )
        super().save(**kwargs)

    def update(self, queryset, all_validated_data):
        """
        用组建的字典进行批量更新，并加入基础模型中的预处理和后处理
        """
        # 分离 id 和验证信息
        view = self.context.get('view')
        id_attr = view.lookup_url_kwarg or view.lookup_field
        all_validated_data_by_id = {
            i.pop(id_attr): i
            for i in all_validated_data
        }

        # 分别对每个对象进行更新
        updated_objects = []
        for _id, validated_data in all_validated_data_by_id.items():
            obj = self.instance.get(**{id_attr: _id})

            # 子序列器执行更新操作
            obj.pre_update(validated_data)
            obj = self.child.update(obj, validated_data)
            obj.post_update()
            updated_objects.append(obj)

        return updated_objects

    def create(self, validated_data):
        """
        加入基础模型中的预处理和后处理
        """
        created_objects = []
        model_class = self.child.Meta.model

        for data in validated_data:
            model_class.pre_create(data)
            obj = self.child.create(data)
            obj.post_create()
            created_objects.append(obj)

        return created_objects
