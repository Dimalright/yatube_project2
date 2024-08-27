import shutil
import tempfile

from posts.forms import PostForm
from posts.models import Post, User, Group
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test Group',
            slug='test-slug',
            description='Test description'
        )
        # Создаем форму, если нужна проверка атрибутов
        cls.form = PostForm()
        cls.post = Post.objects.create(
            text='text_test',
            author=cls.author,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Удаление временной директории после завершения тестов
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id  # Передаем ID группы, чтобы избежать проблем
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        # Проверяем статус кода
        self.assertEqual(response.status_code, 200)

        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:profile', kwargs={'username': self.author.username}))

        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)

        # Проверяем, что создалась запись с заданным текстом и группой
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=self.group.id  # Проверяем на соответствие группе
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        post_id = self.post.id
        form_data = {
            'text': 'Updated text',
            'group': self.group.id
        }

        # Отправляем POST-запрос на редактирование поста
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(post_id,)),
            data=form_data,
            follow=True
        )

        # Проверяем, что редирект сработал правильно
        self.assertRedirects(response, reverse('posts:post_detail', args=(post_id,)))

        # Обновляем объект поста из базы данных
        updated_post = Post.objects.get(id=post_id)

        # Проверяем, что текст поста был обновлен
        self.assertEqual(updated_post.text, 'Updated text')

        # Проверяем, что группа поста не изменилась
        self.assertEqual(updated_post.group.id, self.group.id)
