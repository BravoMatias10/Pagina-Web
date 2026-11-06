from django.urls import path
from . import views
urlpatterns=[path('registro/',views.register,name='register'),path('',views.dashboard,name='dashboard'),path('nueva/',views.new,name='new'),path('auditoria/<int:pk>/',views.detail,name='detail'),path('auditoria/<int:pk>/pdf/',views.download,name='pdf'),path('auditoria/<int:pk>/enviar/',views.send,name='send'),path('auditoria/<int:pk>/eliminar/',views.delete,name='delete'),path('privacidad/',views.privacy,name='privacy')]
