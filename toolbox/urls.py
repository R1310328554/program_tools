from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tools/<slug:slug>/', views.tool_page, name='tool'),
    path('api/tools/<slug:slug>/', views.tool_api, name='tool_api'),
]
