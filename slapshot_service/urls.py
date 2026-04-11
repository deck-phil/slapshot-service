"""
URL configuration for slapshot_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import path, include
from django.views.decorators.http import require_POST

from stats.views.custom_404_view import custom_404_view

admin.site.login_url = "/login/"

handler404 = custom_404_view


@require_POST
def logout_view(request):
    logout(request)
    return redirect(request.META.get("HTTP_REFERER", "/"))


urlpatterns = [
    path('admin/', admin.site.urls),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("", include("stats.urls")),
]
