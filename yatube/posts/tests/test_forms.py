import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from posts.forms import PostForm
from posts.models import Post, User, Group
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

# Создаем временную папку для медиа-файлов
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test Group',
            slug='test-slug',
            description='Test description'
        )
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

    def test_create_post_with_image(self):
        """Валидная форма создает запись в Post с картинкой."""
        posts_count = Post.objects.count()

        # Создаем тестовую картинку
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

        form_data = {
            'text': 'Тестовый текст с картинкой',
            'group': self.group.id,
            'image': uploaded
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

        # Проверяем, что создалась запись с заданным текстом, группой и картинкой
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст с картинкой',
                group=self.group.id,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post_with_image(self):
        """Валидная форма редактирует запись в Post с картинкой."""
        post_id = self.post.id

        # Создаем новое тестовое изображение
        new_small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded_new = SimpleUploadedFile(
            name='new_small.gif',
            content=new_small_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Updated text with new image',
            'group': self.group.id,
            'image': uploaded_new
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
        self.assertEqual(updated_post.text, 'Updated text with new image')

        # Проверяем, что группа поста не изменилась
        self.assertEqual(updated_post.group.id, self.group.id)

        # Проверяем, что изображение обновилось
        self.assertEqual(updated_post.image.name, 'posts/new_small.gif')
