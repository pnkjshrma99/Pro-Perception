from flask import Flask, render_template, request, jsonify, url_for, redirect
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import praw as praw
import csv
import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from textblob import TextBlob
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

app = Flask(__name__, static_url_path='/static', static_folder='static')
analyzer = SentimentIntensityAnalyzer()


# bcrypt = Bcrypt(app)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
# db = SQLAlchemy(app)
# app.config['SECRET_KEY'] = 'key'


# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'login'


# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))


# class User(db.Model, UserMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(20), nullable=False, unique=True)
#     password = db.Column(db.String(80), nullable=False)


# class RegisterForm(FlaskForm):
#     username = StringField(validators=[
#                            InputRequired(), Length(min=4, max=40)], render_kw={"placeholder": "Username"})

#     password = PasswordField(validators=[
#                              InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

#     submit = SubmitField('Register')

#     def validate_username(self, username):
#         existing_user_username = User.query.filter_by(
#             username=username.data).first()
#         if existing_user_username:
#             raise ValidationError(
#                 'That username already exists. Please choose a different one.')


# class LoginForm(FlaskForm):
#     username = StringField(validators=[
#                            InputRequired(), Length(min=4, max=40)], render_kw={"placeholder": "Username"})

#     password = PasswordField(validators=[
#                              InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

#     submit = SubmitField('Login')


# @app.route('/login.html', methods=['GET', 'POST'])
# def login():
#     form = LoginForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(username=form.username.data).first()
#         if user:
#             if bcrypt.check_password_hash(user.password, form.password.data):
#                 login_user(user)
#                 return redirect(url_for('index'))
#     return render_template('login.html', form=form)



# @app.route('/logout', methods=['GET', 'POST'])
# @login_required
# def logout():
#     logout_user()
#     return redirect(url_for('login'))


# @ app.route('/register.html', methods=['GET', 'POST'])
# def register():
#     form = RegisterForm()

#     if form.validate_on_submit():
#         hashed_password = bcrypt.generate_password_hash(form.password.data)
#         new_user = User(username=form.username.data, password=hashed_password)
#         db.session.add(new_user)
#         db.session.commit()
#         return redirect(url_for('login'))

#     return render_template('register.html', form=form)


reddit = praw.Reddit(
    client_id="mG0s_3OPp0QR85VVULmUDw",
    client_secret="TeNFxx-MeKinFbmTkfuh6sO_NpE5JA",
    password="Harshnema1234",
    user_agent="sentiment",
    username="nema_harsh" 
)

# @app.route('/register.html')
# def index():
#     return render_template('register.html')


# @app.route('/login.html')
# def index():
#     return render_template('login.html')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/text.html')
def text():
    return render_template('text.html')


@app.route('/contact.html')
def contact():
    return render_template('contact.html')

@app.route('/service.html')
def service():
    return render_template('service.html')



@app.route('/audio.html')
def audio():
    return render_template('audio.html')


@app.route('/youtube.html')
def youtube():
    return render_template('youtube.html')


# def check_word(word,data):
#     contains=data['title'].str.contains(word,case=False)
#     return contains

# def get_sentiment(title):
#     sid = SentimentIntensityAnalyzer()
#     return sid.polarity_scores(title)['compound']


# @app.route('/analyze_sentiment', methods=['POST'])
# def analyze_sentiment():
#     text = request.form.get('user-input')
#     sentiment_score = perform_sentiment_analysis(text)
#     return jsonify(sentiment_score)

# def perform_sentiment_analysis(text):
#     analyzer = SentimentIntensityAnalyzer()
#     sentiment_score = analyzer.polarity_scores(text)
#     return sentiment_score



# @app.route('/custom_analyze', methods=['POST'])
# def custom_analyze():
#     try:
#         data = request.get_json()
#         url = data['url']

      
#         def get_transcript(url):
#             video_id = url.split("v=")[1]
#             transcript = YouTubeTranscriptApi.get_transcript(video_id)
#             return transcript

#         def analyze_sentiment1(transcript):
#             text = ' '.join([entry['text'] for entry in transcript])
#             blob = TextBlob(text)
#             sentiment = {
#                 'neg': blob.sentiment.polarity if blob.sentiment.polarity < 0 else 0,
#                 'neu': 0, 
#                 'pos': blob.sentiment.polarity if blob.sentiment.polarity > 0 else 0,
#                 'compound': blob.sentiment.polarity
#             }
#             return sentiment

#         transcript = get_transcript(url)
#         if transcript:
#             sentiment_score = analyze_sentiment1(transcript)
#             return jsonify(sentiment_score)
#         else:
#             return jsonify({'error': 'Transcript not available for this video.'}), 400
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500







# @app.route('/results.html', methods=['POST'])
# def results():
#     keyword = request.form['keyword'].strip()
#     if not keyword:
#         return "Error: No keyword provided.", 400  

  
#     search_results = reddit.subreddits.search(keyword, limit=1)
#     subreddit_name = None

#     for result in search_results:
#         subreddit_name = result.display_name
#         break

#     if not subreddit_name:
#         return "Error: No matching subreddit found.", 400

#     try:
#         subreddit = reddit.subreddit(subreddit_name)
#     except Exception as e:
#         return f"Error: {str(e)}", 400  

#     new_data_list = []
#     time_series_sentiment_scores = []
#     time_labels = []

#     for post in subreddit.hot(limit=90):
#         sentiment_score = perform_sentiment_analysis(post.title)
#         new_data_list.append({
#             "title": post.title,
#             "author": post.author,
#             "link": post.shortlink,
#             "comment_ID": post.id,
#             "time": datetime.datetime.fromtimestamp(post.created_utc)
#         })
#         time_series_sentiment_scores.append(sentiment_score['compound'])
#         time_labels.append(datetime.datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M:%S'))

#     field_names = ["title", "author", "link", "comment_ID", "time"]
#     with open('product_sales.csv', 'w', newline='', encoding="utf-8") as csvfile:
#         writer = csv.DictWriter(csvfile, fieldnames=field_names)
#         writer.writeheader()
#         writer.writerows(new_data_list)
    
#     with open('product_sales.csv', 'r', encoding='utf-8') as csvfile:
#         csvreader = csv.DictReader(csvfile)
#         data = list(csvreader)
    
#     sentiment_scores = [0.1, 0.5, 0.4, 0.2] 

#     return render_template('results.html', keyword=keyword, data=data, sentiment_scores=sentiment_scores, time_series_sentiment_scores=time_series_sentiment_scores, time_labels=time_labels)


if __name__ == '__main__':
    app.run()
