# blog/forms.py

from django import forms
from .models import Post, Tag, PostTag
from django.contrib import messages
from django.db import transaction

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