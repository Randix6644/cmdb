from typing import Union, Optional
from pytz import timezone
from datetime import datetime, timedelta
import time
from django.conf import settings


__all__ = [
    'get_datetime_with_tz',
    'get_datetime_in_format',
    'formatted_str_to_datetime',
    'datetime_to_timestamp'
]


def get_datetime_with_tz(
        dt: Optional[Union[datetime, tuple, int]] = None, **timedelta_kwargs) -> datetime:
    """
    得到指定时区的 datetime 对象，允许额外进行时间增减
    :param dt: datetime 对象或可转化为 datetime 对象的对象，默认为当前时间的 datetime 对象
    :param timedelta_kwargs: timedelta 所需参数，来额外进行时间增减
    :return: datetime 对象
    """
    if not isinstance(dt, datetime):
        if isinstance(dt, tuple):
            dt = datetime(*dt)
        elif isinstance(dt, int):
            dt = datetime.fromtimestamp(dt)
        else:
            dt = datetime.now()

    tz = timezone(settings.TIME_ZONE)
    dt_with_tz = dt.astimezone(tz)

    if timedelta_kwargs:
        dt_with_tz += timedelta(**timedelta_kwargs)
    return dt_with_tz


def get_datetime_in_format(
        dt: Optional[Union[datetime, tuple, int]] = None, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    得到指定格式的 datetime 对象
    :param dt: datetime 对象或可转化为 datetime 对象的对象，默认为当前时间的 datetime 对象
    :param fmt: 自定义格式，默认为人性化格式
    :return: 格式化字符串
    """
    datetime_with_tz = get_datetime_with_tz(dt)
    return datetime_with_tz.strftime(fmt)


def formatted_str_to_datetime(s: Optional[str] = None, fmt: str = '%Y-%m-%d %H:%M:%S') -> datetime:
    """
    转化指定格式的字符串为 datetime 对象，，默认得到当前 datetime 对象
    :param s: 指定格式的字符串
    :param fmt: 自定义格式，默认为人性化格式
    :return: 格式化字符串
    """
    if not s:
        dt = None
    else:
        dt = datetime.strptime(s, fmt)
    return get_datetime_with_tz(dt)


def datetime_to_timestamp(dt: Optional[datetime] = None) -> int:
    """
    转化 datetime 对象为时间戳，默认得到当前时间戳
    :param dt: datetime 对象
    :return: int, 时间戳
    """
    if not dt:
        return time.time()

    timetuple = dt.timetuple()
    return time.mktime(timetuple)
