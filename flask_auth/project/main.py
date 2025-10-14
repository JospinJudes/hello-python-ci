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
    tweets = current_user.tweets.order_by(Tweet.timestamp.desc()).all()
    return render_template('profile.html', user=current_user, tweets=tweets)


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



@main.route('/profile/edit_bio', methods=['POST'])
@login_required
def edit_bio():
    new_bio = request.form.get('bio', '').strip()

    # Limite de caractères
    if len(new_bio) > 300:
        flash("Bio is too long (max 300 characters).")
    else:
        current_user.bio = new_bio
        db.session.commit()
        flash("Your bio has been updated!")

    return redirect(url_for('main.profile'))