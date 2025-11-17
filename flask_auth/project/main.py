# main.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import User, Tweet, followers, Like, Comment
from . import db
from .forms import TweetForm
from sqlalchemy import func

main = Blueprint('main', __name__)

# -------------------- HOME / INDEX --------------------
@main.route('/')
def index():
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

# -------------------- PROFILE --------------------
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
        is_own_profile=True
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
        is_own_profile=(user.id == current_user.id)
    )

# -------------------- TWEETS --------------------
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
        except Exception:
            db.session.rollback()
            flash("An error occurred during publication. Please try again.")
    else:
        if form.content.errors:
            flash("Your tweet must be between 1 and 280 characters long.")
    return render_template('tweet.html', form=form)

@main.route('/delete_tweet/<int:tweet_id>', methods=['POST'])
@login_required
def delete_tweet(tweet_id):
    tweet = Tweet.query.get_or_404(tweet_id)
    if tweet.user_id != current_user.id:
        flash("You cannot delete this tweet.")
        return redirect(url_for('main.profile'))
    try:
        db.session.delete(tweet)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("An error occurred during deletion.")
    return redirect(url_for('main.profile'))

# -------------------- EDIT BIO --------------------
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

# -------------------- FOLLOW / UNFOLLOW --------------------
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

# -------------------- SEARCH --------------------
@main.route("/search")
def search_user():
    query = request.args.get("q", "").strip()
    users = []
    if query:
        users = User.query.filter(User.name.ilike(f"%{query}%")).all()
    return render_template("search_results.html", users=users, query=query)

# -------------------- LIKE --------------------
@main.route('/like/<int:tweet_id>', methods=['POST'])
@login_required
def like_tweet(tweet_id):
    tweet = Tweet.query.get_or_404(tweet_id)
    if current_user.has_liked(tweet):
        like = Like.query.filter_by(user_id=current_user.id, tweet_id=tweet.id).first()
        if like:
            db.session.delete(like)
    else:
        new_like = Like(user_id=current_user.id, tweet_id=tweet.id)
        db.session.add(new_like)
    db.session.commit()
    return redirect(request.referrer or url_for('main.profile'))

# -------------------- COMMENT --------------------
@main.route('/comment/<int:tweet_id>', methods=['POST'])
@login_required
def comment_tweet(tweet_id):
    tweet = Tweet.query.get_or_404(tweet_id)
    content = request.form.get('comment_content', '').strip()
    if content:
        new_comment = Comment(user_id=current_user.id, tweet_id=tweet.id, content=content)
        db.session.add(new_comment)
        db.session.commit()
        flash("Comment added!")
    else:
        flash("Comment cannot be empty.")
    return redirect(request.referrer or url_for('main.profile'))
