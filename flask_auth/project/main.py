# main.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Tweet, Like, Comment
from . import db
from .forms import TweetForm
from sqlalchemy import func

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    sort = request.args.get('sort', 'timeline')
    if sort == 'ranked':
        tweets = (db.session.query(Tweet)
              .filter(Tweet.user_id == current_user.id)
              .outerjoin(Like)
              .group_by(Tweet.id)
              .order_by(func.count(Like.id).desc())
              .all())
    elif sort == 'timeline' :
        # tri chronologique (timeline)
        tweets = (Tweet.query
                  .filter_by(user_id=current_user.id)
                  .order_by(Tweet.timestamp.desc())
                  .all())
    return render_template('profile.html', name=current_user.name, tweets=tweets, sort = sort)

@main.route('/tweet', methods=['GET', 'POST'])
@login_required
def tweet():
    form = TweetForm()
    if form.validate_on_submit():
        try:
            new_tweet = Tweet(content=form.content.data, user=current_user)
            db.session.add(new_tweet)
            db.session.commit()
            flash('Tweet posted!')
            return redirect(url_for('main.profile'))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred during publication. Please try again.")
    else:
        if form.content.errors:
            flash("Your tweet must be between 1 and 280 characters long.")
    return render_template('tweet.html', form=form)

### DELETE TWEET
@main.route('/delete_tweet/<int:tweet_id>', methods=['POST'])
@login_required
def delete_tweet(tweet_id):
    tweet = Tweet.query.get_or_404(tweet_id)  # Si le tweet n'existe pas on renvoie une erreur 404
    
    # Vérifier que le tweet appartient à l'utilisateur
    if tweet.user_id != current_user.id:
        flash("You cannot delete this tweet.")
        return redirect(url_for('main.profile'))
    try:
        db.session.delete(tweet)
        db.session.commit()
        # flash("Tweet supprimé avec succès !")
    except Exception:
        db.session.rollback()
        flash("An error occurred during deletion.")
        
    return redirect(url_for('main.profile'))


### LIKE / UNLIKE TWEET
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
    return redirect(url_for('main.profile'))


### COMMENT TWEET
@main.route('/comment/<int:tweet_id>', methods=['POST'])
@login_required
def comment_tweet(tweet_id):
    content = request.form.get('content')
    if not content:
        flash('Comment cannot be empty.')
        return redirect(url_for('main.profile'))

    comment = Comment(content=content, user_id=current_user.id, tweet_id=tweet_id)
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('main.profile'))
