from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import RegisterForm, LoginForm, ProfileForm, ChangePasswordForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Аккаунт успешно создан!")
            return redirect("home")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            login(request, form.user)
            messages.success(request, "Вы вошли в аккаунт.")
            return redirect("home")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("home")

@login_required
def profile_view(request):
    from quiz.models import Question, TestResult
    my_questions = Question.objects.filter(author=request.user).count()
    results = TestResult.objects.filter(user=request.user)
    total_points = sum(r.score for r in results)
    return render(request, "accounts/profile.html", {
        "my_questions": my_questions,
        "tests_count": results.count(),
        "total_points": total_points,
    })

@login_required
def profile_edit_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email
            user.save()
            messages.success(request, "Профиль обновлён.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile_edit.html", {"form": form})

@login_required
def password_change_view(request):
    if request.method == "POST":
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data["new_password1"])
            request.user.save()
            login(request, request.user)
            messages.success(request, "Пароль изменён.")
            return redirect("profile")
    else:
        form = ChangePasswordForm(request.user)
    return render(request, "accounts/password_change.html", {"form": form})
