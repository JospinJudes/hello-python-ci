# main.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import User, Tweet, followers, Like, Comment, Notification, create_notification
from . import db
from .forms import TweetForm
from sqlalchemy import func
from flask import jsonify, request

main = Blueprint('main', __name__)

# -------------------- HOME / INDEX --------------------
@main.route('/')
def index():
    return redirect(url_for('main.home'))

@main.route('/home')
@login_required
def home():
    sort = request.args.get('sort', 'timeline')
    following_ids = [u.id for u in current_user.followed] + [current_user.id]


    if sort == 'ranked':
        ranked_q = (
            db.session.query(Tweet, func.count(Like.id).label("lc"))
            .outerjoin(Like, Like.tweet_id == Tweet.id)
            .filter(Tweet.user_id.in_(following_ids))
            .group_by(Tweet.id)
            .order_by(func.count(Like.id).desc(), Tweet.timestamp.desc())
        )
        tweets = [t for (t, _lc) in ranked_q.all()]
    else:
        tweets = (
            Tweet.query
            .filter(Tweet.user_id.in_(following_ids))
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
    create_notification(recipient_id=user.id, actor_id=current_user.id, notif_type="follow")
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
    if not current_user.has_liked(tweet):  # on some logic frameworks this may be unnecessary; safe to always create here on add
        pass  # placeholder - kept for readability

    create_notification(
        recipient_id=tweet.user_id,
        actor_id=current_user.id,
        notif_type="like",
        payload={"tweet_id": tweet.id}
    )
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
        create_notification(
            recipient_id=tweet.user_id,
            actor_id=current_user.id,
            notif_type="comment",
            payload={"tweet_id": tweet.id, "comment": new_comment.content}
        )
        flash("Comment added!")
    else:
        flash("Comment cannot be empty.")
    return redirect(request.referrer or url_for('main.profile'))

# -------------------- NOTIFICATIONS --------------------

@main.route("/notifications")
@login_required
def notifications():
    notifs = Notification.query.filter_by(recipient_id=current_user.id) \
        .order_by(Notification.created_at.desc()) \
        .all()

    # passe à Jinja une liste de dicts simples
    formatted = [{
        "id": n.id,
        "type": n.type,
        "actor": n.actor.name if n.actor else "",
        "payload": n.get_payload() if hasattr(n, 'get_payload') else {},
        "is_read": n.is_read,
        "created_at": n.created_at.strftime("%Y-%m-%d %H:%M")
    } for n in notifs]


    return render_template("notifications.html", notifications=formatted)


@main.route('/notifications/count')
@login_required
def notifications_count():
    # retourne le nombre de notifications non lues pour l'utilisateur courant
    unread = Notification.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    return jsonify({"unread": unread})

@main.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    # marque toutes les notifications non lues de l'utilisateur comme lues
    Notification.query.filter_by(recipient_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({"status":"ok"})



@main.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def read_notification(notif_id):
    n = Notification.query.get_or_404(notif_id)
    if n.recipient_id != current_user.id:
        return jsonify({"error": "forbidden"}), 403
    n.is_read = True
    db.session.commit()
    return jsonify({"status": "ok"})