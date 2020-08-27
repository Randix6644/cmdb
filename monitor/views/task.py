from rest_framework.views import APIView
from django.views import View
from django.http import JsonResponse
from monitor.event.rpc import RPCClient


class TaskView(View):
    def get(self):
        with RPCClient() as cli:
            cli.get_jobs()

    def post(self, request):
        with RPCClient() as cli:
            cli.add_interval_job(
                'monitor.task.MonitorSync', {
                    'seconds': 15})
        return JsonResponse({})

