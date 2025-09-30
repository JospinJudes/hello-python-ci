# main.py

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from .forms import TweetForm


main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)

#####AJOUT POST
@main.route('/tweet', methods=['GET', 'POST'])
@login_required
def tweet():
    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            new_tweet = Tweet(content=content, user=current_user)
            db.session.add(new_tweet)
            db.session.commit()
            flash('Tweet posted!')
            return redirect(url_for('main.profile'))
    return render_template('tweet.html', form=TweetForm())