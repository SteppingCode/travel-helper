// Флаг наличия несохраненных изменений
let isDirty = false;

// Отслеживаем изменения во всех полях формы
document.querySelectorAll('#profileForm input').forEach(input => {
    const unsavedChangesIcon = document.getElementById('settings-indicator');
    input.addEventListener('input', () => {
        isDirty = true;
        unsavedChangesIcon.style.display = `block`;
    });
});


window.addEventListener('beforeunload', (event) => {
    if (isDirty) {
        event.preventDefault();
    }
});


function previewAvatar(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];

        if (!file.type.startsWith('image/')) {
            alert('Пожалуйста, выберите корректное изображение.');
            return;
        }

        const avatarImg = document.querySelector('.avatar-img');
        if (avatarImg) {
            avatarImg.src = URL.createObjectURL(file);
        }

        const modal = document.getElementById('infoModal');
        const modalTitle = document.getElementById('infoModalTitle');
        const modalContent = document.getElementById('infoModalContent');

        if (modal && modalTitle && modalContent) {
            modalTitle.innerText = "🔄 Аватар обновлен в предпросмотре";
            modalContent.innerHTML = `
                <div style="color: #F9F5ED; text-align: center; font-family: inherit;">
                    <p style="margin-bottom: 12px; font-weight: bold;">Вы успешно выбрали новое фото профиля!</p>
                    <p style="font-size: 13px; opacity: 0.9;">Обратите внимание: чтобы изменения сохранились на сервере навсегда, обязательно нажмите кнопку <strong>"Сохранить изменения"</strong> внизу формы.</p>
                </div>
            `;
            modal.style.display = `flex`;
        }
    }
}


document.getElementById('profileForm').addEventListener('submit', () => {
    isDirty = false;
    const unsavedChangesIcon = document.getElementById('settings-indicator');
    unsavedChangesIcon.style.display = `none`;
});


function removeAvatar() {
    document.getElementById('removeAvatarInput').value = '1';
    document.getElementById('avatarInput').value = '';
}


function formatValue(value) {
    if (!value || value.toString().trim() === '') {
        return '<span class="empty-value">Не указано</span>';
    }
    return value;
}


function showConfirmModal() {
    const email = document.getElementById('emailInput').value || 'Не указан';
    const phone = document.getElementById('phoneInput').value || 'Не указан';
    const city = document.getElementById('cityInput').value || 'Не указан';
    let budget = document.getElementById('budgetInput').value;

    const budgetDisplay = (budget === '') ? 'Не указано' : Number(budget).toLocaleString('ru-RU') + ' ₽';

    const emailAlerts = document.getElementById('emailAlertsSwitch').checked ? '✅ Включено' : '❌ Выключено';

    document.getElementById('previewEmail').innerHTML = formatValue(email);
    document.getElementById('previewPhone').innerHTML = formatValue(phone);
    document.getElementById('previewCity').innerHTML = formatValue(city);
    document.getElementById('previewBudget').innerHTML = budgetDisplay;
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


function closeInfoModal() {
    document.getElementById('infoModal').style.display = 'none';
}


function updateLeftColumn() {
    document.getElementById('leftEmail').textContent = document.getElementById('emailInput').value || 'Не указан';
    document.getElementById('leftPhone').textContent = document.getElementById('phoneInput').value || 'Не указан';
    document.getElementById('leftCity').textContent = document.getElementById('cityInput').value || 'Не указан';

    const budget = document.getElementById('budgetInput').value;
    const leftBudget = document.getElementById('leftBudget');
    if (budget) {
        leftBudget.innerHTML = Number(budget).toLocaleString('ru-RU') + ' ₽';
    } else {
        leftBudget.innerHTML = '<span class="budget-placeholder">—</span>';
    }
}

document.addEventListener('input', function(e) {
    if (e.target.matches('#emailInput, #phoneInput, #cityInput, #budgetInput')) {
        updateLeftColumn();
    }
});