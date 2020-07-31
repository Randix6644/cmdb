from django.utils.deprecation import MiddlewareMixin
from django.utils.log import log_response
from utils import datetime_to_timestamp


__all__ = [
    'LoggingMiddleware'
]


class LoggingMiddleware(MiddlewareMixin):
    """
    记录请求日志的中间件
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.req_start = None

    def process_request(self, request):
        """
        记录请求开始时间
        """
        self.req_start = datetime_to_timestamp()

    def process_response(self, request, response):
        """
        记录请求日志
        """
        duration = datetime_to_timestamp() - self.req_start
        log_kwargs = {
            'response': response,
            'request': request
        }

        exc = getattr(response, 'with_exception', None)
        if exc:
            message = f'"{request.method} {request.get_full_path()}" "{exc.status_code} {exc.__class__.__name__}"' \
                      f' {len(response.getvalue())} {duration}'
            log_kwargs.update(level='error')
        else:
            message = f'"{request.method} {request.get_full_path()}" "{response.status_code} {response.reason_phrase}"' \
                      f' {len(response.getvalue())} {duration}'

        log_response(message, **log_kwargs)

        return response