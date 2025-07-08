# accounts/forms.py

from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError

User = get_user_model()

# 로그인 폼
from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

class CustomAuthenticationForm(forms.Form):
    userid = forms.CharField(
        label='아이디',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '아이디를 입력하세요'
        })
    )
    
    password = forms.CharField(
        label='비밀번호',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '비밀번호를 입력하세요'
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        userid = self.cleaned_data.get('userid')
        password = self.cleaned_data.get('password')

        if userid and password:
            self.user_cache = authenticate(
                request=self.request,
                userid=userid,  # 직접 userid 사용
                password=password
            )
            if self.user_cache is None:
                raise ValidationError('아이디 또는 비밀번호가 올바르지 않습니다.')
            if not self.user_cache.is_active:
                raise ValidationError('이 계정은 비활성화되었습니다.')

        return self.cleaned_data

    def get_user(self):
        return self.user_cache

# 회원가입 폼
class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='비밀번호', widget=forms.PasswordInput)
    password2 = forms.CharField(label='비밀번호 확인', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['userid', 'nickname', 'name', 'phone']

    # 비밀번호 검증 메서드
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        
        if not password1:
            raise forms.ValidationError('비밀번호를 입력해주세요.')
        
        # 길이 검사
        if len(password1) < 8:
            raise forms.ValidationError('비밀번호는 최소 8자 이상이어야 합니다.')
        
        # 최대 길이 검사
        if len(password1) > 128:
            raise forms.ValidationError('비밀번호는 128자를 초과할 수 없습니다.')
        
        # 숫자만으로 구성 검사
        if password1.isdigit():
            raise forms.ValidationError('비밀번호는 숫자만으로 구성할 수 없습니다.')
        
        # 너무 간단한 비밀번호 검사
        common_passwords = [
            'password', '12345678', 'qwerty', 'abc123', 'abcdefg',
            'password123', '11111111', '00000000', '123456789',
            'qwerty123', 'admin', 'test', 'user', '1234', '123123'
        ]
        if password1.lower() in common_passwords:
            raise forms.ValidationError('너무 간단한 비밀번호입니다. 더 복잡한 비밀번호를 사용해주세요.')
        
        # 연속된 문자 검사
        if any(password1.lower().find(seq) != -1 for seq in ['123', 'abc', 'qwe', 'asd']):
            raise forms.ValidationError('연속된 문자나 숫자는 사용할 수 없습니다.')
        
        # 사용자 정보와 유사한지 검사
        userid = self.cleaned_data.get('userid')
        nickname = self.cleaned_data.get('nickname')
        
        if userid and userid.lower() in password1.lower():
            raise forms.ValidationError('비밀번호에 사용자 아이디가 포함될 수 없습니다.')
        
        if nickname and nickname.lower() in password1.lower():
            raise forms.ValidationError('비밀번호에 닉네임이 포함될 수 없습니다.')
        
        return password1

    def clean_password2(self):
        pw1 = self.cleaned_data.get("password1")
        pw2 = self.cleaned_data.get("password2")
        if pw1 and pw2 and pw1 != pw2:
            raise forms.ValidationError("비밀번호가 일치하지 않습니다.")
        return pw2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # 비밀번호 암호화
        if commit:
            user.save()
        return user