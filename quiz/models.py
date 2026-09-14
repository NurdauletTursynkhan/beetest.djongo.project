from io import BytesIO
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageOps


class Topic(models.Model):
    title = models.CharField("Тема", max_length=120)
    description = models.TextField("Описание", blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="topics",
        verbose_name="Автор",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Question(models.Model):
    ANSWER_CHOICES = [
        ("A", "А"),
        ("B", "Б"),
        ("C", "В"),
        ("D", "Г"),
    ]

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions",
        verbose_name="Тема",
    )
    text = models.TextField("Вопрос")
    image = models.ImageField("Фото", upload_to="questions/", blank=True, null=True)
    option_a = models.CharField("А", max_length=500)
    option_b = models.CharField("Б", max_length=500)
    option_c = models.CharField("В", max_length=500)
    option_d = models.CharField("Г", max_length=500)
    correct_answer = models.CharField("Правильный ответ", max_length=1, choices=ANSWER_CHOICES)
    is_published = models.BooleanField("Опубликован", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.text[:80]

    def save(self, *args, **kwargs):
        old_image_name = None
        if self.pk:
            old_image_name = Question.objects.filter(pk=self.pk).values_list("image", flat=True).first()
        super().save(*args, **kwargs)
        if self.image and self.image.name != old_image_name and not getattr(self, "_normalizing_image", False):
            self.normalize_image()

    def get_option(self, letter):
        return {
            "A": self.option_a,
            "B": self.option_b,
            "C": self.option_c,
            "D": self.option_d,
        }[letter]

    def normalize_image(self):
        self.image.open("rb")
        with Image.open(self.image) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image = ImageOps.fit(image, (1200, 675), Image.Resampling.LANCZOS)
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=86, optimize=True)

        old_path = Path(self.image.path)
        filename = f"questions/{uuid4().hex}.jpg"
        self._normalizing_image = True
        self.image.save(filename, ContentFile(buffer.getvalue()), save=False)
        super().save(update_fields=["image"])
        self._normalizing_image = False
        if old_path.exists() and old_path != Path(self.image.path):
            old_path.unlink()


class TestResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="results")
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name="results")
    total_questions = models.PositiveIntegerField(default=50)
    correct_answers = models.PositiveIntegerField(default=0)
    score = models.PositiveIntegerField(default=0)
    percent = models.PositiveIntegerField(default=0)
    grade = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.score} баллов"


class TestAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="test_attempts")
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name="test_attempts")
    question_ids = models.JSONField(default=list)
    answers = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    result = models.OneToOneField(TestResult, on_delete=models.SET_NULL, null=True, blank=True, related_name="attempt")

    class Meta:
        ordering = ["-started_at"]

    @property
    def is_finished(self):
        return self.finished_at is not None

    def __str__(self):
        return f"{self.user.email} - attempt #{self.pk}"


class TestAnswer(models.Model):
    result = models.ForeignKey(TestResult, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="test_answers")
    selected_answer = models.CharField(max_length=1, blank=True)
    correct_answer = models.CharField(max_length=1)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.question_id}: {self.selected_answer or '-'} / {self.correct_answer}"
