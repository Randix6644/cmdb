from rest_framework.fields import CharField, ListField, IntegerField
from utils import safe_json_dumps, safe_json_loads
from utils import DAOException
from rest_framework.exceptions import ValidationError


__all__ = [
    'JsonField',
    'JsonListField',
    'TypeIntegerField'
]


class JsonField(CharField):
    """
    json 作为内部值的任意可序列化类型字段，不验证类型
    """

    def to_internal_value(self, data):
        """
        数据是字典，存入前先编码化为 json
        """
        value = safe_json_dumps(data)
        return super().to_internal_value(value)

    def to_representation(self, value):
        """
        数据是 json，取出前先对 json 解码
        """
        if value is None:
            return None
        value = super().to_representation(value)
        return safe_json_loads(value)


class JsonListField(ListField):
    """
    json 作为内部值的列表字段，会验证列表的元素类型
    """

    def to_internal_value(self, data):
        """
        数据是列表，存入前先编码化为 json
        """
        value = super().to_internal_value(data)
        return safe_json_dumps(value)

    def to_representation(self, value):
        """
        数据是 json，取出前先对 json 解码
        """
        value = safe_json_loads(value)
        return super().to_representation(value)


class TypeIntegerField(IntegerField):
    """
    整数作为内部值的类型字段
    """

    def __init__(self, **kwargs):
        self.mapping = kwargs.pop('mapping', None)
        assert isinstance(self.mapping, tuple), 'Mapping is not a tuple'
        kwargs['max_value'] = len(self.mapping) - 1
        kwargs['min_value'] = 0
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        """
        外部数据是字符串，转为数字后再继续
        """
        data = self.mapping.index(data)
        return super().to_internal_value(data)

    def to_representation(self, value):
        """
        内部数据是数字，取出后解析为映射
        """
        value = super().to_representation(value)
        return self.mapping[value]


class LogicalForeignField(CharField):
    """
    逻辑外键字段
    """

    def __init__(self, model, display_fields=None, **kwargs):
        self.model = model
        self.display_fields = display_fields
        kwargs['allow_blank'] =  False
        kwargs['trim_whitespace'] = True
        kwargs['max_length'] = 32
        kwargs['min_length'] = 32
        super().__init__(**kwargs)

    def run_validation(self, data=''):
        data = super().run_validation(data)

        try:
            self.model.dao.get_obj(uuid=data)
        except DAOException:
            raise ValidationError(f'uuid `{data}` is not found')

        return data

    def to_internal_value(self, data):
        return super().to_internal_value(data)

    def to_representation(self, value):
        value = super().to_representation(value)
        obj = self.model.dao.get_obj(uuid=value)
        if self.display_fields is None:
            d = obj.__dict__
            del d['_state']
            return d
        else:
            return {
                field: getattr(obj, field)
                for field in self.display_fields
            }
