from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask_login import UserMixin
from flask_bcrypt import Bcrypt, check_password_hash


db = SQLAlchemy()
bcrypt = Bcrypt()


# Класс таблицы пользователей
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    login = db.Column(db.String(500), nullable=False, unique=True)
    email = db.Column(db.String(500), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=True)
    activated = db.Column(db.Boolean(), default=False)


# Класс таблицы для сообщений пользователя
class DetoxicMemory(db.Model):
    __tablename__ = 'detoxicMemory'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    toxic_message = db.Column(db.String(150), nullable=False)
    detoxic_message = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)


# Функция хэширования пользовательского пароля
def hash_password(password: str) -> str:
    return bcrypt.generate_password_hash(password).decode('utf-8')


# Функция авторизация пользователя
def authentificate_password(check: str, password: str) -> User | None:
    user = User.query.filter(or_(User.login == check, User.email == check)).first()
    if user and user.password and check_password_hash(user.password, password):
        return user
    return None


# Функция авторизации по пользователей через OAuth
def authentificate_oauth(email: str, login: str) -> User:
    user = User.query.filter(User.email == email).first()
    if not user:
        add_user(login, email, activated=True)
        user = User.query.filter(User.email == email).first()
    return user


# Функция добавления нового пользователя в БД
def add_user(login, email, password=None, activated=False):
    user = User(login=login,
                email=email,
                password=password,
                activated=activated)
    db.session.add(user)
    db.session.commit()


# Функция активации пользовательского аккаунта
def activate_user(email: str) -> None:
    user = User.query.filter(User.email == email).first()
    user.activated = True
    db.session.commit()


# Функция обновления пароля пользователя в БД
def update_password(email: str, new_password: str) -> None:
    user = User.query.filter(User.email == email).first()
    if user:
        password_hash = hash_password(new_password)
        user.password = password_hash
        db.session.commit()
