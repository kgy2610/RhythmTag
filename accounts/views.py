# accounts/views.py

from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, FormView, DetailView, UpdateView, DeleteView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.views import PasswordChangeView as DjangoPasswordChangeView
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import User, Follow
from blog.models import Post

User = get_user_model()


class MainPageView(TemplateView):
    template_name = "accounts/main.html"


class CustomLoginView(FormView):
    template_name = 'accounts/login.html'
    form_class = CustomAuthenticationForm
    success_url = reverse_lazy('post_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        user = form.get_user()
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f'환영합니다, {user.nickname}님!')
            return redirect(self.success_url)
        else:
            # 이 경우는 발생하지 않아야 하지만, 안전장치
            messages.error(self.request, '로그인 처리 중 오류가 발생했습니다.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        # 폼 검증 실패 시 오류 메시지
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return super().form_invalid(form)

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)


class CustomRegisterView(FormView):
    template_name = "accounts/register.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        user = form.save()
        messages.success(
            self.request,
            f"회원가입이 완료되었습니다, {user.nickname}님! 로그인해주세요.",
        )
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("post_list")
        return super().get(request, *args, **kwargs)


class CustomLogoutView(View):
    def post(self, request):
        logout(request)
        messages.success(request, "로그아웃되었습니다.")
        return redirect("post_list")

    def get(self, request):
        logout(request)
        messages.success(request, "로그아웃되었습니다.")
        return redirect("post_list")


# 본인 프로필 페이지
class MyProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_posts"] = Post.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )[:5]
        context["total_posts"] = Post.objects.filter(user=self.request.user).count()

        # 팔로워/팔로잉 수 추가
        context["followers_count"] = self.request.user.followers_count
        context["following_count"] = self.request.user.following_count

        return context


# 다른 사용자 프로필 페이지
class UserProfileView(DetailView):
    model = User
    template_name = "accounts/profile_user.html"
    context_object_name = "profile_user"
    pk_url_kwarg = "user_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.get_object()

        # 팔로우 상태 확인
        if self.request.user.is_authenticated:
            context["is_following"] = self.request.user.is_following(profile_user)
        else:
            context["is_following"] = False

        # 팔로워/팔로잉 수
        context["followers_count"] = profile_user.followers_count
        context["following_count"] = profile_user.following_count

        # 해당 사용자의 게시글들
        context["user_posts"] = Post.objects.filter(user=profile_user).order_by(
            "-created_at"
        )[:10]

        return context
    

# 프로필 수정 뷰
class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'accounts/profile_update.html'
    fields = ['nickname', 'name', 'phone']  # 수정 가능한 필드들
    success_url = reverse_lazy('user_profile')
    
    def get_object(self):
        return self.request.user  # 현재 로그인한 사용자만 수정 가능
    
    def form_valid(self, form):
        messages.success(self.request, '프로필이 성공적으로 수정되었습니다.')
        return super().form_valid(form)

# 비밀번호 변경 뷰
class PasswordChangeView(LoginRequiredMixin, DjangoPasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('user_profile')
    
    def form_valid(self, form):
        messages.success(self.request, '비밀번호가 성공적으로 변경되었습니다.')
        return super().form_valid(form)

# 계정 삭제 뷰
class AccountDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/account_delete.html'
    success_url = reverse_lazy('main_page')
    
    def get_object(self):
        return self.request.user  # 현재 로그인한 사용자만 삭제 가능
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '계정이 성공적으로 삭제되었습니다.')
        return super().delete(request, *args, **kwargs)


# 팔로우 토글 함수 (Ajax 지원)
@login_required
@require_POST
def toggle_follow(request, user_id):
    print(f"팔로우 요청 받음: user_id={user_id}")  # 👈 디버깅
    print(f"요청 사용자: {request.user}")          # 👈 디버깅
    target_user = get_object_or_404(User, id=user_id)

    if request.user == target_user:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"error": "자기 자신을 팔로우할 수 없습니다."}, status=400
            )
        messages.error(request, "자기 자신을 팔로우할 수 없습니다.")
        return redirect("other_user_profile", user_id=user_id)

    # 팔로우 상태 확인 및 토글
    follow_obj, created = Follow.objects.get_or_create(
        follower=request.user, following=target_user
    )

    if not created:
        follow_obj.delete()
        is_following = False
        message = f"{target_user.nickname}님을 언팔로우했습니다."
    else:
        is_following = True
        message = f"{target_user.nickname}님을 팔로우했습니다."

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "is_following": is_following,
                "followers_count": target_user.followers_count,
                "following_count": target_user.following_count,
                "message": message,
            }
        )
    else:
        messages.success(request, message)
        return redirect("other_user_profile", user_id=user_id)
