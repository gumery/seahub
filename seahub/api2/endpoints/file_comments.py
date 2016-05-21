import logging

from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from seaserv import seafile_api
from pysearpc import SearpcError

from seahub.api2.authentication import TokenAuthentication
from seahub.api2.permissions import IsRepoAccessible
from seahub.api2.throttling import UserRateThrottle
from seahub.api2.utils import api_error, user_to_dict
from seahub.avatar.settings import AVATAR_DEFAULT_SIZE
from seahub.base.models import FileComment

logger = logging.getLogger(__name__)


class FileCommentsView(APIView):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, IsRepoAccessible)
    throttle_classes = (UserRateThrottle, )

    def get(self, request, repo_id, format=None):
        """List all comments of a file.
        """
        path = request.GET.get('p', '/').rstrip('/')
        if not path:
            return api_error(status.HTTP_400_BAD_REQUEST, 'Wrong path.')

        try:
            avatar_size = int(request.GET.get('avatar_size',
                                              AVATAR_DEFAULT_SIZE))
        except ValueError:
            avatar_size = AVATAR_DEFAULT_SIZE

        comments = []
        for o in FileComment.objects.get_by_file_path(repo_id, path):
            comment = o.to_dict()
            comment.update(user_to_dict(request.user.username, request=request,
                                        avatar_size=avatar_size))
            comments.append(comment)

        return Response({
            "comments": comments,
        })

    def post(self, request, repo_id, format=None):
        """Post a comments of a file.
        """
        path = request.GET.get('p', '/').rstrip('/')
        if not path:
            return api_error(status.HTTP_400_BAD_REQUEST, 'Wrong path.')

        try:
            avatar_size = int(request.GET.get('avatar_size',
                                              AVATAR_DEFAULT_SIZE))
        except ValueError:
            avatar_size = AVATAR_DEFAULT_SIZE

        try:
            obj_id = seafile_api.get_file_id_by_path(repo_id,
                                                     path)
        except SearpcError as e:
            logger.error(e)
            return api_error(status.HTTP_500_INTERNAL_SERVER_ERROR,
                             'Internal error.')
        if not obj_id:
            return api_error(status.HTTP_404_NOT_FOUND, 'File not found.')

        comment = request.data.get('comment', '')
        if not comment:
            return api_error(status.HTTP_400_BAD_REQUEST, 'Comment can not be empty.')

        username = request.user.username
        o = FileComment.objects.add_by_file_path(
            repo_id=repo_id, file_path=path, author=username, comment=comment)
        comment = o.to_dict()
        comment.update(user_to_dict(request.user.username, request=request,
                                    avatar_size=avatar_size))
        return Response(comment, status=201)
