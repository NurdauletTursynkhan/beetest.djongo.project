import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from .forms import QuestionForm, TopicForm
from .models import Question, TestAnswer, TestAttempt, TestResult, Topic


TEST_LIMIT = 50
TEST_DURATION_SECONDS = 50 * 60


def get_grade(percent):
    if percent >= 90:
        return "Отлично"
    if percent >= 75:
        return "Хорошо"
    if percent >= 50:
        return "Удовлетворительно"
    return "Нужно повторить тему"


def get_active_attempt(user, topic):
    if not user.is_authenticated:
        return None

    attempts = TestAttempt.objects.filter(user=user, finished_at__isnull=True)
    if topic:
        attempts = attempts.filter(topic=topic)
    else:
        attempts = attempts.filter(topic__isnull=True)
    return attempts.first()


def seconds_left(expires_at):
    return max(0, int((expires_at - timezone.now()).total_seconds()))


def prepare_questions(question_ids, answers):
    questions = list(Question.objects.filter(id__in=question_ids, is_published=True).select_related("topic"))
    question_map = {question.id: question for question in questions}
    ordered = []

    for question_id in question_ids:
        question = question_map.get(question_id)
        if not question:
            continue
        question.selected_answer = answers.get(str(question_id), "")
        ordered.append(question)

    return ordered


def build_result_details(question_ids, answers):
    questions = list(Question.objects.filter(id__in=question_ids, is_published=True).select_related("topic"))
    question_map = {question.id: question for question in questions}
    correct = 0
    details = []

    for index, question_id in enumerate(question_ids, start=1):
        question = question_map.get(question_id)
        if not question:
            continue

        selected = answers.get(str(question_id), "")
        is_correct = selected == question.correct_answer
        if is_correct:
            correct += 1

        options = []
        for letter, label in Question.ANSWER_CHOICES:
            options.append({
                "letter": letter,
                "label": label,
                "text": question.get_option(letter),
                "is_selected": selected == letter,
                "is_correct": question.correct_answer == letter,
            })

        details.append({
            "number": index,
            "question": question,
            "selected": selected,
            "correct_answer": question.correct_answer,
            "correct_text": question.get_option(question.correct_answer),
            "is_correct": is_correct,
            "options": options,
        })

    total = len(question_ids)
    percent = round(correct / total * 100) if total else 0
    return correct, total, percent, get_grade(percent), details


def finish_attempt(request, question_ids, answers, topic, attempt=None):
    correct, total, percent, grade, details = build_result_details(question_ids, answers)
    result = attempt.result if attempt and attempt.result_id else None

    if request.user.is_authenticated and result is None:
        result = TestResult.objects.create(
            user=request.user,
            topic=topic,
            total_questions=total,
            correct_answers=correct,
            score=correct,
            percent=percent,
            grade=grade,
        )
        TestAnswer.objects.bulk_create([
            TestAnswer(
                result=result,
                question=item["question"],
                selected_answer=item["selected"],
                correct_answer=item["correct_answer"],
                is_correct=item["is_correct"],
            )
            for item in details
        ])

    if attempt and not attempt.finished_at:
        attempt.finished_at = timezone.now()
        attempt.result = result
        attempt.answers = answers
        attempt.save(update_fields=["finished_at", "result", "answers"])

    request.session.pop("test_question_ids", None)
    request.session.pop("test_topic_id", None)
    request.session.pop("test_answers", None)
    request.session.pop("test_expires_at", None)
    return render(request, "quiz/result.html", {
        "correct": correct,
        "total": total,
        "percent": percent,
        "grade": grade,
        "result": result,
        "details": details,
        "topic": topic,
    })


def home(request):
    topics = Topic.objects.annotate(
        question_count=Count("questions", filter=Q(questions__is_published=True))
    ).select_related("author")
    questions = (
        Question.objects.filter(is_published=True)
        .select_related("author", "topic")
    )
    return render(request, "quiz/home.html", {
        "topics": topics,
        "questions": questions,
        "question_count": questions.count(),
        "test_limit": TEST_LIMIT,
        "test_minutes": TEST_DURATION_SECONDS // 60,
    })


def topics(request):
    topic_list = Topic.objects.annotate(
        question_count=Count("questions", filter=Q(questions__is_published=True))
    ).select_related("author")
    return render(request, "quiz/topics.html", {"topics": topic_list, "test_limit": TEST_LIMIT})


@login_required
def topic_create(request):
    if request.method == "POST":
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.author = request.user
            topic.save()
            messages.success(request, "Тема добавлена.")
            return redirect("topics")
    else:
        form = TopicForm()
    return render(request, "quiz/topic_form.html", {"form": form})


@login_required
def topic_delete(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    if topic.author != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Вы не можете удалить чужую тему.")
    if request.method == "POST":
        topic.delete()
        messages.success(request, "Тема удалена.")
        return redirect("topics")
    return render(request, "quiz/topic_confirm_delete.html", {"topic": topic})


@login_required
def question_create(request):
    if not Topic.objects.exists():
        messages.info(request, "Сначала создайте тему, потом добавьте вопрос.")
        return redirect("topic_create")

    if request.method == "POST":
        form = QuestionForm(request.POST, request.FILES)
        if form.is_valid():
            question = form.save(commit=False)
            question.author = request.user
            question.save()
            messages.success(request, "Вопрос опубликован.")
            return redirect("home")
    else:
        initial = {}
        topic_id = request.GET.get("topic")
        if topic_id:
            initial["topic"] = topic_id
        form = QuestionForm(initial=initial)
    return render(request, "quiz/question_form.html", {
        "form": form,
        "title": "Создать вопрос",
        "button": "Опубликовать",
    })


@login_required
def question_edit(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if question.author != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("У вас нет доступа к редактированию этого вопроса.")
    if request.method == "POST":
        form = QuestionForm(request.POST, request.FILES, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, "Вопрос изменён.")
            return redirect("home")
    else:
        form = QuestionForm(instance=question)
    return render(request, "quiz/question_form.html", {
        "form": form,
        "title": "Редактировать вопрос",
        "button": "Сохранить изменения",
    })


@login_required
def question_delete(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if question.author != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("У вас нет доступа к удалению этого вопроса.")
    if request.method == "POST":
        question.delete()
        messages.success(request, "Вопрос удалён.")
        return redirect("home")
    return render(request, "quiz/question_confirm_delete.html", {"question": question})


def start_test(request, topic_id=None):
    topic = None
    questions_query = Question.objects.filter(is_published=True).select_related("topic")
    if topic_id:
        topic = get_object_or_404(Topic, pk=topic_id)
        questions_query = questions_query.filter(topic=topic)

    attempt = get_active_attempt(request.user, topic)
    if attempt:
        remaining_seconds = seconds_left(attempt.expires_at)
        if remaining_seconds <= 0:
            return finish_attempt(request, attempt.question_ids, attempt.answers, attempt.topic, attempt)

        request.session["test_question_ids"] = attempt.question_ids
        request.session["test_topic_id"] = attempt.topic_id
        request.session["test_answers"] = attempt.answers
        request.session["test_expires_at"] = attempt.expires_at.isoformat()
        selected = prepare_questions(attempt.question_ids, attempt.answers)
        return render(request, "quiz/start_test.html", {
            "questions": selected,
            "topic": attempt.topic,
            "test_limit": TEST_LIMIT,
            "selected_count": len(selected),
            "test_duration_seconds": remaining_seconds,
            "test_minutes": TEST_DURATION_SECONDS // 60,
            "saved_answers": attempt.answers,
        })

    session_question_ids = request.session.get("test_question_ids")
    session_topic_id = request.session.get("test_topic_id")
    session_expires_at = parse_datetime(request.session.get("test_expires_at", ""))
    expected_topic_id = topic.id if topic else None
    if session_question_ids and session_topic_id == expected_topic_id and session_expires_at:
        session_answers = request.session.get("test_answers", {})
        remaining_seconds = seconds_left(session_expires_at)
        if remaining_seconds <= 0:
            return finish_attempt(request, session_question_ids, session_answers, topic)

        selected = prepare_questions(session_question_ids, session_answers)
        return render(request, "quiz/start_test.html", {
            "questions": selected,
            "topic": topic,
            "test_limit": TEST_LIMIT,
            "selected_count": len(selected),
            "test_duration_seconds": remaining_seconds,
            "test_minutes": TEST_DURATION_SECONDS // 60,
            "saved_answers": session_answers,
        })

    questions = list(questions_query)
    if not questions:
        return render(request, "quiz/not_enough.html", {"count": 0, "topic": topic, "test_limit": TEST_LIMIT})

    selected_count = min(len(questions), TEST_LIMIT)
    selected = random.sample(questions, selected_count)
    question_ids = [q.id for q in selected]
    expires_at = timezone.now() + timezone.timedelta(seconds=TEST_DURATION_SECONDS)

    if request.user.is_authenticated:
        TestAttempt.objects.create(
            user=request.user,
            topic=topic,
            question_ids=question_ids,
            answers={},
            expires_at=expires_at,
        )

    request.session["test_question_ids"] = question_ids
    request.session["test_topic_id"] = topic.id if topic else None
    request.session["test_answers"] = {}
    request.session["test_expires_at"] = expires_at.isoformat()
    return render(request, "quiz/start_test.html", {
        "questions": selected,
        "topic": topic,
        "test_limit": TEST_LIMIT,
        "selected_count": selected_count,
        "test_duration_seconds": TEST_DURATION_SECONDS,
        "test_minutes": TEST_DURATION_SECONDS // 60,
    })


def finish_test(request):
    if request.method != "POST":
        return redirect("start_test")

    topic_id = request.session.get("test_topic_id")
    topic = Topic.objects.filter(pk=topic_id).first() if topic_id else None
    attempt = get_active_attempt(request.user, topic)
    ids = attempt.question_ids if attempt else request.session.get("test_question_ids")
    if not ids:
        return redirect("start_test")

    answers = dict(attempt.answers if attempt else request.session.get("test_answers", {}))
    for question_id in ids:
        posted_answer = request.POST.get(f"question_{question_id}", "")
        if posted_answer in dict(Question.ANSWER_CHOICES):
            answers[str(question_id)] = posted_answer

    if attempt:
        topic = attempt.topic
    else:
        request.session["test_answers"] = answers

    return finish_attempt(request, ids, answers, topic, attempt)


@require_POST
def save_test_answer(request):
    question_id = request.POST.get("question_id")
    selected = request.POST.get("answer")
    if selected not in dict(Question.ANSWER_CHOICES):
        return JsonResponse({"ok": False}, status=400)

    try:
        question_id = int(question_id)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False}, status=400)

    topic_id = request.session.get("test_topic_id")
    topic = Topic.objects.filter(pk=topic_id).first() if topic_id else None
    attempt = get_active_attempt(request.user, topic)

    if attempt:
        if question_id not in attempt.question_ids:
            return JsonResponse({"ok": False}, status=400)
        if seconds_left(attempt.expires_at) <= 0:
            return JsonResponse({"ok": False, "expired": True}, status=400)

        answers = dict(attempt.answers)
        answers[str(question_id)] = selected
        attempt.answers = answers
        attempt.save(update_fields=["answers"])
        return JsonResponse({"ok": True, "selected": selected})

    ids = request.session.get("test_question_ids", [])
    if question_id not in ids:
        return JsonResponse({"ok": False}, status=400)

    answers = dict(request.session.get("test_answers", {}))
    answers[str(question_id)] = selected
    request.session["test_answers"] = answers
    request.session.modified = True
    return JsonResponse({"ok": True, "selected": selected})


def rating(request):
    users = (
        TestResult.objects.values("user__id", "user__first_name", "user__last_name", "user__email")
        .annotate(total_score=Sum("score"))
        .order_by("-total_score", "user__last_name", "user__first_name")
    )
    return render(request, "quiz/rating.html", {"users": users})
