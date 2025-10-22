# main.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import User, Tweet, followers
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

##ordre chrono
@main.route('/home/timeline')
@login_required
def home_timeline():
    # ids des comptes que je suis + moi-même
    following_ids = [u.id for u in current_user.followed] + [current_user.id]

    # tweets filtrés + triés du plus récent au plus ancien
    tweets = (Tweet.query
              .filter(Tweet.user_id.in_(following_ids))
              .order_by(Tweet.timestamp.desc())
              .all())
    return render_template('profile.html', name=current_user.name, tweets=tweets)
S