# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    name = forms.CharField(
        max_length=100, 
        label='이름',
        widget=forms.TextInput(attrs={
            'placeholder': '실명을 입력하세요'
        })
    )
    email = forms.EmailField(
        label='이메일',
        widget=forms.EmailInput(attrs={
            'placeholder': '이메일을 입력하세요'
        })
    )
    phone = forms.CharField(
        max_length=15, 
        label='전화번호', 
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '전화번호를 입력하세요 (선택)'
        })
    )
    nickname = forms.CharField(
        max_length=50, 
        label='아이디(닉네임)',
        widget=forms.TextInput(attrs={
            'placeholder': '사용할 아이디를 입력하세요'
        })
    )
    password1 = forms.CharField(
        label='비밀번호',
        widget=forms.PasswordInput(attrs={
            'placeholder': '비밀번호를 입력하세요'
        })
    )
    password2 = forms.CharField(
        label='비밀번호 확인',
        widget=forms.PasswordInput(attrs={
            'placeholder': '비밀번호를 다시 입력하세요'
        })
    )
    
    class Meta:
        model = User
        fields = ('nickname', 'name', 'email', 'phone', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('이미 등록된 이메일입니다.')
        return email
    
    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        if User.objects.filter(username=nickname).exists():
            raise forms.ValidationError('이미 존재하는 아이디입니다.')
        return nickname
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['nickname']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['name']
        
        if commit:
            user.save()
        return user

# 로그인 폼 - 템플릿의 form.id에 맞춰서 필드명을 id로 설정
class CustomAuthenticationForm(forms.Form):
    id = forms.CharField(  # 템플릿에서 form.id를 사용하므로 필드명을 id로 설정
        label='아이디',
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': '아이디를 입력하세요'
        })
    )
    password = forms.CharField(
        label='비밀번호',
        widget=forms.PasswordInput(attrs={
            'placeholder': '비밀번호를 입력하세요'
        })
    )