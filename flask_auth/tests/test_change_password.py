# flask_auth/tests/test_change_password.py
import pytest
from werkzeug.security import check_password_hash
from flask import url_for
from flask_auth.project.models import User

# ------------------------
# Helpers
# ------------------------
def signup(client, email="user@example.com", name="User", password="Abcdef1!"):
    return client.post("/signup", data={
        "email": email, "name": name, "password": password
    }, follow_redirects=True)

def login(client, email="user@example.com", password="Abcdef1!"):
    return client.post("/login", data={
        "email": email, "password": password
    }, follow_redirects=True)

# ------------------------
# Access control
# ------------------------
def test_password_page_requires_login(client):
    # GET non authentifié -> redirection vers /login
    resp = client.get("/password", follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert "/login" in (resp.headers.get("Location") or "")

def test_password_post_requires_login(client):
    resp = client.post("/password", data={
        "current_password": "Abcdef1!", "new_password": "Newpass1!"
    }, follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert "/login" in (resp.headers.get("Location") or "")

# ------------------------
# UI: Cancel link present
# ------------------------
def test_password_page_shows_cancel_link(app, client):
    signup(client)
    login(client)
    resp = client.get("/password")
    assert resp.status_code == 200
    # lien de retour profil (ajuste si tu renvoies ailleurs)
    assert b'href="' in resp.data and b"/profile" in resp.data

# ------------------------
# Scénarios de la User Story
# ------------------------
def test_successful_password_change_updates_hash_and_confirms(app, client):
    signup(client)
    login(client)

    resp = client.post("/password", data={
        "current_password": "Abcdef1!",
        "new_password": "Newpass1!"
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"Password successfully changed" in resp.data

    # vérifie en base: mot de passe réellement modifié
    with app.app_context():
        u = User.query.filter_by(email="user@example.com").first()
        assert u is not None
        assert check_password_hash(u.password, "Newpass1!")
        assert not check_password_hash(u.password, "Abcdef1!")  # ancien n'est plus valable

def test_incorrect_current_password_shows_error(app, client):
    signup(client)
    login(client)

    resp = client.post("/password", data={
        "current_password": "WrongNow!",
        "new_password": "Newpass1!"
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"Current password is incorrect" in resp.data

def test_invalid_new_password_shows_policy_error(client):
    signup(client)
    login(client)

    # Trop court et manque majuscule/spécial etc.
    resp = client.post("/password", data={
        "current_password": "Abcdef1!",
        "new_password": "a1!"  # invalide
    }, follow_redirects=True)

    assert resp.status_code == 200
    # on accepte toute erreur de la politique (au moins l'une des phrases)
    body = resp.data
    assert (b"6 caract" in body) or (b"majuscule" in body) or (b"chiffre" in body) or (b"caract" in body)

def test_new_password_same_as_current_is_rejected(client):
    signup(client)
    login(client)

    resp = client.post("/password", data={
        "current_password": "Abcdef1!",
        "new_password": "Abcdef1!"  # identique
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"New password must be different from the current password" in resp.data

def test_missing_fields_are_rejected(client):
    signup(client)
    login(client)

    # current manquant
    resp1 = client.post("/password", data={
        "current_password": "", "new_password": "Newpass1!"
    }, follow_redirects=True)
    assert resp1.status_code == 200
    assert b"Please fill in both fields" in resp1.data

    # new manquant
    resp2 = client.post("/password", data={
        "current_password": "Abcdef1!", "new_password": ""
    }, follow_redirects=True)
    assert resp2.status_code == 200
    assert b"Please fill in both fields" in resp2.data

# ------------------------
# Post-condition: authentification toujours valide
# ------------------------
def test_still_logged_in_after_successful_change(client, app):
    signup(client)
    login(client)

    client.post("/password", data={
        "current_password": "Abcdef1!",
        "new_password": "Newpass1!"
    }, follow_redirects=True)

    # L'utilisateur doit pouvoir accéder au profil après changement
    resp = client.get("/profile")
    assert resp.status_code == 200
    assert b"@" in resp.data  # un bout du profil
