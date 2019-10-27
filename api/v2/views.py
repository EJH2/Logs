import json

import requests
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from drf_yasg.utils import swagger_auto_schema
from itsdangerous import BadSignature
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.models import Log
from api.permissions import HasAPIAccess
from api.utils import signer
from api.v2 import schemas
from api.v2.parser import create_log
from api.v2.serializers import LogListSerializer, LogCreateSerializer, LogArchiveCreateSerializer


@swagger_auto_schema(method='POST', query_serializer=LogArchiveCreateSerializer, responses=schemas.archive_responses)
@permission_classes([HasAPIAccess])
@api_view(['POST'])
def archive(request):
    serializer = LogArchiveCreateSerializer(data=request.data, context={'user': request.user})
    if not serializer.is_valid():
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    signed_data = signer.dumps(serializer.data)
    url = request.build_absolute_uri(reverse('v2:un-archive', kwargs={'signed_data': signed_data}))
    return Response(data={'url': url}, status=status.HTTP_201_CREATED)


@swagger_auto_schema(method='GET', auto_schema=None)
@permission_classes([HasAPIAccess])
@api_view(['GET'])
def un_archive(request, signed_data: str):
    try:
        data = signer.loads(signed_data)
    except BadSignature:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    data['messages'] = json.loads(requests.get(data['url']).text)
    log = create_log(content=data['messages'], log_type=data['type'], owner=request.user, expires=data['expires'],
                     privacy=data['privacy'], guild=data['guild'])
    return redirect('log-html', pk=log.uuid)


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
