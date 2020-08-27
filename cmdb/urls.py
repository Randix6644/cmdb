from django.urls import re_path, include


urlpatterns = [
    re_path('cmdb/', include('asset.urls')),
    re_path('cmdb/', include('monitor.urls'))
]
