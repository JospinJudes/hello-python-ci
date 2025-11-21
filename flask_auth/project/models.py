# models.py

from flask_login import UserMixin
from . import db
from datetime import datetime
import json

# Table d'association pour le système de follow
followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

# Table d'association Tweet <-> Hashtag
tweet_hashtag = db.Table(
    'tweet_hashtag',
    db.Column('tweet_id', db.Integer, db.ForeignKey('tweet.id')),
    db.Column('hashtag_id', db.Integer, db.ForeignKey('hashtag.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    bio = db.Column(db.String(300))
    
    # Tweets de l'utilisateur
    tweets = db.relationship('Tweet', back_populates='user', lazy='dynamic')

    # Likes et commentaires
    likes = db.relationship('Like', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')

    # Relation pour les follows
    followed = db.relationship(
        'User',
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )

    # ====================
    # Méthodes de follow/unfollow
    # ====================
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def delete_follower(self, user):
        if user in self.followers:
            self.followers.remove(user)

    # ====================
    # Likes
    # ====================
    def has_liked(self, tweet):
        return Like.query.filter_by(user_id=self.id, tweet_id=tweet.id).count() > 0


# ====================
# Tweet
# ====================
class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(280))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    user = db.relationship('User', back_populates='tweets')
    likes = db.relationship('Like', backref='tweet', lazy='dynamic')
    comments = db.relationship('Comment', backref='tweet', lazy='dynamic')

    #  Relation avec les hashtags
    hashtags = db.relationship(
        'Hashtag',
        secondary=tweet_hashtag,
        back_populates='tweets',
        lazy='dynamic'
    )

    @property
    def likes_count(self):
        return self.likes.count()



# ====================
# Like
# ====================
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'), nullable=False)


# ====================
# Comment
# ====================
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'), nullable=False)

    @property
    def content_with_hashtags(self):
        import re
        from flask import url_for
        # Remplace #hashtag par lien cliquable
        def repl(match):
            tag = match.group(1)
            return f'<a href="{url_for("main.hashtag", tag=tag)}" class="hashtag">#{tag}</a>'
        return re.sub(r'#(\w+)', repl, self.content)





class Hashtag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(100), unique=True, nullable=False)

    # relation inverse vers les tweets
    tweets = db.relationship(
        'Tweet',
        secondary=tweet_hashtag,
        back_populates='hashtags',
        lazy='dynamic'
    )


# Notification model
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    type = db.Column(db.String(30), nullable=False)  # 'follow', 'like', 'comment'
    payload = db.Column(db.Text, nullable=True)  # JSON string
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationships so you can use n.actor and n.recipient in Python code
    actor = db.relationship('User', foreign_keys=[actor_id], backref=db.backref('actor_notifications', lazy='dynamic'))
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref=db.backref('received_notifications', lazy='dynamic'))

    def set_payload(self, data):
        self.payload = json.dumps(data)

    def get_payload(self):
        return json.loads(self.payload) if self.payload else {}


def create_notification(recipient_id, actor_id, notif_type, payload=None):
    """Create & persist a notification."""
    n = Notification(
        recipient_id=recipient_id,
        actor_id=actor_id,
        type=notif_type
    )
    if payload:
        n.set_payload(payload)
    db.session.add(n)
    db.session.commit()
    return n
# ----------------- END NOTIFICATIONS -----------------