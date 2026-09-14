from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Question, Topic


class SaveTestAnswerTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            email="tester@example.com",
            password="strongpass123",
        )
        self.client.force_login(self.user)

        self.topic = Topic.objects.create(title="Математика", author=self.user)
        self.question = Question.objects.create(
            author=self.user,
            topic=self.topic,
            text="Какой ответ правильный?",
            option_a="Первый",
            option_b="Второй",
            option_c="Третий",
            option_d="Четвёртый",
            correct_answer="A",
        )

        session = self.client.session
        session["test_topic_id"] = self.topic.id
        session["test_question_ids"] = [self.question.id]
        session["test_answers"] = {}
        session["test_expires_at"] = (timezone.now() + timezone.timedelta(minutes=10)).isoformat()
        session.save()

    def test_second_answer_choice_is_rejected(self):
        first_response = self.client.post(
            reverse("save_test_answer"),
            {"question_id": self.question.id, "answer": "B"},
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertJSONEqual(first_response.content.decode(), {"ok": True})

        second_response = self.client.post(
            reverse("save_test_answer"),
            {"question_id": self.question.id, "answer": "C"},
        )

        self.assertEqual(second_response.status_code, 409)
        self.assertEqual(second_response.json()["locked"], True)
        self.assertEqual(second_response.json()["selected"], "B")
        self.assertEqual(self.client.session["test_answers"][str(self.question.id)], "B")
