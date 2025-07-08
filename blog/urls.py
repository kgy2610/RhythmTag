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
    
    # 블로그 관련
    path('create/', views.BlogCreateView.as_view(), name='blog_create'),
    path('update/', views.BlogUpdateView.as_view(), name='blog_update'),
    path('delete/', views.BlogDeleteView.as_view(), name='blog_delete'),

    # 사용자 관련
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile_update'),
    path('profile/passwordupdate/', views.PasswordChangeView.as_view(), name='password_change'),
    path('profile/delete/', views.AccountDeleteView.as_view(), name='profile_delete'),
    path('logout/', views.LogoutView.as_view(), name="logout"),
]