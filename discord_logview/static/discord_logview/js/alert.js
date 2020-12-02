window.addEventListener('DOMContentLoaded', (event) => {
    document.querySelectorAll('.alert').forEach((alert) => {
        setTimeout(function () {
            alert.classList.add('disappearing');
            setTimeout(function () {
                alert.remove();
            }, 1000);
        }, 5000);
    });

    document.querySelectorAll('.alert time').forEach((time) => {
        time.innerHTML = moment(time.getAttribute('datetime')).format('dddd, MMMM DD, YYYY [at] HH:mm:ss');
    })
});