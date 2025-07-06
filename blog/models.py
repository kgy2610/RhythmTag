# blog/models.py

from django.db import models
from django.urls import reverse
from django.conf import settings
from ckeditor_uploader.fields import RichTextUploadingField

class Blog(models.Model):
    # 사용자당 하나의 블로그
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blog'
    )
    blog_name = models.CharField(max_length=200, verbose_name='블로그 이름')
    blog_description = models.TextField(blank=True, verbose_name='블로그 설명')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.blog_name
    
    class Meta:
        verbose_name = '블로그'
        verbose_name_plural = '블로그'

class Tag(models.Model):
    # 태그 정보
    name = models.CharField(max_length=50, unique=True, verbose_name='태그 이름')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"#{self.name}"
    
    class Meta:
        verbose_name = '태그'
        verbose_name_plural = '태그'

class Post(models.Model):
    # 게시글
    STATUS_CHOICES = [
        ('draft', '임시저장'),
        ('published', '발행'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='제목')
    content = RichTextUploadingField(verbose_name='내용')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, verbose_name='블로그')
    link = models.URLField(blank=True, verbose_name='유튜브 링크')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published', verbose_name='상태')
    tags = models.ManyToManyField(Tag, through='PostTag', blank=True, verbose_name='태그')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('post_detail', args=[str(self.pk)])
    
    @property
    def youtube_thumbnail_url(self):
        if self.link and ('youtube.com' in self.link or 'youtu.be' in self.link):
            # YouTube URL에서 video ID 추출
            if 'youtube.com/watch?v=' in self.link:
                video_id = self.link.split('watch?v=')[1].split('&')[0]
            elif 'youtu.be/' in self.link:
                video_id = self.link.split('youtu.be/')[1].split('?')[0]
            else:
                return None
            return f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
        return None
    
    @property
    def like_count(self):
        return self.likes.count()
    
    @property
    def view_count(self):
        # view_count 필드가 없으므로 property로 처리하거나 필드 추가 필요
        return getattr(self, '_view_count', 0)
    
    class Meta:
        verbose_name = '게시글'
        verbose_name_plural = '게시글'
        ordering = ['-created_at']

class PostTag(models.Model):
    # 게시글-태그 연결(최대 5개 제한)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['post', 'tag']
        verbose_name = '게시글 태그'
        verbose_name_plural = '게시글 태그'

class Like(models.Model):
    # 좋아요 (사용자당 게시글당 1개만)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # User → settings.AUTH_USER_MODEL로 변경
        on_delete=models.CASCADE, 
        verbose_name='사용자'
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes', verbose_name='게시글')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
        verbose_name = '좋아요'
        verbose_name_plural = '좋아요'

class Follow(models.Model):
    # 팔로우 관계
    following_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # User → settings.AUTH_USER_MODEL로 변경
        on_delete=models.CASCADE, 
        related_name='following', 
        verbose_name='팔로우하는 사용자'
    )
    followed_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # User → settings.AUTH_USER_MODEL로 변경
        on_delete=models.CASCADE, 
        related_name='followers', 
        verbose_name='팔로우당하는 사용자'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['following_user', 'followed_user']
        verbose_name = '팔로우'
        verbose_name_plural = '팔로우'

class Comment(models.Model):
    # 댓글
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='게시글')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # User → settings.AUTH_USER_MODEL로 변경
        on_delete=models.CASCADE, 
        verbose_name='작성자'
    )
    comment = models.TextField(verbose_name='댓글 내용')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.nickname}: {self.comment[:30]}..."  # username → nickname으로 변경
    
    class Meta:
        verbose_name = '댓글'
        verbose_name_plural = '댓글'
        ordering = ['created_at']