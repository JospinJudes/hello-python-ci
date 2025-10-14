# main.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Tweet
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

##ordre chrono
@main.route('/timeline')
@login_required
def timeline():
    # Tweets du plus récent au plus ancien
    tweets = Tweet.query.order_by(Tweet.timestamp.desc()).all()
    return render_template('tweets.html', tweets=tweets, sort='chrono')

