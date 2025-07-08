# blog/views.py

# Django 기본 모듈
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, TemplateView
from django.views import View
from django.contrib.auth import logout, update_session_auth_hash, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from .forms import CustomPasswordChangeForm, AccountDeleteForm

User = get_user_model()

# 로컬 모듈
from .models import Post, Blog
from .forms import PostForm

# 게시글 작성
class PostWriteView(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    success_url = reverse_lazy('post_list')
    
    def form_valid(self, form):
        # 로그인 확인
        if not self.request.user.is_authenticated:
            messages.error(self.request, '로그인이 필요합니다.')
            return redirect('login')
        
        # 사용자 설정
        form.instance.user = self.request.user
        
        # 블로그 확인 및 자동 생성
        try:
            blog = Blog.objects.get(user=self.request.user)
        except Blog.DoesNotExist:
            # 블로그가 없으면 자동으로 생성
            blog = Blog.objects.create(
                user=self.request.user,
                title=f"{self.request.user.nickname}의 블로그",
                blog_description="내 블로그입니다."
            )
            messages.info(self.request, '블로그가 자동으로 생성되었습니다.')
        
        form.instance.blog = blog
        
        # 저장
        try:
            response = super().form_valid(form)
            messages.success(self.request, '글이 성공적으로 작성되었습니다.')
            return response
        except Exception as e:
            print(f"저장 오류: {e}")  # 디버깅용
            messages.error(self.request, '저장 중 오류가 발생했습니다.')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        print(f"폼 오류: {form.errors}")  # 디버깅용
        messages.error(self.request, '입력 내용을 확인해주세요.')
        return super().form_invalid(form)


# 게시글 목록
class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 필터링 옵션 처리
        filter_option = self.request.GET.get('filter', 'all')  # 기본값을 'all'로 변경
        
        if filter_option == 'my' and self.request.user.is_authenticated:
            # "내가 작성한 글" 탭 - 로그인한 사용자의 글만 필터링
            queryset = queryset.filter(user=self.request.user)
        elif filter_option == 'follow' and self.request.user.is_authenticated:
            # "팔로워/팔로잉 글" 탭 (추후 구현)
            pass
        elif filter_option == 'famous':
            # "인기가 많은 글" 탭
            queryset = queryset.order_by('-like_count')
        # filter_option == 'all'이면 모든 글 표시 (기본값)
        
        # 검색 기능
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(tags__name__icontains=search_query)
            ).distinct()
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 현재 필터 옵션
        context['current_filter'] = self.request.GET.get('filter', 'all')
        
        # 로그인한 사용자의 블로그 확인
        context['user_has_blog'] = False
        context['user_blog'] = None
        context['blog_name'] = '#블로그가 없습니다'  # 기본값
        
        if self.request.user.is_authenticated:
            try:
                user_blog = Blog.objects.get(user=self.request.user)
                context['user_blog'] = user_blog
                context['user_has_blog'] = True
                context['blog_name'] = f'#{user_blog.blog_name}'  # 수정: 사용자 블로그 이름 사용
            except Blog.DoesNotExist:
                context['user_has_blog'] = False
                context['blog_name'] = '#블로그가 없습니다'  # 블로그가 없을 때 기본값
                
        return context

# 게시글 상세
class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    #조회수 증가
    def get_object(self, queryset=None):
        # 게시글을 가져오면서 조회수를 증가
        # get_object를 통해 한 번만 실행되도록 보장, 중복 조회수 증가를 방지함
        post = super().get_object(queryset)
        session_key = f'post_view_{post.pk}'
        if not self.request.session.get(session_key, False):
            if hasattr(post, 'view_count'):
                post.view_count += 1
                post.save(update_fields=['view_count'])
                self.request.session[session_key] = True
            else:
                print("view_count 필드가 없습니다. 마이그레이션을 실행해주세요.")
        
        return post
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 좋아요 여부 확인
        if self.request.user.is_authenticated:
            context['user_liked'] = self.object.likes.filter(user=self.request.user).exists()
        
        # 디버깅용 로그
        print(f"게시글 조회: {self.object.title}")
        print(f"현재 조회수: {getattr(self.object, 'view_count', '필드 없음')}")

        return context

# 게시글 수정
class PostUpdateView(LoginRequiredMixin, UpdateView):
    # 게시글 수정 뷰
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'  # 템플릿 경로 수정
    
    def get_queryset(self):
        # 자신의 글만 수정 가능
        return super().get_queryset().filter(user=self.request.user)
    
    def form_valid(self, form):
        # 태그 업데이트는 form.save()에서 자동으로 처리됨
        return super().form_valid(form)


# 게시글 삭제
class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/post_delete.html'
    success_url = reverse_lazy('post_list')
    
    def get_queryset(self):
        # 자신의 글만 삭제 가능
        return super().get_queryset().filter(user=self.request.user)


# 블로그 생성
class BlogCreateView(CreateView):
    model = Blog
    fields = ['blog_name', 'blog_description']
    template_name = 'blog/blog_create.html'
    success_url = reverse_lazy('post_list')
    
    def dispatch(self, request, *args, **kwargs):
        # 로그인하지 않은 사용자도 GET 요청(페이지 보기)은 허용
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # POST 요청 시에만 로그인 체크
        if not self.request.user.is_authenticated:
            messages.warning(self.request, '로그인 후 이용해주세요.')
            return redirect('login')
        
        # 이미 블로그가 있는지 확인
        if Blog.objects.filter(user=self.request.user).exists():
            messages.error(self.request, '이미 블로그를 보유하고 있습니다.')
            return redirect('post_list')
        
        form.instance.user = self.request.user
        messages.success(self.request, f'"{form.instance.blog_name}" 블로그가 생성되었습니다!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 로그인하지 않은 사용자에게도 폼을 보여주기 위한 컨텍스트
        context['show_login_message'] = not self.request.user.is_authenticated
        return context
    

# 사용자 정보 페이지
class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_posts'] = Post.objects.filter(user=self.request.user).order_by('-created_at')[:5]
        context['total_posts'] = Post.objects.filter(user=self.request.user).count()
        return context
    
class LogoutView(View):
    def post(self, request):
        logout(request)
        messages.success(request, '로그아웃되었습니다.')
        return redirect('post_list')
    
    def get(self, request):
        logout(request)
        messages.success(request, '로그아웃되었습니다.')
        return redirect('post_list')
    

# 블로그 정보 수정
class BlogUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Blog
    fields = ['blog_name', 'blog_description']
    template_name = 'blog/blog_update.html'

    def test_func(self):
        # 본인의 글만 수정
        blog = self.get_object()
        return self.request.user == blog.user
    
    def get_object(self, queryset=None):
        # 현재 사용자의 블로그 가져오기
        return get_object_or_404(Blog, user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, '블로그 정보가 성공적으로 수정되었습니다.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('user_profile')
    

# 블로그 삭제
class BlogDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Blog
    template_name = 'blog/blog_delete.html'
    success_url = reverse_lazy('post_list')
    
    def test_func(self):
        # 본인 블로그만 삭제 가능하도록 확인
        blog = self.get_object()
        return self.request.user == blog.user
    
    def get_object(self, queryset=None):
        #현재 사용자의 블로그 가져오기
        return get_object_or_404(Blog, user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        # 삭제 처리
        blog = self.get_object()
        
        # 블로그와 연관된 게시글도 함께 삭제 (CASCADE 설정되어 있으면 자동)
        post_count = Post.objects.filter(blog=blog).count()
        
        # 삭제 실행
        blog.delete()
        
        messages.success(
            request, 
            f'블로그와 {post_count}개의 게시글이 모두 삭제되었습니다.'
        )
        return redirect(self.success_url)
    
# 프로필 수정
class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    # 프로필 정보 수정 뷰
    model = User
    template_name = 'accounts/profile_update.html'
    success_url = reverse_lazy('user_profile')
    
    # 수정 가능한 필드들 (실제 User 모델에 맞게 조정)
    fields = ['nickname', 'name', 'phone']
    
    def get_object(self, queryset=None):
        # 현재 로그인한 사용자 반환
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, '프로필이 성공적으로 수정되었습니다.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, '입력 정보를 확인해주세요.')
        return super().form_invalid(form)

# 비밀번호 변경
class PasswordChangeView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile_password_update.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CustomPasswordChangeForm(user=self.request.user)
        return context
    
    def post(self, request, *args, **kwargs):
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        
        if form.is_valid():
            print("=== 비밀번호 변경 성공 ===")
            
            try:
                # 비밀번호 저장
                user = form.save()
                
                # 비밀번호 변경 후 세션 유지 (자동 로그아웃 방지)
                update_session_auth_hash(request, user)
                
                print(f"사용자 {user.userid}의 비밀번호가 변경되었습니다.")
                messages.success(request, '🎉 비밀번호가 성공적으로 변경되었습니다!')
                return redirect('user_profile')
                
            except Exception as e:
                print(f"비밀번호 저장 중 오류: {e}")
                messages.error(request, '비밀번호 저장 중 오류가 발생했습니다. 다시 시도해주세요.')
                
        else:
            print("=== 비밀번호 변경 실패 ===")
            print(f"폼 오류: {form.errors}")
            
            # 각 필드별 오류 메시지를 수집
            all_errors = []
            for field, errors in form.errors.items():
                for error in errors:
                    all_errors.append(f"• {error}")
            
            if all_errors:
                error_message = "다음 문제를 해결해주세요:\n" + "\n".join(all_errors)
                messages.error(request, error_message)
            else:
                messages.error(request, '비밀번호 변경에 실패했습니다. 입력 정보를 확인해주세요.')
        
        # 오류가 있는 폼과 함께 템플릿 렌더링
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)

# 회원 탈퇴
class AccountDeleteView(LoginRequiredMixin, TemplateView):
    """회원 탈퇴 뷰"""
    template_name = 'accounts/profile_delete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AccountDeleteForm(user=self.request.user)
        
        # 사용자 관련 통계 정보 추가
        user = self.request.user
        context['blog_count'] = Blog.objects.filter(user=user).count()
        context['post_count'] = Post.objects.filter(user=user).count()
        
        # 좋아요 수 계산
        try:
            from .models import Like
            context['like_count'] = Like.objects.filter(user=user).count()
        except:
            context['like_count'] = 0
        
        return context
    
    def post(self, request, *args, **kwargs):
        """회원 탈퇴 처리"""
        form = AccountDeleteForm(user=request.user, data=request.POST)
        
        if form.is_valid():
            user = request.user
            userid = user.userid
            
            print(f"=== 회원 탈퇴 진행: {userid} ===")
            
            try:
                # 삭제될 데이터 정보 수집
                blog_count = Blog.objects.filter(user=user).count()
                post_count = Post.objects.filter(user=user).count()
                
                print(f"삭제될 데이터 - 블로그: {blog_count}개, 게시글: {post_count}개")
                
                # 사용자 삭제 (CASCADE로 연관 데이터도 함께 삭제)
                user.delete()
                
                print(f"{userid} 계정 삭제 완료")
                
                # 성공 메시지와 함께 메인페이지로 리다이렉트
                messages.success(
                    request, 
                    f'👋 {userid}님의 계정이 삭제되었습니다. '
                    f'블로그 {blog_count}개, 게시글 {post_count}개가 함께 삭제되었습니다. '
                    f'그동안 이용해 주셔서 감사했습니다.'
                )
                
                # 로그아웃 처리
                logout(request)
                
                # 메인페이지로 리다이렉트
                return redirect('/')
                
            except Exception as e:
                print(f"회원 탈퇴 처리 중 오류: {e}")
                messages.error(request, '❌ 회원탈퇴 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.')
        
        else:
            print("폼 검증 실패:")
            print(f"폼 오류: {form.errors}")
            messages.error(request, '입력 정보를 확인해주세요.')
        
        # 오류가 있는 경우 폼과 함께 템플릿 렌더링
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)