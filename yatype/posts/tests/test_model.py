from django.test import TestCase

from ..models import Group, Post, User, Comment


class GroupModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='G' * 201,
            slug='Test slug',
            description='Test description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test',
        )

    def test_models_have_correct_object_name(self):
        self.assertEqual(self.group.title, str(self.group))

    def test_verbose_name_group(self):
        field_verboses = (
            ('title', 'Naming'),
            ('slug', 'Slug'),
            ('description', 'Description'),
        )

        for value, expected in field_verboses:
            with self.subTest(value=value):
                print(f'Run case for field {value}')
                self.assertEqual(
                    self.group._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        expected_group = 'Group, to each post is connected to'

        self.assertEqual(
            self.post._meta.get_field('group').help_text, expected_group)


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test' * 201,
        )

    def test_models_have_correct_object_name(self):
        self.assertEqual(str(self.post), str(self.post.text[:15]))

    def test_verbose_name_post(self):
        field_verboses = (
            ('text', 'Text'),
            ('pub_date', 'Date'),
            ('author', 'Author'),
            ('group', 'Group'),
            ('image', 'Image')
        )
        for value, expected in field_verboses:
            with self.subTest(value=value):
                print(f'Run case for field {value}')
                self.assertEqual(
                    self.post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        expected_post = 'Enter post text'

        self.assertEqual(
            self.post._meta.get_field('text').help_text, expected_post)


class CommentModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test comment',
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Test' * 201,
            post=cls.post
        )

    def test_help_text(self):
        expected = "Enter comment's text"

        self.assertEqual(
            self.comment._meta.get_field('text').help_text, expected)

    def test_verbose_name_comment(self):
        field_verboses = (
            ('text', "Comment's text"),
            ('author', 'Author'),
            ('post', 'Post'),
            ('created', 'Date')
        )
        for value, expected in field_verboses:
            with self.subTest(value=value):
                print(f'Run case for field {value}')
                self.assertEqual(
                    self.comment._meta.get_field(value).verbose_name, expected)
