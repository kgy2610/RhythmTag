# blog/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # 게시글 관련
    path('', views.PostListView.as_view(), name='post_list'),
    path('post/write/', views.PostWriteView.as_view(), name='post_write'),
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/<int:pk>/update/', views.PostUpdateView.as_view(), name='post_update'),
    path('post/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('post/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    
    # 블로그 관련
    path('create/', views.BlogCreateView.as_view(), name='blog_create'),
    path('update/', views.BlogUpdateView.as_view(), name='blog_update'),
    path('delete/', views.BlogDeleteView.as_view(), name='blog_delete'),
]