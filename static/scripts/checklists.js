// Функция для проверки, был ли изменен элемент
function hasItemChanged(element) {
    const item = element.closest('.checklist-item');
    const checkbox = item.querySelector('input[type="checkbox"]');
    const textInput = item.querySelector('.user-data-input input');

    // Проверяем, был ли изменен чекбокс или текстовое поле
    return checkbox.defaultChecked !== checkbox.checked ||
        textInput.defaultValue !== textInput.value;
}

// Обработчик изменения чекбокса
function handleCheckboxChange(checkbox) {
    const item = checkbox.closest('.checklist-item');
    const label = item.querySelector('.item-text');

    // Обновляем стиль текста
    if (checkbox.checked) {
        label.classList.add('done');
    } else {
        label.classList.remove('done');
    }

    // Показываем иконку настроек
    showSettingsIcon(checkbox);
}

// Обработчик изменения текстового поля
function handleUserDataChange(input) {
    showSettingsIcon(input);
}

// Функция для показа иконки настроек
function showSettingsIcon(element) {
    const categoryCard = element.closest('.category-card');
    const settingsIcon = categoryCard.querySelector('.settings-icon');

    // Проверяем, есть ли изменения в этой категории
    const items = categoryCard.querySelectorAll('.checklist-item');
    let hasChanges = false;

    items.forEach(item => {
        if (hasItemChanged(item)) {
            hasChanges = true;
        }
    });

    // Показываем или скрываем иконку
    if (hasChanges) {
        settingsIcon.classList.add('show');
    } else {
        settingsIcon.classList.remove('show');
    }
}

// Проверяем все категории при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {
    const categoryCards = document.querySelectorAll('.category-card');
    categoryCards.forEach(card => {
        const items = card.querySelectorAll('.checklist-item');
        let hasChanges = false;

        items.forEach(item => {
            if (hasItemChanged(item)) {
                hasChanges = true;
            }
        });

        const settingsIcon = card.querySelector('.settings-icon');
        if (hasChanges) {
            settingsIcon.classList.add('show');
        }
    });
});