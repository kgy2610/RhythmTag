# accounts/urls.py
from django.urls import path
from .views import MainPageView, CustomLoginView, CustomRegisterView, CustomLogoutView

urlpatterns = [
    path('', MainPageView.as_view(), name='main_page'),  # 루트 경로에서 main.html 표시
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', CustomRegisterView.as_view(), name='register'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
]