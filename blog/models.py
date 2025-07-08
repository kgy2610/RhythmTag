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

    @classmethod
    def user_has_blog(cls, user):
        """사용자가 블로그를 가지고 있는지 확인"""
        return cls.objects.filter(user=user).exists()
    
    @classmethod
    def get_user_blog(cls, user):
        """사용자의 블로그 반환"""
        try:
            return cls.objects.get(user=user)
        except cls.DoesNotExist:
            return None


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
    title = models.CharField(max_length=200, verbose_name='제목')
    content = RichTextUploadingField(verbose_name='내용')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, verbose_name='블로그')
    link = models.URLField(blank=True, verbose_name='유튜브 링크')
    tags = models.ManyToManyField(Tag, through='PostTag', blank=True, verbose_name='태그')
    view_count = models.PositiveIntegerField(default=0, verbose_name='조회수')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('post_detail', args=[str(self.pk)])
    
    @property
    def youtube_thumbnail_url(self):
        """YouTube 썸네일 URL 생성"""
        if self.link and ('youtube.com' in self.link or 'youtu.be' in self.link):
            if 'youtube.com/watch?v=' in self.link:
                video_id = self.link.split('watch?v=')[1].split('&')[0]
            elif 'youtu.be/' in self.link:
                video_id = self.link.split('youtu.be/')[1].split('?')[0]
            else:
                return None
            return f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
        return None
    
    @property
    def youtube_embed_url(self):
        """YouTube 임베드 URL 생성"""
        if self.link and ('youtube.com' in self.link or 'youtu.be' in self.link):
            if 'youtube.com/watch?v=' in self.link:
                video_id = self.link.split('watch?v=')[1].split('&')[0]
            elif 'youtu.be/' in self.link:
                video_id = self.link.split('youtu.be/')[1].split('?')[0]
            else:
                return None
            return f'https://www.youtube.com/embed/{video_id}'
        return None
    
    @property
    def like_count(self):
        """좋아요 개수"""
        return self.likes.count()

    def is_liked_by(self, user):
        """사용자가 좋아요를 눌렀는지 확인"""
        if user.is_authenticated:
            return self.likes.filter(user=user).exists()
        return False
    
    def increment_view_count(self):
        """조회수 증가"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    class Meta:
        verbose_name = '게시글'
        verbose_name_plural = '게시글'
        ordering = ['-created_at']


class PostTag(models.Model):
    # 게시글-태그 연결 (중간 테이블)
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
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='사용자'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='게시글'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='좋아요 누른 시간')
    
    class Meta:
        unique_together = ('user', 'post')  # 한 사용자가 같은 게시글에 중복 좋아요 방지
        verbose_name = '좋아요'
        verbose_name_plural = '좋아요'
    
    def __str__(self):
        return f'{self.user.nickname} - {self.post.title}'


class Comment(models.Model):
    # 댓글
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='게시글')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='작성자'
    )
    comment = models.TextField(verbose_name='댓글 내용')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.nickname}: {self.comment[:30]}..."
    
    class Meta:
        verbose_name = '댓글'
        verbose_name_plural = '댓글'
        ordering = ['created_at']