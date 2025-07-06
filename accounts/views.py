# accounts/views.py
from django.views.generic import TemplateView, FormView
from django.contrib.auth.views import LogoutView
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, CustomAuthenticationForm

class MainPageView(TemplateView):
    template_name = 'accounts/main.html'

class CustomLoginView(FormView):
    template_name = 'accounts/login.html'
    form_class = CustomAuthenticationForm
    success_url = reverse_lazy('post_list')
    
    def form_valid(self, form):
        # form.cleaned_data['id']에 아이디(username)가 들어있음
        username = form.cleaned_data['id']  # 필드명이 id이지만 실제로는 username
        password = form.cleaned_data['password']
        
        # Django 기본 인증
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f'환영합니다, {user.first_name}님!')
            return redirect(self.success_url)
        else:
            form.add_error('id', '아이디 또는 비밀번호가 잘못되었습니다.')
            return self.form_invalid(form)
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)

class CustomRegisterView(FormView):
    template_name = 'accounts/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, f'회원가입이 완료되었습니다, {user.first_name}님! 로그인해주세요.')
        return super().form_valid(form)
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('post_list')
        return super().get(request, *args, **kwargs)

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('main_page')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(request, f'안녕히 가세요, {request.user.first_name}님!')
        return super().dispatch(request, *args, **kwargs)