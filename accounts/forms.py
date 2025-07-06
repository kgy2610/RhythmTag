# accounts/forms.py

from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import AuthenticationForm

User = get_user_model()

# ✅ 회원가입 폼 (ModelForm 기반)
class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='비밀번호', widget=forms.PasswordInput)
    password2 = forms.CharField(label='비밀번호 확인', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['userid', 'nickname', 'name', 'phone']

    def clean_password2(self):
        pw1 = self.cleaned_data.get("password1")
        pw2 = self.cleaned_data.get("password2")
        if pw1 and pw2 and pw1 != pw2:
            raise forms.ValidationError("비밀번호가 일치하지 않습니다.")
        return pw2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # ✅ 비밀번호 암호화
        if commit:
            user.save()
        return user

# ✅ 로그인 폼 (userid 사용으로 통일)
class CustomAuthenticationForm(forms.Form):
    userid = forms.CharField(label='아이디', max_length=50)
    password = forms.CharField(label='비밀번호', widget=forms.PasswordInput)

    def clean(self):
        userid = self.cleaned_data.get('userid')
        password = self.cleaned_data.get('password')

        if userid and password:
            # 수정: username → userid로 통일
            self.user_cache = authenticate(username=userid, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("아이디 또는 비밀번호가 잘못되었습니다.")
            elif not self.user_cache.is_active:
                raise forms.ValidationError("비활성화된 계정입니다.")
        
        return self.cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)