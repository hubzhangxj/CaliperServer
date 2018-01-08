"""CaliperServer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from account import views as aViews
from django.conf.urls.static import static
from CaliperServer import  settings

urlpatterns = [
    url('^download$',aViews.download),
    url('^userinfo/$',aViews.getuserinfo),
    url('^userinfo/set/$',aViews.setuserinfo),
    url('^userinfo/upload$', aViews.upload),
    url('^login$',aViews.login),
    url('^logout$', aViews.logout),
    url('^register', aViews.signup),
    url(r'^changepwd$', aViews.change_pwd),
    url(r'^authcallback$', aViews.auth_callback, name="authcallback"),
    url(r'^logoutnotify$', aViews.logout_notify, name="logoutnotify"),
    url(r'^signupcallback$', aViews.signup_callback, name="signupcallback"),
    url(r'^changepwdcallback$', aViews.changepwd_callback, name="changepwdcallback"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
