from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_info(request):
    try:
        user = User.objects.get(id=request.user.id)
        groups = []
        for group in user.groups.all():
            groups.append(group.name)
        user_info = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'date_joined': user.date_joined.isoformat(),
            'groups': groups,
            #'permissions': user.user_permissions,
            'last_login': user.last_login if user.last_login is None else user.last_login.isoformat(),
            'is_staff': user.is_staff,
        }
        print('user_info', user_info)
        return Response(user_info)
    except Exception:
        return Response('user does not exist', status=status.HTTP_403_FORBIDDEN) 
