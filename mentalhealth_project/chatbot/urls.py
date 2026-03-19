from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('home/', views.home, name='home'), 
    path('logout/', views.logout_view, name='logout'),
    path('chat/', views.chat, name='chat'),
    path('new_chat/', views.new_chat, name='new_chat'),
    path('rename_chat/', views.rename_chat, name='rename_chat'),
    path('delete_chat/', views.delete_chat, name='delete_chat'),
]