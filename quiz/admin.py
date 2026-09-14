from django.contrib import admin

from .models import Question, TestAnswer, TestAttempt, TestResult, Topic


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "question_count", "created_at")
    search_fields = ("title", "description", "author__email")

    def question_count(self, obj):
        return obj.questions.count()

    question_count.short_description = "Вопросов"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "topic", "author", "correct_answer", "is_published", "created_at")
    list_filter = ("topic", "is_published", "correct_answer")
    search_fields = ("text", "author__email", "author__first_name", "author__last_name", "topic__title")


class TestAnswerInline(admin.TabularInline):
    model = TestAnswer
    extra = 0
    readonly_fields = ("question", "selected_answer", "correct_answer", "is_correct")


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ("user", "topic", "correct_answers", "total_questions", "percent", "grade", "score", "created_at")
    list_filter = ("topic", "grade", "created_at")
    inlines = (TestAnswerInline,)


@admin.register(TestAnswer)
class TestAnswerAdmin(admin.ModelAdmin):
    list_display = ("result", "question", "selected_answer", "correct_answer", "is_correct")
    list_filter = ("is_correct",)


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "topic", "started_at", "expires_at", "finished_at", "result")
    list_filter = ("topic", "started_at", "finished_at")
    readonly_fields = ("question_ids", "answers", "started_at", "expires_at", "finished_at", "result")
