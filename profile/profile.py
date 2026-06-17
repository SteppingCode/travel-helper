from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
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
    'avatar': None,
    'profile_edited': False,
    'last_edit_type': None
}


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/')
def index():
    return render_template('profile.html', user=user_data)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    global user_data

    if request.method == 'POST':
        # Определяем тип изменения
        edit_type = request.form.get('edit_type', 'full')
        user_data['last_edit_type'] = edit_type

        # Обработка загрузки фото
        remove_avatar = request.form.get('remove_avatar', '0') == '1'
        avatar_updated = False

        if remove_avatar and user_data['avatar']:
            old_avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], user_data['avatar'])
            if os.path.exists(old_avatar_path):
                os.remove(old_avatar_path)
            user_data['avatar'] = None
            avatar_updated = True

        # Загрузка нового фото
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename and allowed_file(file.filename):
                if user_data['avatar']:
                    old_avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], user_data['avatar'])
                    if os.path.exists(old_avatar_path):
                        os.remove(old_avatar_path)

                filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                user_data['avatar'] = filename
                avatar_updated = True

        # Если обновляли только фото
        if edit_type == 'photo':
            if avatar_updated:
                user_data['profile_edited'] = True
            return redirect(url_for('profile', saved=1))

        # Если обновляем профиль полностью
        if edit_type == 'profile' or edit_type == 'full':
            # Сохраняем данные профиля
            email = request.form.get('email', 'traveler@example.com')
            phone = request.form.get('phone', '')
            city = request.form.get('city', '')

            budget_str = request.form.get('budget', '').strip()
            total_trips_str = request.form.get('total_trips', '').strip()
            completed_trips_str = request.form.get('completed_trips', '').strip()
            places_visited_str = request.form.get('places_visited', '').strip()

            user_data['email'] = email
            user_data['phone'] = phone
            user_data['city'] = city
            user_data['budget'] = budget_str if budget_str else ''
            user_data['total_trips'] = total_trips_str if total_trips_str else ''
            user_data['completed_trips'] = completed_trips_str if completed_trips_str else ''
            user_data['places_visited'] = places_visited_str if places_visited_str else ''

            if user_data['total_trips'] and user_data['completed_trips']:
                if int(user_data['completed_trips']) > int(user_data['total_trips']):
                    user_data['completed_trips'] = user_data['total_trips']

            user_data['notifications'] = 'notifications' in request.form
            user_data['data_saving'] = 'data_saving' in request.form
            user_data['email_alerts'] = 'email_alerts' in request.form

            user_data['profile_edited'] = True

        return redirect(url_for('profile', saved=1))

    return render_template('profile.html', user=user_data)


@app.route('/reset_edit_flags', methods=['POST'])
def reset_edit_flags():
    global user_data
    user_data['profile_edited'] = False
    user_data['last_edit_type'] = None
    return jsonify({'status': 'success'})


@app.route('/get_edit_status', methods=['GET'])
def get_edit_status():
    global user_data
    return jsonify({
        'profile_edited': user_data['profile_edited'],
        'last_edit_type': user_data['last_edit_type']
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)