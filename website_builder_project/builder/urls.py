# builder/urls.py 파일을 수정하세요

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('website/create/', views.create_website, name='create_website'),
    path('website/<int:website_id>/edit/', views.edit_website, name='edit_website'),
    path('website/<int:website_id>/preview/', views.preview_website, name='preview_website'),
    path('website/<int:website_id>/send-message/', views.send_message, name='send_message'),
    path('website/<int:website_id>/save/', views.save_website, name='save_website'),
    # 새로 추가된 URL 패턴
    path('website/<int:website_id>/clear-conversation/', views.clear_conversation, name='clear_conversation'),
    path('website/<int:website_id>/get-code/', views.get_website_code, name='get_website_code'),
    path('website/<int:website_id>/update-code/', views.update_website_code, name='update_website_code'),
    path('website/<int:website_id>/export/', views.export_website, name='export_website'),
]