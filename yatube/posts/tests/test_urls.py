from django.test import TestCase, Client
from posts.models import Post, Group, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test Group',
            slug='test-slug',
            description='Test description'
        )
        cls.post = Post.objects.create(
            text='test text',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.other_user = User.objects.create_user(username='other_user')
        self.other_client = Client()
        self.other_client.force_login(self.other_user)

    def test_url_accessibility(self):
        """Проверяет доступность всех страниц разными типами пользователей"""

        # Определяем страницы и ожидаемые шаблоны для проверки
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/profile/{self.user.username}/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
        }

        # Проверка для неавторизованных пользователей
        for template, address in templates_url_names.items():
            with self.subTest(user='guest', address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template)

        # Проверка для авторизованных пользователей
        with self.subTest(user='authorized'):
            response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
            self.assertTemplateUsed(response, 'posts/update_post.html')

            response = self.authorized_client.get('/create/')
            self.assertTemplateUsed(response, 'posts/create_post.html')

        # Проверка для других авторизованных пользователей
        with self.subTest(user='other'):
            response = self.other_client.get('/create/')
            self.assertTemplateUsed(response, 'posts/create_post.html')

            response = self.other_client.get(f'/posts/{self.post.id}/edit/')
            self.assertEqual(response.status_code, 302)

        # Проверка для несуществующих страниц

            response = self.guest_client.get('/nonexistent_page/')
            self.assertEqual(response.status_code, 404)

    def test_create_post_redirect(self):
        """Страницы недоступные для неавторизованных пользователей перенаправляют пользователя на страницу логина."""
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_user_core404_template(self):
        """Вызов кастомного шаблона"""
        response = self.guest_client.get('/sdasd/')
        self.assertTemplateUsed(response, 'core/404.html')
