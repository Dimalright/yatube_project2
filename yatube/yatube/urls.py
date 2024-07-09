# yatube/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # импорт правил из приложения posts
    path('', include('posts.urls')),
    path('admin/', admin.site.urls),
]
