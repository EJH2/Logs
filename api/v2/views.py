import json

import requests
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from drf_yasg.utils import swagger_auto_schema
from itsdangerous import BadSignature
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.models import Log, Whitelist
from api.permissions import HasAPIAccess, filter_queryset
from api.utils import signer
from api.v2 import schemas
from api.v2.parser import create_log
from api.v2.serializers import LogListSerializer, LogCreateSerializer, LogArchiveCreateSerializer, LogPatchSerializer


@swagger_auto_schema(method='POST', query_serializer=LogArchiveCreateSerializer, responses=schemas.archive_responses)
@permission_classes([HasAPIAccess])
@api_view(['POST'])
def archive(request):
    serializer = LogArchiveCreateSerializer(data=request.data, context={'user': request.user})
    if not serializer.is_valid():
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.data
    whitelist = Whitelist.objects.filter(log_type=data['type']).first()
    if whitelist and request.user not in whitelist.users.all():
        return Response({'errors': {'type': [f'You are not authorized to use log type "{data["type"]}"!']}},
                        status=status.HTTP_400_BAD_REQUEST)
    signed_data = signer.dumps(data)
    url = request.build_absolute_uri(reverse('v2:un-archive', kwargs={'signed_data': signed_data}))
    return Response(data={'url': url}, status=status.HTTP_201_CREATED)


@swagger_auto_schema(method='GET', auto_schema=None)
@api_view(['GET'])
def un_archive(request, signed_data: str):
    try:
        data = signer.loads(signed_data)
    except BadSignature:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    try:
        messages = requests.get(data['url']).json()
    except json.JSONDecodeError:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    log = create_log(content=messages, log_type=data['type'], owner=request.user, expires=data['expires'],
                     privacy=data['privacy'], guild=data['guild'])
    return redirect('log-html', pk=log.uuid)


class LogViewSet(viewsets.ViewSet):
    permission_classes = (HasAPIAccess,)

    def get_queryset(self):
        return filter_queryset(self.request, Log.objects.all())

    @swagger_auto_schema(responses=schemas.list_responses)
    def list(self, request):
        """List all logs that you can own or manage."""
        queryset = self.get_queryset()
        serializer = LogListSerializer(queryset, context={'request': request}, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(manual_parameters=[schemas.url_parameter], responses=schemas.read_responses)
    def retrieve(self, request, pk=None):
        """Retrieve a log that you own."""
        queryset = self.get_queryset()
        log = get_object_or_404(queryset, pk=pk)
        serializer = LogListSerializer(log, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(query_serializer=LogPatchSerializer, manual_parameters=[schemas.url_parameter],
                         responses=schemas.partial_update_responses)
    def partial_update(self, request, pk=None):
        """Update an existing log. None of these query parameters are required!"""
        serializer = LogPatchSerializer(data=request.data, context={'user': request.user})
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.data
        queryset = self.get_queryset().filter(pk=pk)
        if not len(queryset) > 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        queryset.update(**data)
        serializer = LogListSerializer(queryset[0], context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(query_serializer=LogCreateSerializer, responses=schemas.create_responses)
    def create(self, request):
        """Create a log."""
        serializer = LogCreateSerializer(data=request.data, context={'user': request.user})
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.data
        whitelist = Whitelist.objects.filter(log_type=data['type']).first()
        if whitelist and request.user not in whitelist.users.all():
            return Response({'errors': {'type': [f'You are not authorized to use log type "{data["type"]}"!']}},
                            status=status.HTTP_400_BAD_REQUEST)
        log = create_log(content=data['messages'], log_type=data['type'], owner=request.user, expires=data['expires'],
                         privacy=data['privacy'], guild=data['guild'])
        serializer = LogListSerializer(log, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(manual_parameters=[schemas.url_parameter])
    def destroy(self, request, pk=None):
        """Delete a log that you own."""
        queryset = self.get_queryset().filter(pk=pk)
        if not len(queryset) > 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
