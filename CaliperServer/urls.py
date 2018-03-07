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
from django.conf.urls import url,include
from django.conf.urls.static import static
from django.contrib import admin

from CaliperServer import settings
from account import urls as userUrl
from account import views as userViews
from data import urls as dataUrl
from task import urls as taskUrl
from account import views as accountView

urlpatterns = [
                  url(r'^admin/', admin.site.urls),
                  url(r'^$', accountView.main),
                  url(r'^uams/logoutnotify$', userViews.logout_notify),
                  url(r'^uams/locknotify$', userViews.lock_notify),
                  url(r'^uams/unlocknotify$', userViews.unlock_notify),
                  url('^user/', include(userUrl)),
                  url('^task/', include(taskUrl)),
                  url('^data/', include(dataUrl)),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
