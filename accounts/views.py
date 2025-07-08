# accounts/views.py

from django.shortcuts import get_object_or_404, redirect, render
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
from .forms import CustomUserCreationForm, CustomAuthenticationForm, AccountDeleteForm
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

        user = self.request.user

        context["user_posts"] = Post.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )[:5]
        context["total_posts"] = Post.objects.filter(user=self.request.user).count()

        # 팔로워/팔로잉 수 추가
        context["followers_count"] = self.request.user.followers_count
        context["following_count"] = self.request.user.following_count

        # 내가 팔로우한 사람들 (팔로잉 목록)
        following_list = Follow.objects.filter(follower=user).select_related('following').order_by('-created_at')
        context["following_list"] = following_list
        
        # 나를 팔로우한 사람들 (팔로워 목록)
        followers_list = Follow.objects.filter(following=user).select_related('follower').order_by('-created_at')
        context["followers_list"] = followers_list
        
        # 팔로우 백 버튼을 위해 내가 팔로우한 사용자들의 목록
        following_users = [follow.following for follow in following_list]
        context["following_users"] = following_users

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
    template_name = 'accounts/profile_password_update.html'
    success_url = reverse_lazy('user_profile')
    
    def form_valid(self, form):
        messages.success(self.request, '비밀번호가 성공적으로 변경되었습니다.')
        return super().form_valid(form)

# 계정 삭제 뷰
class AccountDeleteView(LoginRequiredMixin, View):
    template_name = 'accounts/profile_delete.html'
    form_class = AccountDeleteForm
    
    def get_context_data(self):
        """계정 통계 정보 가져오기"""
        user = self.request.user
        
        # 블로그 수 (사용자당 하나의 블로그)
        blog_count = getattr(user, 'blog', None) and 1 or 0
        
        # 게시글 수
        post_count = user.post_set.count() if hasattr(user, 'post_set') else 0
        
        # 좋아요 수 (사용자가 누른 좋아요)
        like_count = user.like_set.count() if hasattr(user, 'like_set') else 0
        
        return {
            'blog_count': blog_count,
            'post_count': post_count,
            'like_count': like_count,
        }
    
    def get(self, request, *args, **kwargs):
        form = self.form_class(user=request.user)
        context = {
            'form': form,
            **self.get_context_data()
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(user=request.user, data=request.POST)
        
        if form.is_valid():
            # 폼이 유효하면 계정 삭제 진행
            user = request.user
            
            try:
                # 로그아웃 먼저 수행
                logout(request)
                
                # 사용자 삭제 (관련 데이터도 CASCADE로 삭제됨)
                user.delete()
                
                messages.success(request, '계정이 성공적으로 삭제되었습니다. 그동안 이용해 주셔서 감사했습니다.')
                return redirect('main_page')  # 또는 적절한 메인 페이지로
                
            except Exception as e:
                messages.error(request, '계정 삭제 중 오류가 발생했습니다. 다시 시도해주세요.')
                # 로그아웃된 상태이므로 로그인 페이지로 리다이렉트
                return redirect('login')
        
        # 폼이 유효하지 않으면 다시 페이지 표시
        context = {
            'form': form,
            **self.get_context_data()
        }
        return render(request, self.template_name, context)


# 팔로우 토글 함수 (Ajax 지원)
@login_required
@require_POST
def toggle_follow(request, user_id):
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


@login_required
@require_POST
def follow_user(request, userid):
    """
    사용자 아이디를 통해 팔로우하는 함수
    """
    target_user = get_object_or_404(User, userid=userid)
    
    if request.user == target_user:
        return JsonResponse({"success": False, "message": "자기 자신을 팔로우할 수 없습니다."}, status=400)
    
    # 이미 팔로우하고 있는지 확인
    if Follow.objects.filter(follower=request.user, following=target_user).exists():
        return JsonResponse({"success": False, "message": "이미 팔로우하고 있습니다."}, status=400)
    
    # 팔로우 생성
    Follow.objects.create(follower=request.user, following=target_user)
    
    return JsonResponse({
        "success": True,
        "message": f"{target_user.nickname}님을 팔로우했습니다.",
        "followers_count": target_user.followers_count
    })


# 언팔로우 함수 (사용자 아이디로)
@login_required
@require_POST
def unfollow_user(request, userid):
    """
    사용자 아이디를 통해 언팔로우하는 함수
    """
    target_user = get_object_or_404(User, userid=userid)
    
    if request.user == target_user:
        return JsonResponse({"success": False, "message": "자기 자신을 언팔로우할 수 없습니다."}, status=400)
    
    # 팔로우 관계 찾기 및 삭제
    try:
        follow_obj = Follow.objects.get(follower=request.user, following=target_user)
        follow_obj.delete()
        return JsonResponse({
            "success": True,
            "message": f"{target_user.nickname}님을 언팔로우했습니다.",
            "followers_count": target_user.followers_count
        })
    except Follow.DoesNotExist:
        return JsonResponse({"success": False, "message": "팔로우하지 않은 사용자입니다."}, status=400)

# 사용자 목록 뷰 (팔로우할 사용자를 찾기 위한 페이지)
class UserListView(TemplateView):
    template_name = "accounts/user_list.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 현재 로그인한 사용자를 제외한 모든 사용자
        if self.request.user.is_authenticated:
            users = User.objects.exclude(id=self.request.user.id).order_by('-created_at')
        else:
            users = User.objects.all().order_by('-created_at')
        
        context['users'] = users
        return context