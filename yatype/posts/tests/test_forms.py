import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import Group, Post, Comment, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class BaseSetupClass(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='testUser')
        cls.user2 = User.objects.create_user(username='testUser2')

        cls.group = Group.objects.create(
            title='Тестовая Group',
            slug='testSlug',
            description='Test description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test post',
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Comment',
            post=cls.post
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormsTests(BaseSetupClass):

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Check',
            'group': self.group.pk
        }
        self.do_creation_check(form_data, posts_count)

    def test_edit_post(self):
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Check 2',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.pk}'}),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(posts_count, Post.objects.count())

        updated_post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(form_data['text'], updated_post.text)
        self.assertIsNone(updated_post.group)

    def test_edit_post_no_rights(self):
        form_data = {
            'text': 'Check no rights',
        }
        response = self.guest_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.pk}'}),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        updated_post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(self.post.text, updated_post.text)
        self.assertEqual(None, updated_post.group)

    def test_image_post(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Image post',
            'group': self.group.pk,
            'image': uploaded,
        }
        self.do_creation_check(form_data, posts_count)

    def do_creation_check(self, form_data, posts_count):
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(posts_count + 1, Post.objects.count())

        created_post = Post.objects.get(text=form_data['text'])
        self.assertEqual(form_data['text'], created_post.text)
        if 'image' in form_data:
            self.assertEqual(
                f'posts/{str(form_data["image"])}',
                str(created_post.image))
        self.assertEqual(self.group, created_post.group)
        self.assertEqual(self.user, created_post.author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT)


class CommentFormTests(BaseSetupClass):
    def test_comment_post(self):
        comments_count = Comment.objects.filter(
            post_id=self.post.pk).count()
        form_data = {
            'text': 'Comment no rights',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{self.post.pk}'}),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        comments_count_after = Comment.objects.filter(
            post_id=self.post.pk).count()
        self.assertEqual(comments_count + 1, comments_count_after)

    def test_comment_post_no_rights(self):
        comments_count = Comment.objects.filter(
            post_id=self.post.pk).count()
        form_data = {
            'text': 'Comment no rights',
        }
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{self.post.pk}'}),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        comments_count_after = Comment.objects.filter(
            post_id=self.post.pk).count()
        self.assertEqual(comments_count, comments_count_after)


class FollowFormTests(BaseSetupClass):
    def test_follow(self):
        followers = Follow.objects.filter(
            user_id=self.user.pk).count()

        form_data = {
            'author': self.user2.pk,
        }
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': 'testUser2'}),
            data=form_data,
            follow=True
        )
        followers_new = Follow.objects.filter(
            user_id=self.user.pk).count()
        self.assertEqual(followers + 1, followers_new)

    def test_unfollow(self):
        form_data = {
            'author': self.user2.pk,
        }
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': 'testUser2'}),
            data=form_data,
            follow=True
        )
        followers = Follow.objects.filter(
            user_id=self.user.pk).count()

        self.authorized_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': 'testUser2'}),
            data=form_data,
            follow=True
        )
        followers_new = Follow.objects.filter(
            user_id=self.user.pk).count()
        self.assertEqual(followers - 1, followers_new)

    def test_no_wrong_follow(self):
        self.user3 = User.objects.create_user(username='testUser3')
        self.authorized_client_new = Client()
        self.authorized_client_new.force_login(self.user3)

        # user 1 follow user 2
        form_data = {
            'author': self.user2.pk,
        }
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': 'testUser2'}),
            data=form_data,
            follow=True
        )

        # user 3 follow user 1
        form_data = {
            'author': self.user.pk,
        }
        self.authorized_client_new.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': f'{self.user.username}'}),
            data=form_data,
            follow=True
        )

        followers = Follow.objects.filter(
            user_id=self.user3.pk).values()
        self.assertEqual(1, followers.count())
        self.assertEqual(self.user.pk, followers[0]['author_id'])
