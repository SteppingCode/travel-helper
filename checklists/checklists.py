from flask import Flask, render_template, request, redirect, url_for, session
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Initial checklist structure
initial_checklist = {
    'Документы и бронирования': [
        {'text': 'Проверить паспорт и визу', 'done': False, 'user_data': ''},
        {'text': 'Купить авиабилеты', 'done': False, 'user_data': ''},
        {'text': 'Забронировать отель', 'done': False, 'user_data': ''},
        {'text': 'Зарегистрироваться на рейс онлайн', 'done': False, 'user_data': ''},
        {'text': 'Распечатать посадочные талоны', 'done': False, 'user_data': ''},
        {'text': 'Проверить ограничения по багажу', 'done': False, 'user_data': ''}
    ],
    'Аптечка и здоровье': [
        {'text': 'Аптечка первой помощи', 'done': False, 'user_data': ''},
        {'text': 'Лекарства по рецепту', 'done': False, 'user_data': ''},
        {'text': 'Обезболивающие', 'done': False, 'user_data': ''},
        {'text': 'Средства от аллергии', 'done': False, 'user_data': ''}
    ],
    'Защита и гигиена': [
        {'text': 'Солнцезащитный крем', 'done': False, 'user_data': ''},
        {'text': 'Репелленты от насекомых', 'done': False, 'user_data': ''},
        {'text': 'Одежда по погоде', 'done': False, 'user_data': ''},
        {'text': 'Удобная обувь', 'done': False, 'user_data': ''},
        {'text': 'Туалетные принадлежности', 'done': False, 'user_data': ''}
    ],
    'Техника и зарядка': [
        {'text': 'Зарядные устройства', 'done': False, 'user_data': ''},
        {'text': 'Адаптеры для розеток', 'done': False, 'user_data': ''},
        {'text': 'Фотоаппарат или камера', 'done': False, 'user_data': ''}
    ],
    'Важные документы (с собой)': [
        {'text': 'Паспорт', 'done': False, 'user_data': ''},
        {'text': 'Виза или разрешение на въезд', 'done': False, 'user_data': ''},
        {'text': 'Копии документов', 'done': False, 'user_data': ''},
        {'text': 'Страховой полис', 'done': False, 'user_data': ''},
        {'text': 'Водительские права', 'done': False, 'user_data': ''},
        {'text': 'Бронь отеля', 'done': False, 'user_data': ''}
    ],
    'Перед выходом из дома': [
        {'text': 'Выключить электроприборы', 'done': False, 'user_data': ''},
        {'text': 'Закрыть окна и двери', 'done': False, 'user_data': ''},
        {'text': 'Полить растения', 'done': False, 'user_data': ''},
        {'text': 'Организовать уход за питомцами', 'done': False, 'user_data': ''},
        {'text': 'Перенаправить почту', 'done': False, 'user_data': ''},
        {'text': 'Проверить замки', 'done': False, 'user_data': ''}
    ]
}


def get_checklist():
    if 'checklist' not in session:
        session['checklist'] = json.dumps(initial_checklist)
    return json.loads(session['checklist'])


def save_checklist(checklist):
    session['checklist'] = json.dumps(checklist)


@app.route('/', methods=['GET', 'POST'])
def index():
    checklist = get_checklist()

    if request.method == 'POST':
        # Update checkbox states
        for category in checklist:
            for i, item in enumerate(checklist[category]):
                checkbox_key = f"{category}_{i}_done"
                if checkbox_key in request.form:
                    checklist[category][i]['done'] = True
                else:
                    checklist[category][i]['done'] = False

                # Update user data text
                data_key = f"{category}_{i}_data"
                if data_key in request.form:
                    checklist[category][i]['user_data'] = request.form[data_key]

        save_checklist(checklist)
        return redirect(url_for('index'))

    return render_template('index.html', checklist=checklist, enumerate=enumerate)


@app.route('/reset')
def reset():
    session['checklist'] = json.dumps(initial_checklist)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)