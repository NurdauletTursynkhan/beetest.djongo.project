from django import forms

from .models import Question, Topic


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ("title", "description")
        labels = {
            "title": "Название темы",
            "description": "Описание",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Например: История Казахстана"}),
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Коротко опишите тему..."}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = (
            "topic", "text", "image", "option_a", "option_b",
            "option_c", "option_d", "correct_answer",
            "is_published",
        )
        labels = {
            "topic": "Тема",
            "text": "Вопрос",
            "image": "Фото к вопросу",
            "option_a": "А",
            "option_b": "Б",
            "option_c": "В",
            "option_d": "Г",
            "correct_answer": "Правильный ответ",
            "is_published": "Опубликовать",
        }
        widgets = {
            "text": forms.Textarea(attrs={"rows": 4, "placeholder": "Введите текст вопроса..."}),
            "image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "option_a": forms.TextInput(attrs={"placeholder": "Вариант А"}),
            "option_b": forms.TextInput(attrs={"placeholder": "Вариант Б"}),
            "option_c": forms.TextInput(attrs={"placeholder": "Вариант В"}),
            "option_d": forms.TextInput(attrs={"placeholder": "Вариант Г"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["topic"].queryset = Topic.objects.all()
        self.fields["topic"].required = True
        self.fields["topic"].empty_label = "Выберите тему"
