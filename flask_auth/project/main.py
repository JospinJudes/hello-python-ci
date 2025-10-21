# main.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Tweet, Like, Comment
from . import db
from .forms import TweetForm

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    # récupère les tweets de l'utilisateur connecté, triés par date décroissante
    tweets = current_user.tweets.order_by(Tweet.timestamp.desc()).all()
    return render_template('profile.html', name=current_user.name, tweets=tweets)

#####AJOUT POST
@main.route('/tweet', methods=['GET', 'POST'])
@login_required
def tweet():
    form = TweetForm()
    if form.validate_on_submit():
        new_tweet = Tweet(content=form.content.data, user=current_user)
        db.session.add(new_tweet)
        db.session.commit()
        flash('Tweet posted!')
        return redirect(url_for('main.profile'))
    return render_template('tweet.html', form=form)

@main.route('/like/<int:tweet_id>', methods=['POST'])
@login_required
def like_tweet(tweet_id):
    tweet = Tweet.query.get_or_404(tweet_id)
    like = Like.query.filter_by(user_id=current_user.id, tweet_id=tweet_id).first()

    if like:
        db.session.delete(like)  # Unlike
    else:
        new_like = Like(user_id=current_user.id, tweet_id=tweet_id)
        db.session.add(new_like)

    db.session.commit()
    return redirect(url_for('index'))

@main.route('/comment/<int:tweet_id>', methods=['POST'])
@login_required
def comment_tweet(tweet_id):
    content = request.form.get('content')
    if not content:
        flash('Comment cannot be empty.')
        return redirect(url_for('index'))

    comment = Comment(content=content, user_id=current_user.id, tweet_id=tweet_id)
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('index'))
