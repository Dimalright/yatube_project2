from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        text = self.cleaned_data.get('text', '')
        if not text.strip():
            raise forms.ValidationError('Поле не может быть пустым или содержать только пробелы.')
        return text
