# news/forms.py
from django import forms
from .models import NewsArticle


class NewsArticleForm(forms.ModelForm):
    class Meta:
        model = NewsArticle
        fields = ['title', 'slug', 'intro', 'content', 'category', 'tags',
                  'image', 'status', 'is_featured', 'publish_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入文章标题'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '留空则自动从标题生成'
            }),
            'intro': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '请输入文章简介（用于列表页显示）'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 12,
                'placeholder': '请输入文章内容'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'publish_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }

    def clean_tags(self):
        tags = self.cleaned_data.get('tags')
        if tags:
            # ClusterTaggableManager 可能已经将字符串解析为列表
            if isinstance(tags, str):
                tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            elif isinstance(tags, (list, tuple)):
                tag_list = [str(tag).strip() for tag in tags if str(tag).strip()]
            else:
                tag_list = []
            if len(tag_list) > 10:
                raise forms.ValidationError('标签数量不能超过10个。')
            return ','.join(tag_list) if isinstance(tags, str) else tags
        return ''

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 2:
            raise forms.ValidationError('标题至少2个字符。')
        if len(title) > 200:
            raise forms.ValidationError('标题不能超过200个字符。')
        return title

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if not content and not self.cleaned_data.get('body'):
            raise forms.ValidationError('文章内容和正文（StreamField）至少填写一项。')
        return content
