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

function removeAvatar() {
    document.getElementById('removeAvatarInput').value = '1';
    const avatarDiv = document.querySelector('.avatar-image');
    avatarDiv.innerHTML = '<div class="avatar-emoji">🌍</div><div class="avatar-overlay"><span>✏️ Изменить</span></div>';
    document.getElementById('avatarInput').value = '';
}


function toggleSettingsMenu(event) {
    event.stopPropagation();
    const menu = document.getElementById('settingsDropdownMenu');
    menu.classList.toggle('show');
}

document.addEventListener('click', function(event) {
    const menu = document.getElementById('settingsDropdownMenu');
    const indicator = document.querySelector('.settings-indicator');
    if (menu && indicator && !indicator.contains(event.target)) {
        menu.classList.remove('show');
    }
});

function editProfileOnly() {
    document.getElementById('editTypeInput').value = 'profile';
    document.getElementById('profileForm').scrollIntoView({behavior: 'smooth'});
    document.getElementById('settingsDropdownMenu').classList.remove('show');

    const fields = ['emailInput', 'phoneInput', 'cityInput'];
    fields.forEach(id => {
        const field = document.getElementById(id);
        field.style.borderColor = '#5E83AE';
        field.style.boxShadow = '0 0 0 3px rgba(94, 131, 174, 0.3)';
        setTimeout(() => {
            field.style.borderColor = '';
            field.style.boxShadow = '';
        }, 3000);
    });
    showNotification('Режим: редактирование профиля', 'info');
}

function editPhotoOnly() {
    document.getElementById('editTypeInput').value = 'photo';
    document.getElementById('settingsDropdownMenu').classList.remove('show');
    document.getElementById('avatarInput').click();
    showNotification('Выберите новое фото', 'info');
}

function editChecklistOnly() {
    document.getElementById('editTypeInput').value = 'checklist';
    document.getElementById('profileForm').scrollIntoView({behavior: 'smooth'});
    document.getElementById('settingsDropdownMenu').classList.remove('show');

    const fields = ['budgetInput', 'totalTripsInput', 'completedTripsInput', 'placesVisitedInput'];
    fields.forEach(id => {
        const field = document.getElementById(id);
        field.style.borderColor = '#FFD700';
        field.style.boxShadow = '0 0 0 3px rgba(255, 215, 0, 0.3)';
        setTimeout(() => {
            field.style.borderColor = '';
            field.style.boxShadow = '';
        }, 3000);
    });
    showNotification('Режим: редактирование чек-листа', 'info');
}

function resetAllSettings() {
    if (confirm('Вы уверены, что хотите сбросить все изменения?')) {
        document.getElementById('settingsDropdownMenu').classList.remove('show');

        fetch('/reset_edit_flags', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        }).then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const indicator = document.getElementById('settingsIndicator');
                if (indicator) {
                    indicator.style.animation = 'slideOut 0.3s ease forwards';
                    setTimeout(() => {
                        indicator.style.display = 'none';
                    }, 300);
                }
                showNotification('Все изменения сброшены', 'success');
            }
        });
    }
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

function refreshData() {
    const btn = document.querySelector('.refresh-btn');
    btn.style.transform = 'rotate(360deg)';

    fetch('/get_edit_status')
        .then(response => response.json())
        .then(data => {
            if (data.profile_edited) {
                showNotification('Данные обновлены', 'success');
            } else {
                showNotification('Нет новых изменений', 'info');
            }
        })
        .finally(() => {
            setTimeout(() => {
                btn.style.transform = 'rotate(0deg)';
            }, 500);
        });
}

function exportData() {
    const data = {
        email: document.getElementById('emailInput').value,
        phone: document.getElementById('phoneInput').value,
        city: document.getElementById('cityInput').value,
        budget: document.getElementById('budgetInput').value,
        totalTrips: document.getElementById('totalTripsInput').value,
        completedTrips: document.getElementById('completedTripsInput').value,
        placesVisited: document.getElementById('placesVisitedInput').value,
        notifications: document.getElementById('notificationsSwitch').checked,
        dataSaving: document.getElementById('dataSavingSwitch').checked,
        emailAlerts: document.getElementById('emailAlertsSwitch').checked
    };

    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'profile_data.json';
    a.click();
    URL.revokeObjectURL(url);

    showNotification('Данные экспортированы', 'success');
}

function confirmReset() {
    if (confirm('⚠️ Вы уверены, что хотите сбросить все данные?')) {
        document.getElementById('emailInput').value = '';
        document.getElementById('phoneInput').value = '';
        document.getElementById('cityInput').value = '';
        document.getElementById('budgetInput').value = '';
        document.getElementById('totalTripsInput').value = '';
        document.getElementById('completedTripsInput').value = '';
        document.getElementById('placesVisitedInput').value = '';
        document.getElementById('notificationsSwitch').checked = false;
        document.getElementById('dataSavingSwitch').checked = false;
        document.getElementById('emailAlertsSwitch').checked = false;

        showNotification('Все данные сброшены', 'warning');
    }
}

function showNotifications() {
    const modal = document.getElementById('infoModal');
    document.getElementById('infoModalTitle').textContent = '🔔 Настройки уведомлений';
    document.getElementById('infoModalContent').innerHTML = `
        <div style="color: #F9F5ED;">
            <p><strong>Настройки уведомлений:</strong></p>
            <br>
            <p>📧 Email уведомления: ${document.getElementById('emailAlertsSwitch').checked ? '✅ Включены' : '❌ Выключены'}</p>
            <p>🔔 Push уведомления: ${document.getElementById('notificationsSwitch').checked ? '✅ Включены' : '❌ Выключены'}</p>
            <br>
            <p style="color: #5E83AE; font-size: 14px;">Вы можете изменить настройки в разделе "Настройки" ниже</p>
        </div>
    `;
    modal.style.display = 'flex';
}

function showPrivacy() {
    const modal = document.getElementById('infoModal');
    document.getElementById('infoModalTitle').textContent = '🔒 Конфиденциальность';
    document.getElementById('infoModalContent').innerHTML = `
        <div style="color: #F9F5ED;">
            <p><strong>Настройки конфиденциальности:</strong></p>
            <br>
            <p>📊 Сохранение данных: ${document.getElementById('dataSavingSwitch').checked ? '✅ Включено' : '❌ Выключено'}</p>
            <p>🔐 Ваши данные защищены и не передаются третьим лицам</p>
            <br>
            <p style="color: #5E83AE; font-size: 14px;">Вы можете изменить настройки в разделе "Настройки" ниже</p>
        </div>
    `;
    modal.style.display = 'flex';
}

function showHelp() {
    const modal = document.getElementById('infoModal');
    document.getElementById('infoModalTitle').textContent = '❓ Помощь';
    document.getElementById('infoModalContent').innerHTML = `
        <div style="color: #F9F5ED;">
            <p><strong>Как пользоваться профилем:</strong></p>
            <br>
            <p>✏️ <strong>Редактировать профиль</strong> - изменить email, телефон, город</p>
            <p>✅ <strong>Чек-лист</strong> - бюджет, поездки, места</p>
            <p>📷 <strong>Фото</strong> - загрузить или удалить аватар</p>
            <p>⚙️ <strong>Настройки</strong> - уведомления, сохранение данных</p>
            <br>
            <p style="color: #5E83AE; font-size: 14px;">После сохранения появится значок настроек ⚙️</p>
        </div>
    `;
    modal.style.display = 'flex';
}

function closeInfoModal() {
    document.getElementById('infoModal').style.display = 'none';
}

function showNotification(message, type = 'info') {
    const existing = document.querySelector('.notification');
    if (existing) {
        existing.remove();
    }

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

window.onload = function() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('saved') === '1') {
        const saveBtn = document.getElementById('saveButton');
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '✅ Изменения сохранены!';
        saveBtn.classList.add('success');
        showNotification('Профиль успешно сохранен!', 'success');

        setTimeout(() => {
            saveBtn.innerHTML = originalText;
            saveBtn.classList.remove('success');
            const newUrl = window.location.pathname;
            window.history.pushState({}, document.title, newUrl);
        }, 3000);
    }

    document.querySelectorAll('.confirm-modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.style.display = 'none';
            }
        });
    });
};

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

    const totalTrips = document.getElementById('totalTripsInput').value;
    const leftTotalTrips = document.getElementById('leftTotalTrips');
    if (totalTrips) {
        leftTotalTrips.textContent = totalTrips;
    } else {
        leftTotalTrips.innerHTML = '<span class="stat-number-placeholder">—</span>';
    }

    const completedTrips = document.getElementById('completedTripsInput').value;
    const leftCompletedTrips = document.getElementById('leftCompletedTrips');
    if (completedTrips) {
        leftCompletedTrips.textContent = completedTrips;
    } else {
        leftCompletedTrips.innerHTML = '<span class="stat-number-placeholder">—</span>';
    }

    const placesVisited = document.getElementById('placesVisitedInput').value;
    const leftPlacesVisited = document.getElementById('leftPlacesVisited');
    if (placesVisited) {
        leftPlacesVisited.textContent = placesVisited;
    } else {
        leftPlacesVisited.innerHTML = '<span class="stat-number-placeholder">—</span>';
    }
}

document.addEventListener('input', function(e) {
    if (e.target.matches('#emailInput, #phoneInput, #cityInput, #budgetInput, #totalTripsInput, #completedTripsInput, #placesVisitedInput')) {
        updateLeftColumn();
    }
});