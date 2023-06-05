import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class BaseSetupClass(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='viewUser')

        cls.group = Group.objects.create(
            title='Test Group',
            slug='viewSlug',
            description='Test description',
        )

        cls.posts = []
        for x in range(13):
            cls.posts.append(Post(
                text='Test text',
                group=cls.group,
                author=cls.user))
        Post.objects.bulk_create(cls.posts)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ContextViewsTests(BaseSetupClass):

    def setUp(self):
        super().setUp()
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

        self.image_post = Post.objects.create(
            text='Image',
            group=self.group,
            author=self.user,
            image=uploaded)

    def test_index_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('user', response.context)
        self.assertIn('text', response.context)
        self.assertEqual(
            self.image_post.image,
            Post.objects.get(pk=self.image_post.pk).image)
        self.assertEqual(
            response.context['user'],
            self.user)
        self.assertEqual(
            response.context['text'],
            'Last updates')

    def test_group_context(self):
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': f'{self.group.slug}'}))
        self.assertIn('group', response.context)
        self.assertEqual(
            self.image_post.image,
            Post.objects.get(pk=self.image_post.pk).image)
        self.assertEqual(response.context['group'].title, self.group.title)
        self.assertEqual(response.context['group'].slug, self.group.slug)
        self.assertEqual(
            response.context['group'].description,
            self.group.description)

    def test_profile_context(self):
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': f'{self.user.username}'}))
        self.assertIn(
            str(self.image_post.image),
            str(Post.objects.get(pk=self.image_post.pk).image))
        self.assertIn('author', response.context)
        self.assertIn('posts_count', response.context)
        self.assertIn('page_obj', response.context)
        self.assertEqual(response.context['author'], self.user)

    def test_post_detail_context(self):
        created_post = Post.objects.get(pk=self.image_post.pk)
        form_data = {
            'text': 'Test comment',
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{created_post.pk}'}),
            data=form_data,
            follow=True
        )

        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': f'{created_post.pk}'}))

        self.assertIn('post', response.context)
        self.assertIn('can_edit', response.context)
        self.assertIn('comments', response.context)
        self.assertEqual(created_post, response.context['post'])
        self.assertContains(response, 'post', 7)
        self.assertContains(response, 'image', 3)
        self.assertEqual(
            str('Test comment'),
            str(response.context['comments'][0].text))
        self.assertEqual(response.context['can_edit'], True)

    def test_create_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertEqual(
            self.user,
            response.context.get('user')
        )

        self.assertIsNone(
            response.context.get('form')['text'].value()
        )
        self.assertIsNone(
            response.context.get('form')['group'].value()
        )

        self.assertIn('user', response.context)
        self.assertIn('form', response.context)
        self.assertEqual(
            response.context['user'],
            self.user)
        self.assertIn(
            str(self.group),
            str(response.context['form']['group'])
        )

    def test_edit_context(self):
        created_post = Post.objects.first()
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': f'{created_post.pk}'}))
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIsInstance(response.context['post'], Post)
        self.assertEqual(response.context['is_edit'], True)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT)


class PaginatorViewsTests(BaseSetupClass):

    def setUp(self):
        super().setUp()

    def do_paginator_check(self, response):
        self.assertEqual(5, len(response.context['page_obj']))

        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(5, len(response.context['page_obj']))

    def test_index_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.do_paginator_check(response)

    def test_group_context(self):
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': f'{self.group.slug}'}))
        self.do_paginator_check(response)

    def test_profile_context(self):
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': f'{self.user.username}'}))
        self.do_paginator_check(response)


class TemplateViewsTests(BaseSetupClass):

    def test_pages_uses_correct_template(self):
        cache.clear()
        post = Post.objects.first()
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': f'{self.group.slug}'}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={
                    'username': f'{self.user.username}'}):
                'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{post.pk}'}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{post.pk}'}): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                print(f'Run case for reverse_name {reverse_name}')
                self.assertTemplateUsed(response, template)

    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertTemplateUsed(response, 'core/404.html')


class PostsViewsCache(BaseSetupClass):

    def test_cache_index(self):
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='Cash post',
            author=self.user,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        before_clean_cache = response_old.content
        self.assertEqual(before_clean_cache, posts)
        cache.clear()
        after_clean_cache = self.authorized_client.get(reverse('posts:index'))
        new_posts = after_clean_cache.content
        self.assertNotEqual(before_clean_cache, new_posts)
