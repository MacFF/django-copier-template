from rest_framework import viewsets
from rest_framework import mixins

class GenericActionViewSet(viewsets.GenericViewSet):
    """
    A viewset that provides default `get_serializer_class` method
    to return different serializers for different actions.
    """
    action_serializers = {}

    def get_serializer_class(self):
        return self.action_serializers.get(self.action, None) or super().get_serializer_class()


class ModelViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericActionViewSet):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """
    pass
