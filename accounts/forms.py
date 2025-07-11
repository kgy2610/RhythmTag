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
            # 1단계: 아이디가 존재하는지 확인
            try:
                user = User.objects.get(userid=userid)
            except User.DoesNotExist:
                # 아이디가 존재하지 않는 경우
                raise ValidationError('존재하지 않는 아이디입니다.')
            
            # 2단계: 계정이 활성화되어 있는지 확인
            if not user.is_active:
                raise ValidationError('비활성화된 계정입니다. 관리자에게 문의하세요.')
            
            # 3단계: 비밀번호 확인
            if not user.check_password(password):
                # 비밀번호가 틀린 경우
                raise ValidationError('비밀번호가 틀렸습니다.')
            
            # 모든 검증을 통과한 경우
            self.user_cache = user

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
    
# 회원 탈퇴
class AccountDeleteForm(forms.Form):
    password = forms.CharField(
        label='현재 비밀번호',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '현재 비밀번호를 입력하세요',
            'id': 'password-input'
        }),
        help_text='계정 삭제를 위해 현재 비밀번호를 입력해주세요.'
    )
    
    confirm_delete = forms.BooleanField(
        label='위 내용을 모두 확인했으며, 회원탈퇴에 동의합니다.',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'confirm-checkbox'
        }),
        required=True,
        error_messages={
            'required': '회원 탈퇴에 동의해주세요.'
        }
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            # 현재 사용자의 비밀번호가 맞는지 확인
            if not authenticate(userid=self.user.userid, password=password):
                raise forms.ValidationError('현재 비밀번호가 올바르지 않습니다.')
        return password