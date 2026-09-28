from django.shortcuts import redirect, render
from functools import wraps
from users.auth_utils import c_user_group


def unauthenticated_user(view_func):
	@wraps(view_func)
	def wrapper_func(request, *args, **kwargs):
		if request.user.is_authenticated:
			return redirect('home')
		else:
			return view_func(request, *args, **kwargs)
	return wrapper_func


def allowed_users(allowed_roles=[]):
	def decorator(view_func):
		@wraps(view_func)
		def wrapper_func(request, *args, **kwargs):
			group = c_user_group(request.user)
			if group in allowed_roles:
				return view_func(request, *args, **kwargs)
			else:
				return render(request, 'home/403.html', status=403)
		return wrapper_func
	return decorator
