# main.py
from sqlalchemy import func, desc
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import User, Tweet, followers
from . import db
from .forms import TweetForm
try:
    from .models import Like, Comment
    HAS_REACTIONS = True
    print("✅ Like et Comment models disponibles")
except Exception as e:
    HAS_REACTIONS = False
    print(f"❌ Like et Comment models non disponibles: {e}")


main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    sort = request.args.get('sort', 'timeline')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Nombre de tweets par page
    
    # IDs des comptes suivis + moi-même
    following_ids = [u.id for u in current_user.followed] + [current_user.id]

    # Base query
    base_q = Tweet.query.filter(Tweet.user_id.in_(following_ids))

    if sort == 'ranked' and HAS_REACTIONS:
        # Score = 10*likes + 3*comments
        likes_ct = func.count(Like.id)
        comments_ct = func.count(Comment.id)
        score = likes_ct * 10 + comments_ct * 3

        query = (db.session.query(Tweet, likes_ct.label('likes'), comments_ct.label('comments'))
                .filter(Tweet.user_id.in_(following_ids))
                .outerjoin(Like, Like.tweet_id == Tweet.id)
                .outerjoin(Comment, Comment.tweet_id == Tweet.id)
                .group_by(Tweet.id)
                .order_by(desc(score), Tweet.timestamp.desc()))
        
        # Pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        tweets_data = pagination.items
        
        tweets = []
        for t, l, c in tweets_data:
            t.likes_count = int(l or 0)
            t.comments_count = int(c or 0)
            tweets.append(t)
            
    elif sort == 'ranked' and not HAS_REACTIONS:
        # Fallback si réactions non disponibles
        flash("Ranked timeline is not available - showing chronological order instead")
        query = base_q.order_by(Tweet.timestamp.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        tweets = pagination.items
        sort = 'timeline'
    
    else:
        # Tri chronologique
        query = base_q.order_by(Tweet.timestamp.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        tweets = pagination.items

    return render_template('profile.html', 
                         name=current_user.name, 
                         tweets=tweets, 
                         sort=sort,
                         pagination=pagination)

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
    return redirect(url_for('main.profile', sort='timeline'))

@main.route('/home/ranked')
@login_required
def home_ranked():
    return redirect(url_for('main.profile', sort='ranked'))

# Gestion d'erreur pour la pagination
@main.app_errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/profile'):
        flash("Unable to load more posts")
        return redirect(url_for('main.profile'))
    return render_template('404.html'), 404