from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name="Naming")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(verbose_name="Description")

    def __str__(self) -> str:
        return str(self.title)


class Post(models.Model):
    text = models.TextField(
        verbose_name="Text",
        help_text='Enter post text'
    )
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name="Author"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name="Group",
        help_text='Group, to each post is connected to'
    )
    image = models.ImageField(
        verbose_name='Image',
        upload_to='posts/',
        blank=True,
        null=True,
    )

    def __str__(self):
        return f'{self.text[:15]}'

    class Meta:
        ordering = ['-pub_date']
        verbose_name_plural = 'Posts'


class Comment(models.Model):
    text = models.TextField(
        max_length=255,
        verbose_name="Comment's text",
        help_text="Enter comment's text")

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Author"
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Post",
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date")


class Follow(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )

    unique_together = [['author', 'user']]
