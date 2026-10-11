# Импорт библиотек и программных модулей
from flask import Flask, render_template, jsonify, request, Response, redirect, url_for
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from redis import Redis
from dotenv import load_dotenv
from string import ascii_letters, digits
from smtplib import SMTP
from email.message import EmailMessage
from celery import Celery
from datetime import datetime
from detox_models.detox import ModelsInference
from detox_models.model_exception import ModelException
from oauth import OAuthSignIn
from database_server import User, db, authentificate_oauth, hash_password, add_user, bcrypt, activate_user,\
    update_password, authentificate_password, DetoxicMemory
import secrets
import os


# Загрузка переменных окружения
load_dotenv()


# Инициалиция фласк приложения
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Инициализация моделей
DETOX_MODEL_PATH = os.getenv("DETOX_MODEL_PATH")
DETOX_TOKENIZER_PATH = os.getenv("DETOX_TOKENIZER_PATH")
CLASSIFIER_MODEL_PATH = os.getenv("CLASSIFIER_MODEL_PATH")
CLASSIFIER_TOKENIZER_PATH = os.getenv("CLASSIFIER_TOKENIZER_PATH")
SIMILARITY_MODEL_PATH = os.getenv("SIMILARITY_MODEL_PATH")

model_inference = ModelsInference(
    DETOX_MODEL_PATH,
    DETOX_TOKENIZER_PATH,
    CLASSIFIER_MODEL_PATH,
    CLASSIFIER_TOKENIZER_PATH,
    SIMILARITY_MODEL_PATH
)

# Инициализация менеджера пользователей
login_manager = LoginManager(app)

# Настройка подключения к бд
USERNAME = os.getenv('DATABASE_USER')
PASSWORD = os.getenv('DATABASE_PASSWORD')
HOST = os.getenv('DATABASE_HOST')
DATABASE = os.getenv('DATABASE_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}/{DATABASE}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt.init_app(app)

# Подключение фонового планировщика задачa
REDIS_HOST = os.getenv("CACHE_HOST")
REDIS_PASSWORD = os.getenv("CACHE_PASSWORD")
REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:6379/0"
celery_app = Celery(app.name, broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(app.config)

# Настройка OAuth аутентификации
OAUTH_CONFIG = {
    'google': {
        'id': os.getenv('GOOGLE_CLIENT_ID'),
        'secret': os.getenv('GOOGLE_CLIENT_SECRET')
    },
    'yandex': {
        'id': os.getenv('YANDEX_CLIENT_ID'),
        'secret': os.getenv('YANDEX_CLIENT_SECRET')
    },
    'github': {
        'id': os.getenv('GITHUB_CLIENT_ID'),
        'secret': os.getenv('GITHUB_CLIENT_SECRET')
    }
}
app.config['OAUTH_CREDENTIALS'] = OAUTH_CONFIG

LOGIN = os.getenv('MAIL_USERNAME')
PASSWORD = os.getenv('APP_PASSWORD')

# Настройка встроенного кэша
app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_URL'] = REDIS_URL
redis_client = Redis.from_url(REDIS_URL)


# Функция для отправки сообщения по email
@celery_app.task
def send_message(recipient: str, key: str) -> None:
    try:
        text = f'Код подтверждения: {key}\nЕсли вы не запрашивали подтверждение, проигнорируйте это сообщение'

        message = EmailMessage()
        message['From'] = LOGIN
        message['To'] = recipient
        message['Subject'] = 'Подтверждение почты'
        message.set_content(text)

        with SMTP('smtp.yandex.ru', 587) as server:
            server.starttls()
            server.login(LOGIN, PASSWORD)
            server.send_message(message)
    except OSError:
        print('Почты не существует')


# Фоновая функция записи сообщения пользователя в БД
@celery_app.task
def add_to_detoxicMemory(user_id: int | None, toxic_message: str, detoxic_message: str, date: datetime) -> None:
    with app.app_context():
        memory = DetoxicMemory(user_id=user_id,
                      toxic_message=toxic_message,
                      detoxic_message=detoxic_message,
                      created_at=date)
        db.session.add(memory)
        db.session.commit()


# Функция добавления в кэш сообщение пользователя
def add_to_cache(toxic_content: str, detoxic_content: str) -> None:
    cache_value = {
        'detoxic_content': detoxic_content,
    }
    redis_client.hmset(toxic_content, cache_value)


# Функция генерации ключа подтверждения почты
def generate_key(email: str) -> str:
    length_key = 6
    key = ''.join([secrets.choice(ascii_letters + digits) for _ in range(length_key)])
    redis_client.set(f'confirm {email}', key, 300)
    return key


# Функция отправки кода подтверждения на email
@app.route('/set_message', methods=['POST'])
def set_message() -> Response:
    if not request.is_json:
        return Response('Некорректный формат данных', 400)

    data = request.json
    if 'email' not in data:
        return Response('Отсутсвует почта получателя', 400)

    email = data['email']
    key = generate_key(email)
    send_message.delay(email, key)

    return Response('Код подтверждения успешно отправлен', 200)


# Создание таблиц в базе данных
with app.app_context():
    db.create_all()


# Функция получения пользователя для login manager
@login_manager.user_loader
def user_load(user_id: str) -> User | None:
    return db.session.get(User, int(user_id))


# Маршрутизация на главную страницу
@app.route('/')
def home_page():
    # Передача пользователя
    username = None
    if not current_user.is_anonymous:
        username = current_user.login

    return render_template('detox.html', username=username)


# API взаимодействия с моделями
@app.route('/inference', methods=['POST'])
def inference() -> jsonify:
    if not request.is_json:
        return Response('Некорректный формат данных', 400)

    data = request.json
    try:
        match data['task']:
            # Детоксикация
            case 'detox':
                toxic_text = data['text']
                cache_answer = redis_client.hgetall(toxic_text)
                if cache_answer:
                    detox_text = cache_answer[b'detoxic_content'].decode('utf-8')
                    return jsonify({'text': detox_text, 'source': 'cache'})

                detox_text = model_inference.detoxification_text(data['text'])
                return jsonify({"text": detox_text, 'source': 'model'}), 200
            # Классификация токсичности
            case 'classifier':
                classifier = model_inference.classifier_text(data['text'])
                percent = classifier * 100
                return jsonify({"percent": f'{percent:.2f}'}), 200
            # Определения смысловой схожести двух сообщения
            case 'similarity':
                similarity = model_inference.similarity_texts(data['toxicText'], data['detoxText'])
                percent = similarity * 100
                return jsonify({"percent": f'{percent:.2f}'}), 200
            case _:
                return Response('Операция не найдена', 404)
    # Обработки ошибок моделей и некорректных запросов
    except KeyError:
        return Response('Произошла ошибка в обработке данных', 400)
    except ModelException as model_error:
        return Response(model_error.message, 500)


# Сохранение сообщение в памяти и добавление в кэш
@app.route('/save_detoxic_message', methods=['POST'])
def save_detoxic_message():
    if not request.is_json:
        return Response('Некорректный формат данных', 400)

    data = request.json
    try:
        user_id = current_user.id if not current_user.is_anonymous else None
        toxic_context = data['toxic_context']
        detoxic_context = data['detoxic_context']
        created_at = datetime.now()

        add_to_detoxicMemory.delay(user_id, toxic_context, detoxic_context, created_at)
        add_to_cache(toxic_context, detoxic_context)
        return Response('Запрос на добавление отправлен', 200)
    except KeyError:
        return Response('Произошла ошибка в обработке данных', 400)


# Функция загрузки истории сообщений авторизиррованного пользователя
@app.route('/load_messages', methods=['GET'])
@login_required
def load_messages():
    messages_count = 25
    user_id = current_user.id
    if 'date' not in request.args:
        date = datetime.now()
    else:
        try:
            date = datetime.fromisoformat(request.args.get('date'))
        except ValueError:
            return jsonify({'error': 'Некорректный формат данных'}), 400


    messages = db.session.query(DetoxicMemory.toxic_message, DetoxicMemory.detoxic_message, DetoxicMemory.created_at)\
        .order_by(db.desc(DetoxicMemory.created_at))\
        .filter(DetoxicMemory.user_id == user_id, DetoxicMemory.created_at < date)\
        .limit(messages_count).all()
    if not messages:
        return jsonify({'messages': []}), 200

    messages = [
        {
            'toxic_message': message[0],
            'detoxic_message': message[1],
            'date': message[2].isoformat().replace('T', ' ')
        }
        for message in messages
    ]
    return jsonify({'messages': messages}), 200


# Маршрут регистрации пользователяs
@app.route('/sign_up', methods=['POST', 'GET'])
def sign_up():
    # Получения страницы
    if request.method == 'GET':
        return render_template('sign_up.html')
    elif request.method == 'POST':
        # Получения введенных данных из формы
        form = request.form
        login = form['login']
        email = form['email']
        password = form['password']
        hashed_pwd = hash_password(password)
        add_user(login, email, hashed_pwd)

        # Отправка кода подтверждения
        key = generate_key(email)
        send_message.delay(email, key)

        # Генерация токена почты
        token = secrets.token_urlsafe(32)
        redis_client.set(f'email-{token}', email, 1800)
        redis_client.set(f'task-{email}', 'activate', 300)

        # Перенаправление на подтверждение почты
        return redirect(url_for('verify_email', token=token))


# Маршрут входа в систему
@app.route('/sign_in', methods=['POST', 'GET'])
def sign_in():
    # Получение страницы
    if request.method == 'GET':
        return render_template('sign_in.html', login_failed=False)
    elif request.method == 'POST':
        # Получение данных с формы
        form = request.form
        login = form['login']
        password = form['password']

        # Проверка и вход валидного пользователя в систему с перенаправлением на главную страницу
        user = authentificate_password(login, password)
        if user and user.activated:
            login_user(user)
            return redirect('/')

        # Обновление страницы с ошибкой входа
        return render_template('sign_in.html', login_failed=True)


# Маршрут подтверждения почты пользователя
@app.route('/verify_email/<token>', methods=['GET', 'POST'])
def verify_email(token: str):
    email_bytes = redis_client.get(f'email-{token}')
    if not email_bytes:
        return Response('Токен недействителен', 500)
    current_email = email_bytes.decode('utf-8')

    if request.method == 'GET':
        return render_template('verify_email.html', email=current_email, failed=False)
    elif request.method == 'POST':
        entered_code = request.form['code']
        code_bytes = redis_client.get(f'confirm {current_email}')
        task_bytes = redis_client.get(f'task-{current_email}')

        if not code_bytes or not task_bytes:
            return Response('Код недействителен или вышло время ожидания. Повторите попытку еще раз', 404)
        check_code = code_bytes.decode('utf-8')
        task = task_bytes.decode('utf-8')

        if entered_code != check_code:
            return render_template('verify_email.html', email=current_email, failed=True)

        match task:
            case 'activate':
                redis_client.delete(f'confirm {current_email}', f'task-{current_email}')
                activate_user(current_email)
                return redirect('/sign_in')
            case 'reset_password':
                redis_client.delete(f'confirm {current_email}', f'task-{current_email}')
                return redirect(url_for('set_new_password', token=token))


# Функция восстановления пароля
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_password.html')
    elif request.method == 'POST':
        email = request.form['email']

        # Запрос на отправку кода подтверждения
        # Отправка кода подтверждения
        key = generate_key(email)
        send_message.delay(email, key)

        # Генерация токена почты
        token = secrets.token_urlsafe(32)
        redis_client.set(f'email-{token}', email, 1800)
        redis_client.set(f'task-{email}', 'reset_password', 300)

        # Перенаправление на подтверждение почты
        return redirect(url_for('verify_email', token=token))


# Функция установки нового пароля
@app.route('/set_new_password/<token>', methods=['GET', 'POST'])
def set_new_password(token: str):
    email_bytes = redis_client.get(f'email-{token}')
    if not email_bytes:
        return Response('Время ожидания истекло. Повторите процедуру восстановления пароля еще раз', 500)
    current_email = email_bytes.decode('utf-8')

    if request.method == 'GET':
        return render_template('set_new_password.html')
    elif request.method == 'POST':
        new_password = request.form['new_password']
        update_password(current_email, new_password)
        return redirect('/sign_in')



# Проверка существования логина пользователя в бд
@app.route('/check_login', methods=['GET'])
def check_login() -> Response:
    if 'login' not in request.args:
        return Response("Неверный формат данных", 400)

    login = request.args.get('login')
    login_exist = User.query.filter(User.login == login).first()
    if login_exist:
        return Response('Логин существует', 200)
    else:
        return Response('Логин не существует', 200)


# Проверка существования почты пользователя в бд
@app.route('/check_email', methods=['GET'])
def check_email() -> Response:
    if 'email' not in request.args:
        return Response("Неверный формат данных", 400)

    email = request.args.get('email')
    email_exist = User.query.filter(User.email == email).first()
    if email_exist:
        return Response('Почта существует', 200)
    else:
        return Response('Почты не существует', 200)


# Функция выхода из системы
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


# Авторизация с помощью протокола OAuth
@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


# Получение входа от стороннего ресурса
@app.route('/callback/<provider>')
def oauth_callback(provider):
    oauth = OAuthSignIn.get_provider(provider)

    email, login = oauth.callback()
    if not email and not login:
        return Response('Авторизация не прошла успешно')

    user = authentificate_oauth(email, login)
    login_user(user)
    return redirect('/')


