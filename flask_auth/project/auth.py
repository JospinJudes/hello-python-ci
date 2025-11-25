# auth.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from . import db
import re

def password_errors(password: str) -> list[str]:
    errors = []
    if password is None or password == "":
        errors.append("Password required.", category="error")
        return errors

    if len(password) < 6:
        errors.append("The password must contain at least 6 characters.", category="error")
    if not re.search(r"[A-Z]", password):
        errors.append("The password must contain at least one capital letter.", category="error")
    if not re.search(r"\d", password):
        errors.append("The password must contain at least one number.", category="error")
    if not re.search(r"[!@#$%^&*(),.?\":{}|]", password): 
        errors.append("The password must contain at least one special character.", category="error")

    return errors
auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    # check if required fields are missing
    if not email or not password:
        flash('Please complete all fields before proceeding.', category="error")
        return redirect(url_for('auth.login')) # reload the page

    user = User.query.filter_by(email=email).first()
    
    # check if user actually exists
    if not user:
        flash('No account found with this email address.', category="error")
        return redirect(url_for('auth.login')) # reload the page

    
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not user or not check_password_hash(user.password, password): 
        flash('Please check your login details and try again.', category="error")
        return redirect(url_for('auth.login')) # if user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('main.profile'))

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    # Vérification des champs vides
    if not email or not password:
        flash("Please complete all fields before proceeding.", category="error")
        return redirect(url_for('auth.signup'))
    
    # Vérification de l'existence de l'utilisateur
    user = User.query.filter_by(email=email).first()
    if user:

        flash("This email adress is already used", category="email_exists")
        return redirect(url_for('auth.signup'))
    
    # Validation des critères du mot de passe 
    errs = password_errors(password)
    if errs:
        for e in errs:
            flash(e, category="error")
        return redirect(url_for('auth.signup'))

    # ⚡ Utilisation correcte de pbkdf2:sha256
    new_user = User(
        email=email,
        name=name,
        password=generate_password_hash(password, method='pbkdf2:sha256')
    )

    db.session.add(new_user)
    db.session.commit()

    flash('Accound successfully created !', category="success")
    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/password', methods=['GET'])
@login_required
def password_page():
    """Affiche la page de changement de mot de passe"""
    return render_template('password.html')


@auth.route('/password', methods=['POST'])
@login_required
def password_post():
    current_pwd = request.form.get('current_password')
    new_pwd = request.form.get('new_password')

    # Vérif des champs
    if not current_pwd or not new_pwd:
        flash("Please fill in both fields.", category="error")
        return redirect(url_for('auth.password_page'))

    # Vérif du mot de passe actuel
    if not check_password_hash(current_user.password, current_pwd):
        flash("Current password is incorrect.", category="error")
        return redirect(url_for('auth.password_page'))

    # Refuser si identique
    if new_pwd == current_pwd:
        flash("New password must be different from the current password", category="error")
        return redirect(url_for('auth.password_page'))

    # Vérification des critères (réutilise ta fonction existante)
    errs = password_errors(new_pwd)
    if errs:
        for e in errs:
            flash(e, category="error")
        return redirect(url_for('auth.password_page'))

    # Mise à jour
    current_user.password = generate_password_hash(new_pwd, method='pbkdf2:sha256')
    db.session.commit()

    flash("Password successfully changed.", category="success")
    return redirect(url_for('main.profile'))