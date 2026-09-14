# BEE TEST — Django

Красивый адаптивный сайт тестирования в жёлто-чёрно-белом стиле.

## Возможности

- Регистрация: имя, фамилия, email, пароль, подтверждение пароля
- Вход/выход
- Профиль и редактирование данных
- Смена пароля
- Создание вопросов
- Редактирование/удаление своих вопросов
- Суперпользователь может управлять всеми вопросами через Django Admin
- Публичные вопросы на главной
- Случайный тест из 50 вопросов
- 1 правильный ответ = 1 балл
- Результат после теста
- Общий рейтинг
- Адаптация для ПК и телефона

## Запуск в VS Code

### Windows PowerShell

```powershell
cd путь\к\bee_test_django
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Если PowerShell запрещает активацию:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Потом снова:

```powershell
.\venv\Scripts\Activate.ps1
```

Открой:
http://127.0.0.1:8000/

Админка:
http://127.0.0.1:8000/admin/

## Важно

Для кнопки «Начать тест» нужно минимум 50 опубликованных вопросов.

Для продакшена обязательно заменить SECRET_KEY, DEBUG=False, настроить ALLOWED_HOSTS и базу данных.
