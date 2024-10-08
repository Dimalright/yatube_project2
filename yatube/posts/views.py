from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect
from .models import Post, Group, User, Follow
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .forms import PostForm, CommentForm
from django.views.decorators.cache import cache_page
from django.core.exceptions import ValidationError


@cache_page(20, key_prefix='index_page')
def index(request):
    temp = 'posts/index.html'
    post_list = Post.objects.all().order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, temp, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group).order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all().order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = Follow.objects.filter(user=request.user, author=user).exists()
    context = {
        'profile_user': user,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author = get_object_or_404(User, username=post.author)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    # Здесь код запроса к модели и создание словаря контекста
    context = {
        'post': post,
        'author': author,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):

    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES,
        )

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect('posts:profile', username=request.user.username)
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.id)

    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES,
            instance=post
        )
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)

    return render(
                 request, 'posts/update_post.html',
                 {'form': form, 'post': post, 'is_edit': True}
    )


@login_required
def add_comment(request, post_id):
    # Получите пост и сохраните его в переменную post.
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    posts = Post.objects.filter(author__following__user=user)
    context = {'posts': posts}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(
            user=user, author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.filter(
            user=user, author=author
        ).delete()
    return redirect('posts:profile', username=username)
