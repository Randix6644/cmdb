from common.viewsets import BulkManageViewSet
from ..models import Project
from ..serializer import ProjectSerializer


__all__ = [
    'ProjectViewSet'
]


class ProjectViewSet(BulkManageViewSet):
    """
    项目视图集
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'uuid'
