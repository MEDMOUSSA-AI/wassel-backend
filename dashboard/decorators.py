from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


def admin_required(view_func):
    """
    يسمح بالوصول فقط للمستخدمين المسجلين دخولهم ولديهم role = admin.
    """
    @wraps(view_func)
    @login_required(login_url="dashboard:login")
    def wrapped(request, *args, **kwargs):
        if getattr(request.user, "role", None) != "admin":
            return redirect("dashboard:login")
        return view_func(request, *args, **kwargs)
    return wrapped
