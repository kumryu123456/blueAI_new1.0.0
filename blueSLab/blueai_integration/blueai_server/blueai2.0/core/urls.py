# core/urls.py - URL configuration
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Main pages
    path('', views.index, name='index'),  # Welcome page
    path('task/<int:task_id>/', views.task_detail_view, name='task_detail'),  # Individual conversation page
    
    # API endpoints
    path('api/process_input/', views.process_input, name='process_input'),
    path('api/get_tasks/', views.get_tasks, name='get_tasks'),
    path('api/get_task/<int:task_id>/', views.get_task, name='get_task'),
    path('api/update_conversation/', views.update_conversation, name='update_conversation'),
    path('api/execute_task/', views.execute_task, name='execute_task'),
    path('api/delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('api/update_task_title/', views.update_task_title, name='update_task_title'),
    path('api/tasks/<int:task_id>/share', views.share_task, name='share_task'),
    path('api/tasks/<int:task_id>/project', views.add_task_to_project, name='add_task_to_project'),
    
    # Favorites related API
    path('api/toggle_favorite/<int:task_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('api/get_favorites/', views.get_favorites, name='get_favorites'),
]