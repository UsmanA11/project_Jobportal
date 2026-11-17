"""
URL configuration for jobportal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
from django.contrib.auth.views import LoginView
from django.urls import include, path

from accounts import views as account_views
from jobs import views as job_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'accounts/login/',
        LoginView.as_view(template_name='login.html'),
        name='login',
    ),
    path('accounts/signup/', account_views.signup_view, name='signup'),
    path('accounts/switch-role/', job_views.switch_role, name='switch_role'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', job_views.JobListView.as_view(), name='job_list'),
    path('jobs/create/', job_views.JobCreateView.as_view(), name='job_create'),
    path('jobs/<int:pk>/', job_views.JobDetailView.as_view(), name='job_detail'),
    path('jobs/<int:pk>/update/', job_views.JobUpdateView.as_view(), name='job_update'),
    path('jobs/<int:pk>/delete/', job_views.JobDeleteView.as_view(), name='job_delete'),
    path('jobs/<int:job_id>/apply/', job_views.apply_to_job, name='apply_to_job'),
    path('my/jobs/', job_views.MyJobsListView.as_view(), name='my_jobs'),
    path(
        'my/applications/',
        job_views.MyApplicationsListView.as_view(),
        name='my_applications',
    ),
]
