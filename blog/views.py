# blog/views.py

from django.shortcuts import render, redirect
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import logout
from django.urls import reverse_lazy
from .models import Post, Blog
from .forms import PostForm
from django.db.models import Q
from django.contrib import messages
from django.views import View
from django.http import JsonResponse


class PostWriteView(CreateView):
    # 글 작성 뷰 - 로그인하지 않은 사용자도 폼은 볼 수 있음
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'  # 템플릿 경로 수정
    success_url = reverse_lazy('post_list')
    
    def form_valid(self, form):
        # 폼이 유효할 때 - 여기서 로그인 체크
        # 로그인하지 않은 경우
        if not self.request.user.is_authenticated:
            # AJAX 요청인 경우
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': '로그인이 필요합니다.',
                    'redirect_url': reverse_lazy('login')
                }, status=401)
            # 일반 POST 요청인 경우
            else:
                messages.error(self.request, '로그인이 필요합니다.')
                return redirect('login')
        
        # 로그인한 사용자의 경우
        form.instance.user = self.request.user
        
        # 사용자의 블로그 확인
        try:
            blog = Blog.objects.get(user=self.request.user)
            form.instance.blog = blog
        except Blog.DoesNotExist:
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': '블로그를 먼저 생성해주세요.',
                    'redirect_url': reverse_lazy('blog_create')
                }, status=400)
            else:
                messages.error(self.request, '블로그를 먼저 생성해주세요.')
                return redirect('blog_create')
        
        # 글 저장 (태그는 form.save()에서 자동으로 처리됨)
        response = super().form_valid(form)
        
        # AJAX 요청인 경우
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': '글이 성공적으로 작성되었습니다.',
                'redirect_url': reverse_lazy('post_detail', kwargs={'pk': self.object.pk})
            })
        
        return response
    
    def form_invalid(self, form):
        print(f"폼 유효성 검사 실패: {form.errors}")  # 추가
        print(f"폼 데이터: {form.data}")  # 추가
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': '입력한 내용을 확인해주세요.',
                'errors': form.errors
            }, status=400)
        return super().form_invalid(form)


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

class PostWriteView(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    success_url = reverse_lazy('post_list')
    
    def form_valid(self, form):
        # 로그인 체크
        if not self.request.user.is_authenticated:
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': '로그인이 필요합니다.',
                    'redirect_url': reverse_lazy('login')
                }, status=401)
            else:
                messages.error(self.request, '로그인이 필요합니다.')
                return redirect('login')
        
        # 사용자 설정
        form.instance.user = self.request.user
        
        # 블로그 확인 및 설정
        try:
            blog = Blog.objects.get(user=self.request.user)
            form.instance.blog = blog
        except Blog.DoesNotExist:
            messages.error(self.request, '블로그를 먼저 생성해주세요.')
            return redirect('blog_create')
        
        # 저장
        response = super().form_valid(form)
        messages.success(self.request, '글이 성공적으로 작성되었습니다.')
        return response
    
    def form_invalid(self, form):
        # 폼 에러 출력
        print(f"Form errors: {form.errors}")  # 디버깅용
        messages.error(self.request, '입력 내용을 확인해주세요.')
        return super().form_invalid(form)

class PostDetailView(DetailView):
    # 게시글 상세 뷰
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


class PostDeleteView(LoginRequiredMixin, DeleteView):
    # 게시글 삭제 뷰
    model = Post
    template_name = 'blog/post_delete.html'
    success_url = reverse_lazy('post_list')
    
    def get_queryset(self):
        # 자신의 글만 삭제 가능
        return super().get_queryset().filter(user=self.request.user)


class BlogCreateView(CreateView):  # 수정: LoginRequiredMixin 제거
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
    

class UserProfileView(LoginRequiredMixin, TemplateView):
    # 사용자 정보 페이지
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