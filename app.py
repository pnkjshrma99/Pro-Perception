import os
import csv
import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob
from youtube_transcript_api import YouTubeTranscriptApi
import re

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ─── Database Models ────────────────────────────────────────────

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=40)],
                           render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)],
                             render_kw={"placeholder": "Password"})
    submit = SubmitField('Register')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('That username already exists.')

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=40)],
                           render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)],
                             render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

# ─── Helpers ────────────────────────────────────────────────────

nltk_data_path = os.path.join(os.path.dirname(__file__), 'nltk_data')
if not os.path.exists(nltk_data_path):
    import nltk
    nltk.download('vader_lexicon', quiet=True)

analyzer = SentimentIntensityAnalyzer()

def perform_sentiment_analysis(text):
    return analyzer.polarity_scores(text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

# ─── Auth Routes ────────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/register.html', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout.html')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ─── Page Routes ────────────────────────────────────────────────

@app.route('/index.html')
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

# ─── Text Sentiment API ─────────────────────────────────────────

@app.route('/analyze_sentiment', methods=['POST'])
def analyze_sentiment():
    text = request.form.get('user-input') or request.json.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    score = perform_sentiment_analysis(text)
    return jsonify(score)

# ─── YouTube Sentiment API ──────────────────────────────────────

@app.route('/custom_analyze', methods=['POST'])
def custom_analyze():
    try:
        data = request.get_json()
        url = data.get('url', '')
        video_id_match = re.search(r'(?:v=|\/)([a-zA-Z0-9_-]{11})', url)
        if not video_id_match:
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        video_id = video_id_match.group(1)
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = ' '.join(entry['text'] for entry in transcript)
        blob = TextBlob(text)
        sentiment = {
            'neg': blob.sentiment.polarity if blob.sentiment.polarity < 0 else 0,
            'neu': 0,
            'pos': blob.sentiment.polarity if blob.sentiment.polarity > 0 else 0,
            'compound': blob.sentiment.polarity
        }
        return jsonify(sentiment)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─── Reddit Social Media Analysis ───────────────────────────────

@app.route('/results.html', methods=['POST'])
def results():
    keyword = request.form.get('keyword', '').strip()
    if not keyword:
        return render_template('results.html', keyword='', data=[],
                               sentiment_scores=[], time_series_sentiment_scores=[],
                               time_labels=[], error='No keyword provided')

    try:
        import praw
        reddit = praw.Reddit(
            client_id=os.environ.get('REDDIT_CLIENT_ID', 'mG0s_3OPp0QR85VVULmUDw'),
            client_secret=os.environ.get('REDDIT_CLIENT_SECRET', 'TeNFxx-MeKinFbmTkfuh6sO_NpE5JA'),
            password=os.environ.get('REDDIT_PASSWORD', 'Harshnema1234'),
            user_agent=os.environ.get('REDDIT_USER_AGENT', 'sentiment'),
            username=os.environ.get('REDDIT_USERNAME', 'nema_harsh')
        )
        search_results = list(reddit.subreddits.search(keyword, limit=1))
        if not search_results:
            return render_template('results.html', keyword=keyword, data=[],
                                   sentiment_scores=[], time_series_sentiment_scores=[],
                                   time_labels=[], error='No matching subreddit found')
        subreddit = reddit.subreddit(search_results[0].display_name)
    except ImportError:
        return render_template('results.html', keyword=keyword, data=[],
                               sentiment_scores=[], time_series_sentiment_scores=[],
                               time_labels=[], error='Reddit API not configured')
    except Exception as e:
        return render_template('results.html', keyword=keyword, data=[],
                               sentiment_scores=[], time_series_sentiment_scores=[],
                               time_labels=[], error=str(e))

    new_data = []
    time_scores = []
    time_labels = []

    for post in subreddit.hot(limit=90):
        score = perform_sentiment_analysis(post.title)
        ts = datetime.datetime.fromtimestamp(post.created_utc)
        new_data.append({
            "title": post.title,
            "author": str(post.author),
            "link": post.shortlink,
            "comment_ID": post.id,
            "time": ts.strftime('%Y-%m-%d %H:%M:%S'),
            "sentiment": score['compound']
        })
        time_scores.append(score['compound'])
        time_labels.append(ts.strftime('%Y-%m-%d %H:%M:%S'))

    # Write to CSV
    field_names = ["title", "author", "link", "comment_ID", "time", "sentiment"]
    csv_path = 'product_sales.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=field_names)
        w.writeheader()
        w.writerows(new_data)

    # Aggregate sentiment stats
    avg_sentiment = sum(time_scores) / len(time_scores) if time_scores else 0
    positive_count = sum(1 for s in time_scores if s > 0.05)
    negative_count = sum(1 for s in time_scores if s < -0.05)
    neutral_count = len(time_scores) - positive_count - negative_count

    sentiment_scores = [
        round(negative_count / len(time_scores) * 100, 1) if time_scores else 0,
        round(neutral_count / len(time_scores) * 100, 1) if time_scores else 0,
        round(positive_count / len(time_scores) * 100, 1) if time_scores else 0,
        round(avg_sentiment, 2)
    ]

    return render_template('results.html',
                           keyword=keyword,
                           data=new_data,
                           sentiment_scores=sentiment_scores,
                           time_series_sentiment_scores=time_scores,
                           time_labels=time_labels,
                           error=None)

# ─── Run ────────────────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
