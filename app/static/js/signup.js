const form = document.getElementById('register-form');
const successMessage = document.getElementById('success-message');
const fields = {
    csrf_token: {
        input: document.getElementById('csrf_token'),
        error: document.getElementById('csrf_token-error')
    },
    username: {
        input: document.getElementById('username'),
        error: document.getElementById('username-error')
    },
    email: {
        input: document.getElementById('email'),
        error: document.getElementById('email-error')
    },
    password: {
        input: document.getElementById('password'),
        error: document.getElementById('password-error')
    },
    password2: {
        input: document.getElementById('password2'),
        error: document.getElementById('password2-error')
    }
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const response = await fetch('/auth/register_ajax', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            csrf_token: fields.csrf_token.input.value,
            username: fields.username.input.value,
            email: fields.email.input.value,
            password: fields.password.input.value,
            password2: fields.password2.input.value
        })
    });
    if (response.ok) {
        successMessage.innerHTML = await response.text();
        form.style.display = 'none';
        successMessage.style.display = 'block';
    } else {
        const errors = await response.json();
        Object.keys(errors).forEach((key) => {
           fields[key].input.classList.add('is-invalid');
           fields[key].error.innerHTML = errors[key][0];
        });
    }
});