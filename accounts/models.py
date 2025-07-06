# accounts/models.py

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, nickname, password=None, **extra_fields):
        if not nickname:
            raise ValueError('닉네임은 필수 항목입니다.')
        
        user = self.model(nickname=nickname, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, nickname, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(nickname, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # 기본 필드
    nickname = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name='닉네임',
        help_text='다른 사용자와 중복되지 않는 닉네임을 입력하세요.'
    )
    name = models.CharField(
        max_length=100, 
        verbose_name='이름'
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name='전화번호'
    )
    
    # 권한 관련 필드
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # 타임스탬프
    created_at = models.DateTimeField(default=timezone.now, verbose_name='가입일')
    
    objects = UserManager()
    
    # nickname을 username 필드로 사용
    USERNAME_FIELD = 'nickname'
    REQUIRED_FIELDS = ['name']  # createsuperuser 명령 시 필요한 필드
    
    class Meta:
        db_table = 'user'
        verbose_name = '사용자'
        verbose_name_plural = '사용자들'
    
    def __str__(self):
        return self.nickname
    
    def get_full_name(self):
        return self.name
    
    def get_short_name(self):
        return self.nickname