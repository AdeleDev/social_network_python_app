from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class URLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='urlUser')

        cls.group = Group.objects.create(
            title='Тестовая Group',
            slug='urlSlug',
            description='Test description',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Test post',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_url_access_guest(self):
        url_data = (
            ('/', HTTPStatus.OK),
            (f'/group/{self.group.slug}/', HTTPStatus.OK),
            (f'/profile/{self.user.username}/', HTTPStatus.OK),
            (f'/posts/{self.post.pk}/', HTTPStatus.OK),
            ('/create/', HTTPStatus.FOUND),
        )

        for value, expected in url_data:
            with self.subTest(value=value):
                response = self.guest_client.get(value)
                self.assertEqual(
                    response.status_code, expected)

    def test_create_auth_url_access(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(HTTPStatus.OK, response.status_code)

    def test_edit_url_access_guest(self):
        response = self.guest_client.get(
            f'/posts/{self.post.pk}/edit/',
            follow=True)
        self.assertRedirects(
            response,
            '/auth/login/?next=%2Fposts%2F1%2Fedit%2F')

    def test_edit_url_access_author(self):
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(HTTPStatus.OK, response.status_code)

    def test_url_not_found(self):
        response = self.guest_client.get('/notexist/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                print(
                    f'Got response code : {response.status_code} for '
                    f'{address}')
                self.assertTemplateUsed(response, template)

    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(
            response.status_code, HTTPStatus.NOT_FOUND)
