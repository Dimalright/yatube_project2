from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Post, Group, User, Comment, Follow
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import time
from django.core.cache import cache
import time


class PostContextTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.follower_user = User.objects.create_user(username='follower')
        cls.non_follower_user = User.objects.create_user(username='non_follower')
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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        # Создаем 13 постов, чтобы проверить пагинацию
        cls.posts = [
            Post.objects.create(
                text=f'Test post {i}',
                author=cls.user,
                group=cls.group,
                image=uploaded if i == 0 else None
            ) for i in range(13)
        ]
        # Создаем новый пост для проверки в разных местах
        cls.new_post = Post.objects.create(
            text='New Test Post',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )
        cls.posts.append(cls.new_post)
        cls.comment = Comment.objects.create(
            post=cls.new_post,
            author=cls.user,
            text='test comment'
        )
        Follow.objects.create(
            user=cls.follower_user,
            author=cls.user)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_follower_client = Client()
        self.authorized_non_follower_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_follower_client.force_login(self.follower_user)
        self.authorized_non_follower_client.force_login(self.non_follower_user)
        self.post = self.posts[0]
        self.post_with_comment = self.posts[13]
        cache.clear()

    def test_index_page_context_and_pagination(self):
        """Проверка контекста и пагинации главной страницы."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        # Проверяем, что на первой странице 10 постов
        self.assertEqual(len(response.context['page_obj']), 10)
        # Проверяем, что картинка передалась в пост
        first_post = response.context['page_obj'][0]
        self.assertTrue(first_post.image, 'Изображение отсутствует в посте')
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
        # Проверяем, что картинка передалась в пост
        first_post = response.context['page_obj'][0]
        self.assertTrue(first_post.image, 'Изображение отсутствует в посте')
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
        # Проверяем, что картинка передалась в пост
        first_post = response.context['page_obj'][0]
        self.assertTrue(first_post.image, 'Изображение отсутствует в посте')
        # Проверяем, что на второй странице 4 поста
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
        self.assertTrue(post.image, 'Не содержит картинки')

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

    def test_post_comment_vision_in_post_detail(self):
        """Проверка, что комментарий появляется на странице поста"""
        response = self.authorized_client.get(reverse('posts:post_detail', kwargs={'post_id': self.post_with_comment.pk}))
        comments = response.context['comments']
        self.assertIn(self.comment, comments)

    def test_post_comment_only_authorized_user(self):
        """Проверям что только авторизованный юзер может комментить"""
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.new_post.pk}),
            {'text': 'blablabla'},
            follow=True
        )
        self.assertRedirects(response, f'/auth/login/?next=/posts/{self.new_post.pk}/comment/')
        self.assertFalse(Comment.objects.filter(text='blablabla').exists())

    def test_cache_work_in_index_page(self):
        """Проверям корректную работу кэща index_page"""
        response = self.authorized_client.get(reverse('posts:index'))
        content_before = response.content
        Post.objects.create(text='blasdad', author=self.user, group=self.group)
        response = self.authorized_client.get(reverse('posts:index'))
        content_after = response.content
        self.assertEqual(content_before, content_after)
        time.sleep(20)
        response = self.authorized_client.get(reverse('posts:index'))
        content_update = response.content
        self.assertNotEqual(content_before, content_update)

    def test_auhh_user_can_follow_unfollow(self):
        """Проверка авториз. польз. можете подписываться и отписываться"""
        another_user = User.objects.create_user(username='another_user')
        response_follow = self.authorized_client.get(reverse('posts:profile_follow', kwargs={'username': another_user.username}))
        self.assertEqual(response_follow.status_code, 302)
        self.assertTrue(self.user.follower.exists())
        response_unfollow = self.authorized_client.get(reverse('posts:profile_unfollow', kwargs={'username': another_user.username}))
        self.assertEqual(response_unfollow.status_code, 302)
        self.assertFalse(self.user.follower.exists())

    def test_follow_index_page_context(self):
        """Проверка контекста страницы подписок."""
        response = self.authorized_follower_client.get(reverse('posts:follow_index'))
        self.assertIn('posts', response.context)
        self.assertIn(self.new_post, response.context['posts'])
        # Проверяем, что посты от неподписанных пользователей не отображаются
        response_non_follower = self.authorized_non_follower_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.new_post, response_non_follower.context['posts'])
