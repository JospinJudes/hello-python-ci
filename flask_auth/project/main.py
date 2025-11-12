# main.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Tweet
from . import db
from .forms import TweetForm
from .models import User  
main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    tweets = current_user.tweets.order_by(Tweet.timestamp.desc()).all()
    following_count = current_user.followed.count()
    followers_count = current_user.followers.count()
    return render_template(
        'profile.html',
        user=current_user,
        tweets=tweets,
        following_count=following_count,
        followers_count=followers_count,
        is_own_profile=True  # on indique que c’est ton profil
    )


@main.route('/profile/<int:user_id>')
@login_required
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    tweets = user.tweets.order_by(Tweet.timestamp.desc()).all()
    following_count = user.followed.count()
    followers_count = user.followers.count()
    return render_template(
        'profile.html',
        user=user,
        tweets=tweets,
        following_count=following_count,
        followers_count=followers_count,
        is_own_profile=(user.id == current_user.id)  # ✅ comparaison directe
    )







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


@main.route('/profile/edit_bio', methods=['POST'])
@login_required
def edit_bio():
    new_bio = request.form.get('bio', '').strip()

    if len(new_bio) > 300:
        flash("Bio is too long (max 300 characters)", category='bio')
    else:
        current_user.bio = new_bio
        db.session.commit()
        flash("Your bio has been updated!", category="bio")

    return redirect(url_for('main.profile'))



##### FOLLOW / UNFOLLOW #####
@main.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash("You cannot follow yourself.", category="follow")
        return redirect(url_for('main.user_profile', user_id=user.id))
    current_user.follow(user)
    db.session.commit()
    flash(f"You are now following {user.name}!", category="follow")
    return redirect(url_for('main.user_profile', user_id=user.id))


@main.route('/unfollow/<int:user_id>', methods=['POST'])
@login_required
def unfollow(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash("You cannot unfollow yourself.", category="follow")
        return redirect(url_for('main.user_profile', user_id=user.id))
    current_user.unfollow(user)
    db.session.commit()
    flash(f"You unfollowed {user.name}.", category="follow")
    return redirect(url_for('main.user_profile', user_id=user.id))



@main.route("/search")
def search_user():
    query = request.args.get("q", "").strip()  # récupère le texte
    users = []
    if query:
        # Recherche insensible à la casse sur le champ name
        users = User.query.filter(User.name.ilike(f"%{query}%")).all()
    return render_template("search_results.html", users=users, query=query)