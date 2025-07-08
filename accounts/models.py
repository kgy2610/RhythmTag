# accounts/models.py

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, userid, password=None, **extra_fields):
        if not userid:
            raise ValueError('아이디는 필수 항목입니다.')
        
        user = self.model(userid=userid, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, userid, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(userid, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # 기본 필드
    userid = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='아이디',
        help_text='로그인할 때 사용할 아이디를 입력하세요.'
    )
    nickname = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='닉네임',
        help_text='사용할 닉네임을 입력하세요.'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='이름',
        help_text='이름을 입력하세요.'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='전화번호',
        help_text='전화번호를 입력하세요.'
    )
    
    # 권한 관련 필드
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # 가입일
    created_at = models.DateTimeField(default=timezone.now, verbose_name='가입일')
    
    objects = UserManager()
    
    USERNAME_FIELD = 'userid'
    REQUIRED_FIELDS = ['nickname', 'name']
    
    class Meta:
        db_table = 'user'
        verbose_name = '사용자'
        verbose_name_plural = '사용자들'
    
    def __str__(self):
        return f'{self.userid} ({self.nickname})'
    
    def get_full_name(self):
        return self.name
    
    def get_short_name(self):
        return self.nickname
    
    # 팔로우 관련 메서드들
    def follow(self, user):
        """다른 사용자를 팔로우"""
        if self != user:  # 자기 자신은 팔로우 불가
            Follow.objects.get_or_create(follower=self, following=user)
    
    def unfollow(self, user):
        """팔로우 취소"""
        Follow.objects.filter(follower=self, following=user).delete()
    
    def is_following(self, user):
        """특정 사용자를 팔로우하고 있는지 확인"""
        if self.is_authenticated and user != self:
            return Follow.objects.filter(follower=self, following=user).exists()
        return False
    
    @property
    def followers_count(self):
        """나를 팔로우하는 사람 수"""
        return self.followers.count()
    
    @property
    def following_count(self):
        """내가 팔로우하는 사람 수"""
        return self.following.count()
    
    def get_following_users(self):
        """내가 팔로우하는 사용자들"""
        return User.objects.filter(followers__follower=self)
    
    def get_followers_users(self):
        """나를 팔로우하는 사용자들"""
        return User.objects.filter(following__following=self)


class Follow(models.Model):
    # 팔로우를 하는 사람 (팔로워)
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following',  # 내가 팔로우하는 사람들
        verbose_name='팔로워'
    )

    # 팔로우를 받는 사람 (팔로잉)
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers',  # 나를 팔로우하는 사람들
        verbose_name='팔로잉'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='팔로우 시간')

    class Meta:
        unique_together = ('follower', 'following')  # 중복 팔로우 방지
        verbose_name = '팔로우'
        verbose_name_plural = '팔로우'

    def __str__(self):
        return f'{self.follower.nickname} → {self.following.nickname}'