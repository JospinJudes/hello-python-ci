# models.py

from flask_login import UserMixin
from . import db
from datetime import datetime

# Table d'association pour le système de follow (Un utilisateur peut suivre plusieurs autres utilisateurs,Un utilisateur peut être suivi par plusieurs autres)
followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),# on relie ces colonnes à la colonne id de la table user
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    bio = db.Column(db.String(300))  
    tweets = db.relationship('Tweet', back_populates='user', lazy='dynamic')

    # Relation pour les follows
    followed = db.relationship(
        'User', 
        secondary=followers, 
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),# créer automatiquement une relation inverse (followers)
        lazy='dynamic'
    )

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user): #verifie si self suit user
        return self.followed.filter(
            followers.c.followed_id == user.id
        ).count() > 0
    
    def delete_follower(self,user):
        if user in self.followers:
            self.followers.remove(user)



#post
class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(280))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='tweets')

from flask_auth.project.models import User

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