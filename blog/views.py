# blog/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Post, Blog, Tag, PostTag
from .forms import PostForm
from django.db.models import Q


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
        # 폼이 유효하지 않을 때
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': '입력한 내용을 확인해주세요.',
                'errors': form.errors
            }, status=400)
        return super().form_invalid(form)


class PostListView(ListView):
    # 게시글 목록 뷰
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 필터링 옵션 처리
        filter_option = self.request.GET.get('filter', 'my')
        
        if filter_option == 'my' and self.request.user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)
        elif filter_option == 'follow' and self.request.user.is_authenticated:
            # 팔로우/팔로잉 로직 구현 필요
            pass
        elif filter_option == 'famous':
            queryset = queryset.order_by('-like_count')
        
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
        
        if self.request.user.is_authenticated:
            try:
                context['user_blog'] = Blog.objects.get(user=self.request.user)
                context['user_has_blog'] = True
            except Blog.DoesNotExist:
                context['user_has_blog'] = False
        else:
            context['user_has_blog'] = False
            
        return context


class PostDetailView(DetailView):
    # 게시글 상세 뷰
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 조회수 증가
        self.object.view_count += 1
        self.object.save()
        
        # 좋아요 여부 확인
        if self.request.user.is_authenticated:
            context['user_liked'] = self.object.likes.filter(user=self.request.user).exists()
        
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
    template_name = 'blog/post_confirm_delete.html'
    success_url = reverse_lazy('post_list')
    
    def get_queryset(self):
        # 자신의 글만 삭제 가능
        return super().get_queryset().filter(user=self.request.user)


class BlogCreateView(LoginRequiredMixin, CreateView):
    # 블로그 생성 뷰
    model = Blog
    fields = ['blog_name', 'description']
    template_name = 'blog/blog_create.html'
    success_url = reverse_lazy('post_list')
    
    def form_valid(self, form):
        # 이미 블로그가 있는지 확인
        if Blog.objects.filter(user=self.request.user).exists():
            messages.error(self.request, '이미 블로그를 보유하고 있습니다.')
            return redirect('post_list')
        
        form.instance.user = self.request.user
        return super().form_valid(form)