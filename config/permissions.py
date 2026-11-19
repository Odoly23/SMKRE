from rest_framework.permissions import BasePermission
from users.auth_utils import c_user_group


# fábrika permisaun DRF tuir papél; uza: permission_classes = [IsAuthenticated, HasRole(*ROLE_VERIFIKA)]
def HasRole(*roles):
	class _HasRole(BasePermission):
		def has_permission(self, request, view):
			return c_user_group(request.user) in roles
	return _HasRole
