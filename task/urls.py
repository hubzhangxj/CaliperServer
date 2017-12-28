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
from django.contrib import admin
from task import views as taskViews

urlpatterns = [
    url(r"^list$", taskViews.task),
    url(r"^page$",taskViews.pageChange),
    url(r"^filter$",taskViews.filter),
    url(r"^single$",taskViews.singleTask),
    url(r"^compare$",taskViews.compare),
    url(r"^compare/(\w+)$", taskViews.dimcompare),
    url(r"^single/(\w+)$", taskViews.tool_result),
    url(r"^highlight$",taskViews.highlightChange),
    url(r"^folder/(\d+)$", taskViews.folder),
    url("^boardInfo/?$", taskViews.boardInfo),
    url("^boardInfo/searchUser/?$", taskViews.stateSearchUser),
    url("^boardInfo/page/?$", taskViews.statePageChange),
    url("^boardInfo/filter/?$", taskViews.stateFilter),
    url("^boardInfo/rowdelete/?$", taskViews.rowdelete),
    url("^boardInfo/rowRestore/?$", taskViews.rowRestore),
    url("^boardInfo/permanentDelete/?$", taskViews.permanentDelete),
    url("^download/?$", taskViews.downloadFile),
    url("^list/userlist/?$", taskViews.userList),
    url("^list/addusersubmit/?$", taskViews.addUserSubmit),
    url("^list/adduser/?$", taskViews.addUser),
    url("^list/page/?$", taskViews.listPage),
    url("^list/delete/?$", taskViews.delete),

]
