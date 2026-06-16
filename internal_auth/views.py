# internal_auth/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django import forms
from .models import UserProfile

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """自定义用户注册表单，适配 CustomUser 模型"""
    email = forms.EmailField(
        required=True,
        label='邮箱',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '请输入邮箱'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入用户名'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': '请输入密码'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': '请再次输入密码'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('该邮箱已被注册。')
        return email


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'账户 {username} 已创建成功！')
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('news_home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'internal_auth/register.html', {'form': form})


@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    # 获取用户发布的文章
    from news.models import NewsArticle
    user_articles = NewsArticle.objects.filter(author=request.user).order_by('-publish_date')[:10]

    context = {
        'profile': profile,
        'user_articles': user_articles,
    }
    return render(request, 'internal_auth/profile.html', context)
