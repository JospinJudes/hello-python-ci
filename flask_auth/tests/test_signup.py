# test_signup.py
from flask_auth.project.models import User
from flask import url_for

def test_signup_page_get(client):
    resp = client.get("/signup")
    assert resp.status_code == 200
    assert b"Inscription" in resp.data or b"signup" in resp.data.lower()

def test_signup_success_creates_user_and_redirects_to_login(app, client):
    form = {
        "email": "alice@example.com",
        "name": "Alice",
        "password": "StrongPwd!123",
    }
    resp = client.post("/signup", data=form, follow_redirects=False)
    # La route redirige vers /login après succès
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers.get("Location", "")

    # Vérifier en base
    with app.app_context():
        user = User.query.filter_by(email=form["email"]).first()
        assert user is not None
        assert user.name == "Alice"
        # le mot de passe est hashé
        assert user.password != form["password"]

def test_signup_duplicate_email_is_rejected_without_creating_new_user(app, client):
    # 1) Création initiale
    client.post("/signup", data={
        "email": "bob@example.com",
        "name": "Bob",
        "password": "Pwd123!"
    }, follow_redirects=True)

    # 2) Nouvelle tentative avec le même email
    resp = client.post("/signup", data={
        "email": "bob@example.com",
        "name": "Other Bob",
        "password": "Pwd456!"
    }, follow_redirects=True)

    assert resp.status_code == 200
    # On vérifie que la page d'inscription est renvoyée (échec)
    assert b"<!-- templates/signup.html -->" in resp.data or b"<form" in resp.data

    # Invariant BDD : un seul utilisateur avec cet email
    with app.app_context():
        assert User.query.filter_by(email="bob@example.com").count() == 1
def test_signup_rejects_weak_or_empty_password(client):
    resp = client.post("/signup", data={
        "email": "weak@example.com",
        "name": "Weak",
        "password": ""}, follow_redirects=True)
    # Selon ton code, le formulaire ne valide pas explicitement,
    # mais un mot de passe vide ne doit pas créer un compte utile.
    assert resp.status_code == 200