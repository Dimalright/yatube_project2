from django.test import TestCase, Client
from posts.models import Group, Post, User


class PostModelTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index(self):
        """Доступ к / авторизованным пользователям с помощью index.html."""
        response = self.authorized_client.get('/')
        self.assertTemplateUsed(response, 'posts/index.html')
