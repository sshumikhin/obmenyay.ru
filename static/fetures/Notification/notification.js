export const showNotification = (message,type = 'error') => {
    const notification = document.getElementById('notification');
    notification.textContent = message;

    if (type === 'success') {
        notification.classList.add('success');
    } else {
        notification.classList.remove('success');
    }

    notification.style.display = 'block';
    notification.style.opacity = '1';

    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            notification.style.display = 'none';
        }, 500);
    }, 4000);
};
