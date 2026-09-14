from django.urls import path

from .views import (
    finish_test,
    home,
    question_create,
    question_delete,
    question_edit,
    rating,
    save_test_answer,
    start_test,
    topic_create,
    topic_delete,
    topics,
)


urlpatterns = [
    path("", home, name="home"),
    path("topics/", topics, name="topics"),
    path("topics/create/", topic_create, name="topic_create"),
    path("topics/<int:pk>/delete/", topic_delete, name="topic_delete"),
    path("create/", question_create, name="question_create"),
    path("question/<int:pk>/edit/", question_edit, name="question_edit"),
    path("question/<int:pk>/delete/", question_delete, name="question_delete"),
    path("test/start/", start_test, name="start_test"),
    path("test/topic/<int:topic_id>/", start_test, name="start_topic_test"),
    path("test/finish/", finish_test, name="finish_test"),
    path("test/save-answer/", save_test_answer, name="save_test_answer"),
    path("rating/", rating, name="rating"),
]
