from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
from . import db


class TweetForm(FlaskForm):
    content = TextAreaField('Your Message', validators=[DataRequired(), Length(max=280)])
    submit = SubmitField('Post')
