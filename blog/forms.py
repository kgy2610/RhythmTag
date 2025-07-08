# blog/forms.py

from django import forms
from .models import Post, Tag, PostTag
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError

User = get_user_model()

class PostForm(forms.ModelForm):
    tag_input = forms.CharField(
        max_length=200,
        required=False,
        help_text='태그를 입력하세요 (예: #음악 #힙합) 최대 5개',
        widget=forms.TextInput(attrs={
            'placeholder': '#태그1 #태그2 #태그3',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'link']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '제목을 입력하세요'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': '내용을 입력하세요'
            }),
            'link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': '링크를 입력하세요'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 수정 시 기존 태그를 불러와서 표시
        if self.instance.pk:
            tag_names = ['#' + tag.name for tag in self.instance.tags.all()]
            self.fields['tag_input'].initial = ' '.join(tag_names)
    
    def clean_tag_input(self):
        tag_input = self.cleaned_data.get('tag_input', '')
        tags = [tag.strip().lstrip('#') for tag in tag_input.split() if tag.strip()]
        
        # 태그 개수 제한 (최대 5개)
        if len(tags) > 5:
            raise forms.ValidationError('태그는 최대 5개까지만 입력할 수 있습니다.')
        
        return tags

    @transaction.atomic  # 추가: 트랜잭션 보장
    def save(self, commit=True):
        print("=== PostForm.save() 호출 ===")  # 추가: 디버깅 로그
        
        instance = super().save(commit=commit)
        print(f"게시글 저장됨: {instance}")  # 추가
        
        if commit:
            try:
                # 수정: through 모델 사용 시 직접 PostTag 테이블 조작
                PostTag.objects.filter(post=instance).delete()
                print("기존 태그 연결 삭제 완료")  # 추가
                
                # 새 태그 추가
                tags = self.cleaned_data.get('tag_input', [])
                print(f"처리할 태그들: {tags}")  # 추가
                
                for tag_name in tags:
                    if tag_name:  # 추가: 빈 태그명 제외
                        tag, created = Tag.objects.get_or_create(name=tag_name)
                        PostTag.objects.create(post=instance, tag=tag)
                        print(f"태그 연결 완료: {tag.name}")  # 추가
                
                print("모든 태그 처리 완료")  # 추가
                
            except Exception as e:
                print(f"태그 처리 중 오류: {e}")  # 추가
                raise  # 오류를 다시 발생시켜서 트랜잭션 롤백
        
        return instance
    
    def form_invalid(self, form):
        print(f"Form errors: {form.errors}")
        print(f"Form data: {form.data}")
        for field, errors in form.errors.items():
            print(f"Field '{field}': {errors}")
        messages.error(self.request, f'폼 오류: {form.errors}')
        return super().form_invalid(form)
    


class AccountDeleteForm(forms.Form):
    # 회원 탈퇴 폼
    
    password = forms.CharField(
        label='현재 비밀번호',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '계정 확인을 위해 현재 비밀번호를 입력하세요'
        })
    )
    
    confirm_delete = forms.BooleanField(
        label='위 내용을 모두 확인했으며, 회원 탈퇴에 동의합니다.',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_password(self):
        # 비밀번호 검증
        password = self.cleaned_data.get('password')
        
        if not password:
            raise forms.ValidationError('비밀번호를 입력해주세요.')
        
        if not self.user.check_password(password):
            raise forms.ValidationError('현재 비밀번호가 올바르지 않습니다.')
        
        return password
    
    def clean_confirm_delete(self):
        # 삭제 확인 체크박스 검증 
        confirm = self.cleaned_data.get('confirm_delete')
        
        if not confirm:
            raise forms.ValidationError('회원 탈퇴에 동의해주세요.')
        
        return confirm



# 비밀번호 번경 폼 커스텀
class CustomPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label='현재 비밀번호',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '현재 비밀번호를 입력하세요'
        })
    )
    
    new_password1 = forms.CharField(
        label='새 비밀번호',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '새 비밀번호를 입력하세요'
        })
    )
    
    new_password2 = forms.CharField(
        label='새 비밀번호 확인',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '새 비밀번호를 다시 입력하세요'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_old_password(self):
        # 현재 비밀번호 검증
        old_password = self.cleaned_data.get('old_password')
        
        if not old_password:
            raise ValidationError('현재 비밀번호를 입력해주세요.')
        
        if not self.user.check_password(old_password):
            raise ValidationError('현재 비밀번호가 올바르지 않습니다. 다시 입력해주세요.')
        
        return old_password
    
    def clean_new_password1(self):
        # 새 비밀번호 검증
        password1 = self.cleaned_data.get('new_password1')
        
        if not password1:
            raise ValidationError('새 비밀번호를 입력해주세요.')
        
        # 길이 검사
        if len(password1) < 8:
            raise ValidationError('비밀번호는 최소 8자 이상이어야 합니다.')
        
        # 최대 길이 검사
        if len(password1) > 128:
            raise ValidationError('비밀번호는 128자를 초과할 수 없습니다.')
        
        # 숫자만으로 구성 검사
        if password1.isdigit():
            raise ValidationError('비밀번호는 숫자만으로 구성할 수 없습니다.')
        
        # 너무 간단한 비밀번호 검사
        common_passwords = [
            'password', '12345678', 'qwerty', 'abc123', 'abcdefg',
            'password123', '11111111', '00000000', '123456789',
            'qwerty123', 'admin', 'test', 'user', '1234', '123123'
        ]
        if password1.lower() in common_passwords:
            raise ValidationError('너무 간단한 비밀번호입니다. 더 복잡한 비밀번호를 사용해주세요.')
        
        # 연속된 문자 검사
        if any(password1.lower().find(seq) != -1 for seq in ['123', 'abc', 'qwe', 'asd']):
            raise ValidationError('연속된 문자나 숫자는 사용할 수 없습니다.')
        
        # 사용자 정보와 유사한지 검사
        if hasattr(self.user, 'userid') and self.user.userid and self.user.userid.lower() in password1.lower():
            raise ValidationError('비밀번호에 사용자 아이디가 포함될 수 없습니다.')
        
        if hasattr(self.user, 'nickname') and self.user.nickname and self.user.nickname.lower() in password1.lower():
            raise ValidationError('비밀번호에 닉네임이 포함될 수 없습니다.')
        
        # 현재 비밀번호와 동일한지 검사
        old_password = self.cleaned_data.get('old_password')
        if old_password and password1 == old_password:
            raise ValidationError('새 비밀번호는 현재 비밀번호와 달라야 합니다.')
        
        return password1
    
    def clean_new_password2(self):
        # "새 비밀번호 확인 검증
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if not password2:
            raise ValidationError('비밀번호 확인을 입력해주세요.')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('두 비밀번호가 일치하지 않습니다. 다시 확인해주세요.')
        
        return password2
    
    def clean(self):
        # 전체 폼 검증
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        # 최종 비밀번호 일치 확인
        if password1 and password2 and password1 != password2:
            raise ValidationError('새 비밀번호와 비밀번호 확인이 일치하지 않습니다.')
        
        return cleaned_data
    
    def save(self):
        # 비밀번호 저장
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()
        return self.user