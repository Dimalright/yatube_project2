from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Post, Group, User
from django import forms


class PostContextTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test Group',
            slug='test-slug',
            description='Test description'
        )
        cls.other_group = Group.objects.create(
            title='Other Group',
            slug='other-slug',
            description='Other description'
        )
        # Создаем 13 постов, чтобы проверить пагинацию
        cls.posts = [
            Post.objects.create(
                text=f'Test post {i}',
                author=cls.user,
                group=cls.group
            ) for i in range(13)
        ]

        # Создаем новый пост для проверки в разных местах
        cls.new_post = Post.objects.create(
            text='New Test Post',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = self.posts[0]

    def test_index_page_context_and_pagination(self):
        """Проверка контекста и пагинации главной страницы."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        # Проверяем, что на первой странице 10 постов
        self.assertEqual(len(response.context['page_obj']), 10)
        # Проверяем, что на второй странице 3 поста
        response = self.authorized_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_group_posts_page_context_and_pagination(self):
        """Проверка контекста и пагинации страницы группы."""
        response = self.authorized_client.get(reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertIn('page_obj', response.context)
        self.assertIn('group', response.context)
        group = response.context['group']
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        # Проверяем, что на первой странице 10 постов
        self.assertEqual(len(response.context['page_obj']), 10)
        # Проверяем, что на второй странице 3 поста
        response = self.authorized_client.get(reverse('posts:group_list', kwargs={'slug': self.group.slug}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_profile_page_context_and_pagination(self):
        """Проверка контекста и пагинации страницы профиля."""
        response = self.authorized_client.get(reverse('posts:profile', kwargs={'username': self.user.username}))
        self.assertIn('page_obj', response.context)
        self.assertIn('profile_user', response.context)
        profile_user = response.context['profile_user']
        self.assertEqual(profile_user.username, self.user.username)
        # Проверяем, что на первой странице 10 постов
        self.assertEqual(len(response.context['page_obj']), 10)
        # Проверяем, что на второй странице 3 поста
        response = self.authorized_client.get(reverse('posts:profile', kwargs={'username': self.user.username}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_post_detail_page_context(self):
        """Проверка контекста страницы поста."""
        response = self.authorized_client.get(reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertIn('post', response.context)
        post = response.context['post']
        self.assertEqual(post.text, 'Test post 0')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)

    def test_post_create_page_context(self):
        """Проверка контекста страницы создания поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], forms.ModelForm)

    def test_post_edit_page_context(self):
        """Проверка контекста страницы редактирования поста."""
        response = self.authorized_client.get(reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        self.assertIn('form', response.context)
        self.assertIn('post', response.context)
        self.assertIn('is_edit', response.context)
        self.assertIsInstance(response.context['form'], forms.ModelForm)
        self.assertTrue(response.context['is_edit'])
        self.assertEqual(response.context['post'], self.post)

    def test_post_appears_on_main_page(self):
        """Проверка, что новый пост появляется на главной странице."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn(self.new_post, response.context['page_obj'].object_list)

    def test_post_appears_on_group_page(self):
        """Проверка, что новый пост появляется на странице группы."""
        response = self.authorized_client.get(reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertIn(self.new_post, response.context['page_obj'].object_list)

    def test_post_appears_on_profile_page(self):
        """Проверка, что новый пост появляется на странице профиля пользователя."""
        response = self.authorized_client.get(reverse('posts:profile', kwargs={'username': self.user.username}))
        self.assertIn(self.new_post, response.context['page_obj'].object_list)

    def test_post_does_not_appear_in_other_group(self):
        """Проверка, что новый пост не появляется на странице другой группы."""
        response = self.authorized_client.get(reverse('posts:group_list', kwargs={'slug': self.other_group.slug}))
        self.assertNotIn(self.new_post, response.context['page_obj'].object_list)
