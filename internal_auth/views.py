# internal_auth/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.conf import settings
from django import forms
from .models import UserProfile
from news.models import NewsArticle, UserFollow, CategorySubscription, TagSubscription, NewsCategory
from taggit.models import Tag

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


def logout_view(request):
    """自定义注销视图，同时支持 GET 和 POST 请求"""
    logout(request)
    redirect_url = getattr(settings, 'LOGOUT_REDIRECT_URL', '/news/')
    return redirect(redirect_url)


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
    user_articles = NewsArticle.objects.filter(author=request.user).order_by('-publish_date')[:10]

    # 获取关注/订阅数据
    following_ids = UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    following_users = User.objects.filter(id__in=following_ids)
    follower_ids = UserFollow.objects.filter(following=request.user).values_list('follower_id', flat=True)
    followers = User.objects.filter(id__in=follower_ids)
    subscribed_categories = NewsCategory.objects.filter(
        id__in=CategorySubscription.objects.filter(user=request.user).values_list('category_id', flat=True)
    )
    subscribed_tags = Tag.objects.filter(
        id__in=TagSubscription.objects.filter(user=request.user).values_list('tag_id', flat=True)
    )

    context = {
        'profile': profile,
        'user_articles': user_articles,
        'following_users': following_users,
        'followers': followers,
        'subscribed_categories': subscribed_categories,
        'subscribed_tags': subscribed_tags,
    }
    return render(request, 'internal_auth/profile.html', context)
