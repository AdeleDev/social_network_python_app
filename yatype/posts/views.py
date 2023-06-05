from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Comment, Follow
from .utils import get_page_obj


@cache_page(timeout=20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related("group", "author")
    text = "Last updates"
    context = {
        'text': text,
        'page_obj': get_page_obj(request, post_list)
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    context = {
        'group': group,
        'page_obj': get_page_obj(request, post_list)
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related("group", "author")
    following = Follow.objects.filter(
        user_id=request.user.id,
        author_id=author.pk).exists()
    context = {
        'author': author,
        'posts_count': post_list.count(),
        'page_obj': get_page_obj(request, post_list),
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = Comment.objects.filter(
        post_id=post_id)

    context = {
        'post': post,
        'can_edit': request.user == post.author,
        'comments': comments,
        'form': CommentForm()
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {'form': form, 'is_edit': True, 'post': post}
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
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
    post_list = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': get_page_obj(request, post_list),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow_exists = Follow.objects.filter(
        user_id=request.user.id,
        author_id=author.pk).exists()

    if not follow_exists and request.user != author:
        Follow.objects.create(
            author=author,
            user=request.user
        )
    post_list = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': get_page_obj(request, post_list),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    unfollow = Follow.objects.filter(
        user_id=request.user.id,
        author_id=author.pk)

    unfollow.delete()
    return redirect('posts:profile', username=author)
