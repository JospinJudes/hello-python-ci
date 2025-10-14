# test_signin.py
from flask_auth.project.models import User
from werkzeug.security import generate_password_hash

def create_user(app, email="carol@example.com", name="Carol", password="Pwd!234"):
    from flask_auth.project import db
    with app.app_context():
        user = User(
            email=email,
            name=name,
            password=generate_password_hash(password, method="pbkdf2:sha256")
        )
        db.session.add(user)
        db.session.commit()
        return user

def test_login_page_get(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Connexion" in resp.data or b"login" in resp.data.lower()

def test_login_success_redirects_to_profile(app, client):
    create_user(app, email="dave@example.com", password="TopSecret!")
    resp = client.post("/login", data={
        "email": "dave@example.com",
        "password": "TopSecret!"
    }, follow_redirects=False)
    assert resp.status_code in (301, 302)

def test_login_invalid_credentials_keeps_user_on_login(app, client):
    # Création d’un utilisateur valide
    create_user(app, email="erin@example.com", password="Correct#1")

    # Tentative de connexion avec un mauvais mot de passe
    resp = client.post("/login", data={
        "email": "erin@example.com",
        "password": "WrongPwd"
    }, follow_redirects=True)

    # La page de login est renvoyée (échec d'authentification)
    assert resp.status_code == 200
    assert b"<!-- templates/login.html -->" in resp.data or b"<form" in resp.data

    # Vérifie qu'on ne peut pas accéder à /profile sans être connecté
    resp_profile = client.get("/profile", follow_redirects=False)
    assert resp_profile.status_code in (301, 302)
    assert "/login" in resp_profile.headers.get("Location", "")

def test_logout_requires_login_and_redirects(client, app):
    # non connecté -> Flask-Login redirige vers la page de login
    resp = client.get("/logout", follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers.get("Location", "")

def test_access_protected_profile_requires_auth_then_succeeds(client, app):
    # 1) non connecté -> redirection
    resp = client.get("/profile", follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers.get("Location", "")

    # 2) connexion
    create_user(app, email="frank@example.com", password="Pa$$w0rd")
    client.post("/login", data={
        "email": "frank@example.com",
        "password": "Pa$$w0rd"
    }, follow_redirects=True)

    # 3) accès OK
    resp2 = client.get("/profile")
    assert resp2.status_code == 200
    assert b"frank" in resp2.data.lower() or b"profile" in resp2.data.lower()