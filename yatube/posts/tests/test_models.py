from django.test import TestCase
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

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTests.post
        group = PostModelTests.group
        post_text = post.text[:15]
        group_name = group.title
        self.assertEqual(post_text, str(post))
        self.assertEqual(group_name, str(group))
