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
            avatarDiv.innerHTML = '<img src="' + e.target.result + '" alt="Avatar" class="avatar-img"></div>';
        }
        reader.readAsDataURL(input.files[0]);
    }
}

function removeAvatar() {
    document.getElementById('removeAvatarInput').value = '1';
    document.getElementById('avatarInput').value = '';
}


document.addEventListener('click', function(event) {
    const menu = document.getElementById('settingsDropdownMenu');
    const indicator = document.querySelector('.settings-indicator');
    if (menu && indicator && !indicator.contains(event.target)) {
        menu.classList.remove('show');
    }
});


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
}

document.addEventListener('input', function(e) {
    if (e.target.matches('#emailInput, #phoneInput, #cityInput, #budgetInput')) {
        updateLeftColumn();
    }
});