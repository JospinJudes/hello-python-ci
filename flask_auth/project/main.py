# main.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import User, Tweet, followers, Like, Comment
from . import db
from .forms import TweetForm
from sqlalchemy import func 

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # page d'accueil = home
    return redirect(url_for('main.home'))

@main.route('/home')
@login_required
def home():
    sort = request.args.get('sort', 'timeline')
    following_ids_q = current_user.followed.with_entities(User.id)

    if sort == 'ranked':
        ranked_q = (
            db.session.query(Tweet, func.count(Like.id).label("lc"))
            .outerjoin(Like, Like.tweet_id == Tweet.id)
            .filter(
                (Tweet.user_id == current_user.id) |
                (Tweet.user_id.in_(following_ids_q))
            )
            .group_by(Tweet.id)
            .order_by(func.count(Like.id).desc(), Tweet.timestamp.desc())
        )
        tweets = [t for (t, _lc) in ranked_q.all()]
    else:
        tweets = (
            Tweet.query
            .filter(
                (Tweet.user_id == current_user.id) |
                (Tweet.user_id.in_(following_ids_q))
            )
            .order_by(Tweet.timestamp.desc())
            .all()
        )

    return render_template('home.html', name=current_user.name, tweets=tweets, sort=sort)



@main.route('/home/timeline')
@login_required
def home_timeline():
    return redirect(url_for('main.home', sort='timeline'))

@main.route('/home/ranked')
@login_required
def home_ranked():
    return redirect(url_for('main.home', sort='ranked'))

@main.route('/profile')
@login_required
def profile():
    # profil: uniquement mes tweets (comportement existant)
    tweets = current_user.tweets.order_by(Tweet.timestamp.desc()).all()
    return render_template('profile.html', name=current_user.name, tweets=tweets)

#####AJOUT POST
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
    tweet = Tweet.query.get_or_404(tweet_id) #si le tweet n'existe pas on renvoit directement l'utilisateur vers une "Page not found"
   
    #verifier que le tweet appartient à l'utilisateur
    if tweet.user_id != current_user.id:
        flash("You cannot delete this tweet.")
        return redirect(url_for('main.profile'))
    try:
        db.session.delete(tweet)
        db.session.commit()
        #flash("Tweet supprimé avec succès !")
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
    tweet = Tweet.query.get_or_404(tweet_id)
    content = request.form.get('comment_content')
    if not content:
        flash('Comment cannot be empty.')
        return redirect(url_for('main.profile'))

    comment = Comment(content=content, user_id=current_user.id, tweet_id=tweet_id)
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('main.profile'))

