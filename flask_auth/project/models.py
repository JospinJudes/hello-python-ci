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
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
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

