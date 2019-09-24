from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.response import Response


@swagger_auto_schema(method='GET', auto_schema=None)
@api_view(['GET'])
def get_token(request):
    if not request.is_ajax():
        return Response(status=status.HTTP_403_FORBIDDEN)
    if not request.user.is_authenticated:
        return Response(data={'token': 'You have to log in first to see your token!'})
    if request.query_params.get('refresh'):
        Token.objects.filter(user=request.user).delete()

    token = Token.objects.get_or_create(user=request.user)
    return Response(data={'token': token[0].key})
