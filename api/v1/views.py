from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.response import Response

from api.models import Log
from api.v1.parser import create_log
from api.permissions import HasAPIAccess
from api.v1 import schemas
from api.v1.serializers import LogListSerializer, LogCreateSerializer


class LogViewSet(viewsets.ViewSet):
    permission_classes = (HasAPIAccess,)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Log.objects.none()
        queryset = Log.objects.filter(owner=self.request.user)
        return queryset

    @swagger_auto_schema(responses=schemas.list_responses)
    def list(self, request):
        queryset = self.get_queryset()
        serializer = LogListSerializer(queryset, context={'request': request}, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(manual_parameters=[schemas.url_parameter], responses=schemas.read_responses)
    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        log = get_object_or_404(queryset, pk=pk)
        serializer = LogListSerializer(log, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(query_serializer=LogCreateSerializer, responses=schemas.create_responses)
    def create(self, request):
        serializer = LogCreateSerializer(data=request.data, context={'user': request.user})
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.data
        log = create_log(content=data['messages'], log_type=data['type'], owner=request.user, expires=data['expires'],
                         privacy=data['privacy'], guild=data['guild'])
        serializer = LogListSerializer(log, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(manual_parameters=[schemas.url_parameter])
    def destroy(self, request, pk=None):
        queryset = self.get_queryset()
        log = get_object_or_404(queryset, pk=pk)
        log.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
