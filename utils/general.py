from typing import AnyStr, Union, Optional
from importlib import import_module
from django.conf import settings
import json, uuid, logging


__all__ = [
    'logger',
    'safe_json_dumps',
    'safe_json_loads',
    'dynamic_import_class',
    'generate_unique_uuid'
]


# 获取日志器
logger = logging.getLogger(settings.LOGGER)


def safe_json_dumps(d: Union[dict, list]) -> str:
    """
    安全的 json 序列化，一定返回字符串，且通过返回空字符串来代替报错
    :param d: 字典或列表
    :return: 字符串
    """
    if not isinstance(d, (dict, list)):
        return ''

    try:
        return json.dumps(d)
    # 以下两种异常能捕捉此处的所有可能
    except (TypeError, ValueError):
        return ''


def safe_json_loads(s: Union[AnyStr, bytearray]) -> Union[dict, list]:
    """
    安全的 json 反序列化，一定能返回字典，且通过返回空字典来代替报错
    :param s: 字符串
    :return: 字典
    """
    try:
        obj = json.loads(s)
    # 以下两种异常能捕捉此处的所有可能
    except (TypeError, ValueError):
        return {}

    if isinstance(obj, (dict, list)):
        return obj

    else:
        return {}


def dynamic_import_class(dotted_path: str) -> Optional[type]:
    """
    动态加载以字符串表示的模块中的类，也可用于模块中的函数或变量
    :param dotted_path: [包.]模块.[类|函数|变量]
    :return: 类、函数或变量
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        return None

    try:
        m = import_module(module_path)
    except ModuleNotFoundError:
        return None

    try:
        return getattr(m, class_name)
    except AttributeError:
        return None


def generate_unique_uuid() -> str:
    """
    获取唯一性的 uuid
    :return: str, 十六进制 uuid
    """
    uuid_hex = uuid.uuid1().hex
    return uuid_hex
