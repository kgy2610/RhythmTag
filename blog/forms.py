# blog/forms.py

from django import forms
from .models import Post, Tag, PostTag

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
        fields = ['title', 'content', 'link', 'status']
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
                'placeholder': 'https://www.youtube.com/watch?v=...'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
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

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            # 기존 태그 관계 제거
            instance.tags.clear()
            
            # 새 태그 추가
            tags = self.cleaned_data.get('tag_input', [])
            for tag_name in tags:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                PostTag.objects.create(post=instance, tag=tag)
        
        return instance