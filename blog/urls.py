# blog/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # 게시글 관련
    path('', views.PostListView.as_view(), name='post_list'), # 게시글 리스트
    path('post/write/', views.PostWriteView.as_view(), name='post_write'), # 게시글 작성
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'), # 게시글 세부내용
    path('post/<int:pk>/update/', views.PostUpdateView.as_view(), name='post_update'), # 게시글 수정
    path('post/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'), # 게시글 삭제
    path('post/<int:post_id>/like/', views.toggle_like, name='toggle_like'), # 좋아요
    path('generate-ai-blog/', views.generate_ai_blog, name='generate_ai_blog'), # AI 글 생성
    
    # 블로그 관련
    path('create/', views.BlogCreateView.as_view(), name='blog_create'), # 블로그 생성
    path('update/', views.BlogUpdateView.as_view(), name='blog_update'), # 블로그 정보 수정
    path('delete/', views.BlogDeleteView.as_view(), name='blog_delete'), # 블로그 삭제

    # 댓글 관련
    path('post/<int:pk>/comment/', views.add_comment, name='add_comment'), # 댓글
    path('comment/<int:pk>/edit/', views.edit_comment, name='edit_comment'), # 댓글 수정
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'), # 댓글 삭제
]