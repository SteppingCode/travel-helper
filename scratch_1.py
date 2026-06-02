from flask import Flask, render_template_string, request, redirect, url_for, send_from_directory
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Настройки для загрузки файлов
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

# Создаём папку для загрузок, если её нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Хранилище данных пользователя
user_data = {
    'name': 'Путешественник',
    'email': 'traveler@example.com',
    'phone': '',
    'city': '',
    'budget': '',
    'total_trips': '',
    'completed_trips': '',
    'places_visited': '',
    'notifications': False,
    'data_saving': False,
    'email_alerts': False,
    'avatar': None  # Путь к аватару
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Профиль | TravelPlanner</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background-color: #F9F5ED;
            font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            padding: 2rem;
            min-height: 100vh;
        }

        /* Главный контейнер */
        .main-wrapper {
            max-width: 1200px;
            margin: 0 auto;
        }

        /* ========== ШАПКА ПРОФИЛЯ ========== */
        .profile-header {
            background-color: #5E83AE;
            border-radius: 24px;
            padding: 1rem 2rem;
            margin-bottom: 2rem;
            transition: all 0.3s ease;
            width: 100%;
        }

        .header-content {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        /* Меню (3 чёрточки) */
        .menu-container {
            position: relative;
        }

        .menu-icon {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            cursor: pointer;
            padding: 10px;
            display: flex;
            flex-direction: column;
            gap: 5px;
            border-radius: 12px;
            transition: all 0.2s;
        }

        .menu-icon:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: scale(0.98);
        }

        .menu-icon span {
            display: block;
            width: 22px;
            height: 2.5px;
            background-color: white;
            border-radius: 3px;
        }

        /* Выпадающее меню */
        .dropdown-menu {
            display: none;
            position: absolute;
            top: 55px;
            left: 0;
            background: #2A2A2A;
            min-width: 220px;
            border-radius: 16px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.3);
            z-index: 100;
            overflow: hidden;
        }

        .dropdown-menu.show {
            display: block;
        }

        .dropdown-menu a {
            display: block;
            padding: 12px 20px;
            color: #F9F5ED;
            text-decoration: none;
            transition: all 0.2s;
            font-size: 14px;
            cursor: pointer;
        }

        .dropdown-menu a:hover {
            background: #5E83AE;
        }

        /* Самолётик */
        .plane-icon-header {
            font-size: 28px;
            background: rgba(255, 255, 255, 0.2);
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .header-info h1 {
            color: white;
            font-size: 1.8rem;
            font-weight: 700;
            letter-spacing: -0.3px;
        }

        .header-info p {
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.8rem;
        }

        /* Контейнер с двумя колонками */
        .profile-container {
            display: flex;
            gap: 1.75rem;
            flex-wrap: wrap;
        }

        /* ЛЕВАЯ КОЛОНКА */
        .sidebar-card {
            flex: 1;
            min-width: 300px;
            background: #2A2A2A;
            border-radius: 32px;
            padding: 2rem 1.5rem;
            box-shadow: 0 12px 28px rgba(0,0,0,0.2);
            height: fit-content;
        }

        /* Аватар */
        .profile-avatar {
            text-align: center;
            margin-bottom: 1.5rem;
            position: relative;
        }

        .avatar-image {
            width: 120px;
            height: 120px;
            background: linear-gradient(135deg, #5E83AE 0%, #F9F5ED 100%);
            border-radius: 50%;
            margin: 0 auto 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            box-shadow: 0 8px 20px rgba(0,0,0,0.3);
            position: relative;
            cursor: pointer;
            transition: all 0.3s;
        }

        .avatar-image:hover .avatar-overlay {
            opacity: 1;
        }

        .avatar-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s;
            border-radius: 50%;
        }

        .avatar-overlay span {
            color: white;
            font-size: 14px;
            text-align: center;
        }

        .avatar-emoji {
            font-size: 52px;
            color: #2A2A2A;
        }

        .avatar-img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .profile-name {
            font-size: 1.5rem;
            font-weight: 700;
            color: #F9F5ED;
            margin-bottom: 0.25rem;
        }

        .profile-email {
            color: #5E83AE;
            font-size: 0.85rem;
            font-weight: 500;
            margin-bottom: 1.5rem;
        }

        /* Блок бюджета */
        .budget-block {
            background: rgba(94, 131, 174, 0.15);
            border-radius: 20px;
            padding: 1rem;
            text-align: center;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(94, 131, 174, 0.3);
        }

        .budget-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #5E83AE;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        .budget-amount {
            font-size: 1.8rem;
            font-weight: 700;
            color: #F9F5ED;
        }

        .budget-placeholder {
            font-size: 1.2rem;
            color: #888;
            font-weight: 400;
        }

        /* Статистика */
        .stats-grid {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .stat-card {
            flex: 1;
            text-align: center;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 0.75rem 0.5rem;
        }

        .stat-number {
            font-size: 1.4rem;
            font-weight: 700;
            color: #F9F5ED;
        }

        .stat-number-placeholder {
            font-size: 1rem;
            color: #888;
            font-weight: 400;
        }

        .stat-label {
            font-size: 0.7rem;
            color: #5E83AE;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 0.25rem;
        }

        /* Контакты */
        .contact-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 0;
            border-top: 1px solid rgba(249, 245, 237, 0.1);
            margin-top: 0.5rem;
        }

        .contact-icon {
            width: 32px;
            height: 32px;
            background: rgba(94, 131, 174, 0.25);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
        }

        .contact-info {
            flex: 1;
        }

        .contact-label {
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #5E83AE;
            font-weight: 600;
        }

        .contact-value {
            font-size: 0.85rem;
            font-weight: 500;
            color: #F9F5ED;
        }

        /* ПРАВАЯ КОЛОНКА */
        .main-content {
            flex: 2;
            min-width: 300px;
        }

        .top-bar {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .top-bar h2 {
            font-size: 1.5rem;
            font-weight: 600;
            color: #2A2A2A;
        }

        .info-section {
            background: #2A2A2A;
            border-radius: 28px;
            padding: 1.5rem;
            margin-bottom: 1.75rem;
            border: 1px solid rgba(249, 245, 237, 0.1);
        }

        .info-section h2 {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
            color: #F9F5ED;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #5E83AE;
            display: inline-block;
        }

        .field-group {
            margin-bottom: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .field-group label {
            font-weight: 600;
            color: #5E83AE;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .field-group input {
            background: #F9F5ED;
            border: 1px solid rgba(42,42,42,0.2);
            border-radius: 20px;
            padding: 12px 18px;
            font-size: 1rem;
            font-family: inherit;
            color: #2A2A2A;
            transition: all 0.2s;
        }

        .field-group input:focus {
            outline: none;
            border-color: #5E83AE;
            box-shadow: 0 0 0 3px rgba(94, 131, 174, 0.3);
        }

        .field-group input[type="number"] {
            -moz-appearance: textfield;
        }

        .field-group input[type="number"]::-webkit-inner-spin-button,
        .field-group input[type="number"]::-webkit-outer-spin-button {
            opacity: 0.5;
        }

        /* Стили для загрузки фото */
        .photo-upload {
            margin-bottom: 1.25rem;
        }

        .photo-label {
            display: inline-block;
            background: #5E83AE;
            color: #F9F5ED;
            padding: 10px 20px;
            border-radius: 40px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.2s;
        }

        .photo-label:hover {
            background: #6d95c2;
            transform: scale(0.98);
        }

        .photo-input {
            display: none;
        }

        .remove-photo {
            background: rgba(255, 255, 255, 0.1);
            color: #ff6b6b;
            border: 1px solid #ff6b6b;
            padding: 8px 16px;
            border-radius: 40px;
            cursor: pointer;
            font-size: 0.8rem;
            margin-left: 10px;
            transition: all 0.2s;
        }

        .remove-photo:hover {
            background: rgba(255, 107, 107, 0.2);
        }

        /* Стили для свитчей */
        .settings-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            margin-bottom: 1.25rem;
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(249, 245, 237, 0.1);
        }

        .settings-label {
            display: flex;
            align-items: center;
            gap: 14px;
            font-weight: 500;
            color: #F9F5ED;
        }

        .setting-icon {
            width: 32px;
            height: 32px;
            background: rgba(94, 131, 174, 0.25);
            border-radius: 10px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
        }

        /* Свитч */
        .switch {
            position: relative;
            display: inline-block;
            width: 52px;
            height: 28px;
        }

        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: 0.3s;
            border-radius: 34px;
        }

        .slider:before {
            position: absolute;
            content: "";
            height: 22px;
            width: 22px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: 0.3s;
            border-radius: 50%;
        }

        input:checked + .slider {
            background-color: #5E83AE;
        }

        input:checked + .slider:before {
            transform: translateX(24px);
        }

        .save-button {
            background: #5E83AE;
            color: #F9F5ED;
            border: none;
            border-radius: 40px;
            padding: 14px 28px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s;
            font-family: inherit;
        }

        .save-button:hover {
            background: #6d95c2;
            transform: scale(0.98);
        }

        .save-button.success {
            background: #2e7d32;
        }

        /* Модальное окно подтверждения */
        .confirm-modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.8);
            backdrop-filter: blur(5px);
            align-items: center;
            justify-content: center;
        }

        .confirm-modal-content {
            background: #2A2A2A;
            border-radius: 32px;
            max-width: 500px;
            width: 90%;
            padding: 2rem;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                transform: translateY(-50px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }

        .confirm-modal-content h2 {
            color: #F9F5ED;
            margin-bottom: 1.5rem;
            text-align: center;
        }

        .preview-data {
            background: rgba(94, 131, 174, 0.15);
            border-radius: 20px;
            padding: 1rem;
            margin-bottom: 1rem;
            max-height: 400px;
            overflow-y: auto;
        }

        .preview-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(249,245,237,0.1);
        }

        .preview-label {
            color: #5E83AE;
            font-weight: 600;
        }

        .preview-value {
            color: #F9F5ED;
        }

        .empty-value {
            color: #888;
            font-style: italic;
        }

        .modal-buttons {
            display: flex;
            gap: 1rem;
            margin-top: 1.5rem;
        }

        .confirm-btn {
            flex: 1;
            background: #5E83AE;
            color: white;
            border: none;
            padding: 12px;
            border-radius: 40px;
            cursor: pointer;
            font-weight: 600;
            font-size: 1rem;
        }

        .cancel-btn {
            flex: 1;
            background: rgba(255,255,255,0.1);
            color: #F9F5ED;
            border: 1px solid rgba(255,255,255,0.2);
            padding: 12px;
            border-radius: 40px;
            cursor: pointer;
            font-weight: 600;
            font-size: 1rem;
        }

        .cancel-btn:hover {
            background: rgba(255,255,255,0.2);
        }

        @media (max-width: 768px) {
            body { padding: 1rem; }
            .profile-container { flex-direction: column; }
            .sidebar-card { text-align: center; }
            .stats-grid { justify-content: center; }
            .header-content { flex-wrap: wrap; }
            .header-info h1 { font-size: 1.3rem; }
            .modal-buttons { flex-direction: column; }
        }
    </style>
</head>
<body>
<div class="main-wrapper">
    <!-- ШАПКА ПРОФИЛЯ -->
    <div class="profile-header">
        <div class="header-content">
            <div class="menu-container">
                <button class="menu-icon" onclick="toggleMenu()">
                    <span></span>
                    <span></span>
                    <span></span>
                </button>
                <div class="dropdown-menu" id="dropdownMenu">
                    <a href="#" onclick="document.querySelector('form').scrollIntoView({behavior: 'smooth'}); return false;">✏️ Редактировать профиль</a>
                    <a href="#" onclick="alert('Настройки уведомлений'); return false;">🔔 Уведомления</a>
                    <a href="#" onclick="alert('Конфиденциальность'); return false;">🔒 Конфиденциальность</a>
                    <a href="#" onclick="alert('Помощь'); return false;">❓ Помощь</a>
                </div>
            </div>

            <div class="plane-icon-header">✈️</div>

            <div class="header-info">
                <h1>TravelPlanner</h1>
                <p>Ваш личный гид в путешествиях</p>
            </div>
        </div>
    </div>

    <div class="profile-container">
        <!-- ЛЕВАЯ КОЛОНКА -->
        <div class="sidebar-card">
            <div class="profile-avatar">
                <div class="avatar-image" onclick="document.getElementById('avatarInput').click()">
                    {% if user.avatar %}
                        <img src="{{ url_for('uploaded_file', filename=user.avatar) }}" alt="Avatar" class="avatar-img">
                    {% else %}
                        <div class="avatar-emoji">🌍</div>
                    {% endif %}
                    <div class="avatar-overlay">
                        <span>✏️ Изменить</span>
                    </div>
                </div>
                <div class="profile-name">Путешественник</div>
                <div class="profile-email" id="leftEmail">{{ user.email }}</div>
            </div>

            <div class="budget-block">
                <div class="budget-label">Общий бюджет</div>
                <div class="budget-amount" id="leftBudget">
                    {% if user.budget and user.budget != '' %}
                        {{ "{:,.0f}".format(user.budget|int).replace(',', ' ') }} ₽
                    {% else %}
                        <span class="budget-placeholder">—</span>
                    {% endif %}
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="leftTotalTrips">
                        {% if user.total_trips and user.total_trips != '' %}
                            {{ user.total_trips }}
                        {% else %}
                            <span class="stat-number-placeholder">—</span>
                        {% endif %}
                    </div>
                    <div class="stat-label">всего поездок</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="leftCompletedTrips">
                        {% if user.completed_trips and user.completed_trips != '' %}
                            {{ user.completed_trips }}
                        {% else %}
                            <span class="stat-number-placeholder">—</span>
                        {% endif %}
                    </div>
                    <div class="stat-label">Завершено</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="leftPlacesVisited">
                        {% if user.places_visited and user.places_visited != '' %}
                            {{ user.places_visited }}
                        {% else %}
                            <span class="stat-number-placeholder">—</span>
                        {% endif %}
                    </div>
                    <div class="stat-label">Посещено мест</div>
                </div>
            </div>

            <div class="contact-item">
                <div class="contact-icon">📱</div>
                <div class="contact-info">
                    <div class="contact-label">ТЕЛЕФОН</div>
                    <div class="contact-value" id="leftPhone">{{ user.phone or 'Не указан' }}</div>
                </div>
            </div>
            <div class="contact-item">
                <div class="contact-icon">📍</div>
                <div class="contact-info">
                    <div class="contact-label">ГОРОД</div>
                    <div class="contact-value" id="leftCity">{{ user.city or 'Не указан' }}</div>
                </div>
            </div>
        </div>

        <!-- ПРАВАЯ КОЛОНКА -->
        <div class="main-content">
            <div class="top-bar">
                <h2>Настройки профиля</h2>
            </div>

            <form id="profileForm" method="POST" enctype="multipart/form-data" onsubmit="event.preventDefault(); showConfirmModal();">
                <div class="info-section">
                    <h2>Редактировать профиль</h2>

                    <div class="photo-upload">
                        <label class="photo-label">
                            📷 Загрузить фото профиля
                            <input type="file" name="avatar" id="avatarInput" class="photo-input" accept="image/*" onchange="previewAvatar(this)">
                        </label>
                        {% if user.avatar %}
                            <button type="button" class="remove-photo" onclick="removeAvatar()">🗑️ Удалить фото</button>
                        {% endif %}
                        <input type="hidden" name="remove_avatar" id="removeAvatarInput" value="0">
                    </div>

                    <div class="field-group">
                        <label>Email</label>
                        <input type="email" name="email" id="emailInput" value="{{ user.email }}" placeholder="your@email.com">
                    </div>

                    <div class="field-group">
                        <label>Телефон</label>
                        <input type="tel" name="phone" id="phoneInput" value="{{ user.phone }}" placeholder="+7 (___) ___-__-__">
                    </div>

                    <div class="field-group">
                        <label>Город</label>
                        <input type="text" name="city" id="cityInput" value="{{ user.city }}" placeholder="Ваш город">
                    </div>

                    <div class="field-group">
                        <label>Общий бюджет (₽)</label>
                        <input type="number" name="budget" id="budgetInput" value="{{ user.budget if user.budget else '' }}" placeholder="Например: 500000">
                    </div>

                    <div class="field-group">
                        <label>Всего поездок</label>
                        <input type="number" name="total_trips" id="totalTripsInput" value="{{ user.total_trips if user.total_trips else '' }}" placeholder="Количество поездок">
                    </div>

                    <div class="field-group">
                        <label>Завершено поездок</label>
                        <input type="number" name="completed_trips" id="completedTripsInput" value="{{ user.completed_trips if user.completed_trips else '' }}" placeholder="Завершено">
                    </div>

                    <div class="field-group">
                        <label>Посещено мест</label>
                        <input type="number" name="places_visited" id="placesVisitedInput" value="{{ user.places_visited if user.places_visited else '' }}" placeholder="Мест">
                    </div>
                </div>

                <div class="info-section">
                    <h2>Настройки</h2>

                    <div class="settings-item">
                        <div class="settings-label">
                            <div class="setting-icon">🔔</div>
                            <span>Уведомления</span>
                        </div>
                        <label class="switch">
                            <input type="checkbox" name="notifications" id="notificationsSwitch" {% if user.notifications %}checked{% endif %}>
                            <span class="slider"></span>
                        </label>
                    </div>

                    <div class="settings-item">
                        <div class="settings-label">
                            <div class="setting-icon">💾</div>
                            <span>Сохранение данных</span>
                        </div>
                        <label class="switch">
                            <input type="checkbox" name="data_saving" id="dataSavingSwitch" {% if user.data_saving %}checked{% endif %}>
                            <span class="slider"></span>
                        </label>
                    </div>

                    <div class="settings-item">
                        <div class="settings-label">
                            <div class="setting-icon">✉️</div>
                            <span>Email-оповещения</span>
                        </div>
                        <label class="switch">
                            <input type="checkbox" name="email_alerts" id="emailAlertsSwitch" {% if user.email_alerts %}checked{% endif %}>
                            <span class="slider"></span>
                        </label>
                    </div>
                </div>

                <button type="submit" class="save-button" id="saveButton">💾 Сохранить изменения</button>
            </form>
        </div>
    </div>
</div>

<!-- Модальное окно подтверждения -->
<div id="confirmModal" class="confirm-modal">
    <div class="confirm-modal-content">
        <h2>📋 Проверьте данные</h2>
        <div class="preview-data">
            <div class="preview-row">
                <span class="preview-label">Email:</span>
                <span class="preview-value" id="previewEmail"></span>
            </div>
            <div class="preview-row">
                <span class="preview-label">Телефон:</span>
                <span class="preview-value" id="previewPhone"></span>
            </div>
            <div class="preview-row">
                <span class="preview-label">Город:</span>
                <span class="preview-value" id="previewCity"></span>
            </div>
            <div class="preview-row">
                <span class="preview-label">Бюджет:</span>
                <span class="preview-value" id="previewBudget"></span>
            </div>
            <div class="preview-row">
                <span class="preview-label">Всего поездок:</span>
                <span class="preview-value" id="previewTotalTrips"></span>
            </div>
            <div class="preview-row">
                <span class="preview-label">Завершено:</span>
                <span class="preview-value" id="previewCompletedTrips"></span>
            </div>
            <div class="preview-row">
                <span class="preview-label">Посещено мест:</span>
                <span class="preview-value" id="previewPlacesVisited"></span>
            </div>
            <div class="preview-row">
                <span class="preview-label">Уведомления:</span>
                <span class="preview-value" id="previewNotifications"></span>
            </div>
            <div class="preview-row">
                <span class="preview-label">Сохранение данных:</span>
                <span class="preview-value" id="previewDataSaving"></span>
            </div>
            <div class="preview-row">
                <span class="preview-label">Email-оповещения:</span>
                <span class="preview-value" id="previewEmailAlerts"></span>
            </div>
        </div>
        <div class="modal-buttons">
            <button class="cancel-btn" onclick="closeConfirmModal()">✖️ Отмена</button>
            <button class="confirm-btn" onclick="submitForm()">✅ Подтвердить</button>
        </div>
    </div>
</div>

<script>
    // Выпадающее меню
    function toggleMenu() {
        const menu = document.getElementById('dropdownMenu');
        menu.classList.toggle('show');
    }

    window.onclick = function(event) {
        if (!event.target.matches('.menu-icon') && !event.target.closest('.menu-icon')) {
            const dropdowns = document.getElementsByClassName('dropdown-menu');
            for (let i = 0; i < dropdowns.length; i++) {
                if (dropdowns[i].classList.contains('show')) {
                    dropdowns[i].classList.remove('show');
                }
            }
        }
    }

    // Предпросмотр фото
    function previewAvatar(input) {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const avatarDiv = document.querySelector('.avatar-image');
                avatarDiv.innerHTML = '<img src="' + e.target.result + '" alt="Avatar" class="avatar-img"><div class="avatar-overlay"><span>✏️ Изменить</span></div>';
            }
            reader.readAsDataURL(input.files[0]);
        }
    }

    // Удалить фото
    function removeAvatar() {
        document.getElementById('removeAvatarInput').value = '1';
        const avatarDiv = document.querySelector('.avatar-image');
        avatarDiv.innerHTML = '<div class="avatar-emoji">🌍</div><div class="avatar-overlay"><span>✏️ Изменить</span></div>';
        document.getElementById('avatarInput').value = '';
    }

    // Форматирование значения
    function formatValue(value) {
        if (!value || value.toString().trim() === '') {
            return '<span class="empty-value">Не указано</span>';
        }
        return value;
    }

    // Показать модальное окно
    function showConfirmModal() {
        const email = document.getElementById('emailInput').value || 'Не указан';
        const phone = document.getElementById('phoneInput').value || 'Не указан';
        const city = document.getElementById('cityInput').value || 'Не указан';
        let budget = document.getElementById('budgetInput').value;
        let totalTrips = document.getElementById('totalTripsInput').value;
        let completedTrips = document.getElementById('completedTripsInput').value;
        let placesVisited = document.getElementById('placesVisitedInput').value;

        const budgetDisplay = (budget === '') ? 'Не указано' : Number(budget).toLocaleString('ru-RU') + ' ₽';
        const totalTripsDisplay = (totalTrips === '') ? 'Не указано' : totalTrips;
        const completedTripsDisplay = (completedTrips === '') ? 'Не указано' : completedTrips;
        const placesVisitedDisplay = (placesVisited === '') ? 'Не указано' : placesVisited;

        const notifications = document.getElementById('notificationsSwitch').checked ? '✅ Включено' : '❌ Выключено';
        const dataSaving = document.getElementById('dataSavingSwitch').checked ? '✅ Включено' : '❌ Выключено';
        const emailAlerts = document.getElementById('emailAlertsSwitch').checked ? '✅ Включено' : '❌ Выключено';

        document.getElementById('previewEmail').innerHTML = formatValue(email);
        document.getElementById('previewPhone').innerHTML = formatValue(phone);
        document.getElementById('previewCity').innerHTML = formatValue(city);
        document.getElementById('previewBudget').innerHTML = budgetDisplay;
        document.getElementById('previewTotalTrips').innerHTML = totalTripsDisplay;
        document.getElementById('previewCompletedTrips').innerHTML = completedTripsDisplay;
        document.getElementById('previewPlacesVisited').innerHTML = placesVisitedDisplay;
        document.getElementById('previewNotifications').innerHTML = notifications;
        document.getElementById('previewDataSaving').innerHTML = dataSaving;
        document.getElementById('previewEmailAlerts').innerHTML = emailAlerts;

        document.getElementById('confirmModal').style.display = 'flex';
    }

    function closeConfirmModal() {
        document.getElementById('confirmModal').style.display = 'none';
    }

    function submitForm() {
        const form = document.getElementById('profileForm');
        closeConfirmModal();
        form.submit();
    }

    window.onload = function() {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('saved') === '1') {
            const saveBtn = document.getElementById('saveButton');
            const originalText = saveBtn.innerHTML;
            saveBtn.innerHTML = '✅ Изменения сохранены!';
            saveBtn.classList.add('success');
            setTimeout(() => {
                saveBtn.innerHTML = originalText;
                saveBtn.classList.remove('success');
                const newUrl = window.location.pathname;
                window.history.pushState({}, document.title, newUrl);
            }, 3000);
        }
    }
</script>
</body>
</html>
"""


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/', methods=['GET', 'POST'])
def profile():
    global user_data

    if request.method == 'POST':
        # Обработка загрузки фото
        remove_avatar = request.form.get('remove_avatar', '0') == '1'

        if remove_avatar and user_data['avatar']:
            # Удаляем старый файл
            old_avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], user_data['avatar'])
            if os.path.exists(old_avatar_path):
                os.remove(old_avatar_path)
            user_data['avatar'] = None

        # Загрузка нового фото
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename and allowed_file(file.filename):
                # Удаляем старый файл если есть
                if user_data['avatar']:
                    old_avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], user_data['avatar'])
                    if os.path.exists(old_avatar_path):
                        os.remove(old_avatar_path)

                # Сохраняем новый файл
                filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                user_data['avatar'] = filename

        # Сохраняем остальные данные
        email = request.form.get('email', 'traveler@example.com')
        phone = request.form.get('phone', '')
        city = request.form.get('city', '')

        budget_str = request.form.get('budget', '').strip()
        total_trips_str = request.form.get('total_trips', '').strip()
        completed_trips_str = request.form.get('completed_trips', '').strip()
        places_visited_str = request.form.get('places_visited', '').strip()

        user_data['budget'] = budget_str if budget_str else ''
        user_data['total_trips'] = total_trips_str if total_trips_str else ''
        user_data['completed_trips'] = completed_trips_str if completed_trips_str else ''
        user_data['places_visited'] = places_visited_str if places_visited_str else ''

        if user_data['total_trips'] and user_data['completed_trips']:
            if int(user_data['completed_trips']) > int(user_data['total_trips']):
                user_data['completed_trips'] = user_data['total_trips']

        user_data['email'] = email
        user_data['phone'] = phone
        user_data['city'] = city
        user_data['notifications'] = 'notifications' in request.form
        user_data['data_saving'] = 'data_saving' in request.form
        user_data['email_alerts'] = 'email_alerts' in request.form
        return redirect(url_for('profile', saved=1))

    return render_template_string(HTML_TEMPLATE, user=user_data)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)