# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 기본 페이지
    path('', views.MainPageView.as_view(), name='main_page'),
    
    # 인증 관련
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.CustomRegisterView.as_view(), name='register'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # 프로필 관련
    path('profile/', views.MyProfileView.as_view(), name='user_profile'),  # 본인 프로필
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile_update'),
    path('profile/passwordupdate/', views.PasswordChangeView.as_view(), name='password_change'),
    path('profile/delete/', views.AccountDeleteView.as_view(), name='profile_delete'),
    
    # 다른 사용자 관련
    path('user/<int:user_id>/profile/', views.UserProfileView.as_view(), name='other_user_profile'),
    path('user/<int:user_id>/follow/', views.toggle_follow, name='toggle_follow'),
]