from uuid import uuid4

import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_register_page_creates_user_and_stores_token(page, fastapi_server):
    suffix = uuid4().hex[:8]
    username = f'playwright_{suffix}'
    email = f'{username}@example.com'

    page.goto('http://127.0.0.1:8000/register')

    page.fill('#username', username)
    page.fill('#email', email)
    page.fill('#password', 'ValidPassword123')
    page.click('#register-form button[type="submit"]')

    expect(page.locator('#status')).to_contain_text(f'Registration successful for {username}.')
    token = page.evaluate("() => localStorage.getItem('access_token')")
    assert token is not None
    assert len(token.split('.')) == 3


@pytest.mark.e2e
def test_register_page_rejects_short_password_with_frontend_validation(page, fastapi_server):
    suffix = uuid4().hex[:8]
    username = f'pw_short_{suffix}'
    email = f'{username}@example.com'

    page.goto('http://127.0.0.1:8000/register')
    page.fill('#username', username)
    page.fill('#email', email)
    page.fill('#password', 'hi')
    page.click('#register-form button[type="submit"]')

    is_invalid = page.evaluate("""
        () => {
            const password = document.getElementById('password');
            return !password.checkValidity() && password.validationMessage.length > 0;
        }
    """)
    assert is_invalid is True

    token = page.evaluate("() => localStorage.getItem('access_token')")
    assert token is None


@pytest.mark.e2e
def test_login_page_accepts_email_identifier(page, fastapi_server):
    suffix = uuid4().hex[:8]
    username = f'login_playwright_{suffix}'
    email = f'{username}@example.com'

    page.goto('http://127.0.0.1:8000/register')
    page.fill('#username', username)
    page.fill('#email', email)
    page.fill('#password', 'ValidPassword123')
    page.click('#register-form button[type="submit"]')
    expect(page.locator('#status')).to_contain_text('Registration successful')

    page.goto('http://127.0.0.1:8000/login')
    page.fill('#identifier', email)
    page.fill('#password', 'ValidPassword123')
    page.click('#login-form button[type="submit"]')

    expect(page).to_have_url('http://127.0.0.1:8000/?logged_in=1')
    expect(page.locator('#auth-status')).to_have_text(f'Logged in as {username}.')
    user = page.evaluate("() => JSON.parse(localStorage.getItem('current_user'))")
    assert user['username'] == username


@pytest.mark.e2e
def test_login_page_shows_invalid_credentials(page, fastapi_server):
    page.goto('http://127.0.0.1:8000/login')

    page.fill('#identifier', 'missing_user')
    page.fill('#password', 'WrongPassword123')
    with page.expect_response(
        lambda response: response.url.endswith('/login') and response.status == 401
    ) as login_response:
        page.click('#login-form button[type="submit"]')

    assert login_response.value.status == 401

    expect(page.locator('#status')).to_have_text('Invalid username or password.')
