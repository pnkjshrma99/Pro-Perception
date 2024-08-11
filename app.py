from flask import Flask, render_template, request, jsonify
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import praw as praw
import pandas as pd
import csv
import datetime
import matplotlib.pyplot as plt
from youtube_transcript_api import YouTubeTranscriptApi
from textblob import TextBlob


app = Flask(__name__, static_url_path='/static', static_folder='static')
analyzer = SentimentIntensityAnalyzer()

import nltk
nltk.download('vader_lexicon')

reddit = praw.Reddit(
    client_id="mG0s_3OPp0QR85VVULmUDw",
    client_secret="TeNFxx-MeKinFbmTkfuh6sO_NpE5JA",
    password="Harshnema1234",
    user_agent="sentiment",
    username="nema_harsh" 
)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login.html')
def login():
    return render_template('login.html')



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


def check_word(word,data):
    contains=data['title'].str.contains(word,case=False)
    return contains

def get_sentiment(title):
    sid = SentimentIntensityAnalyzer()
    return sid.polarity_scores(title)['compound']


@app.route('/analyze_sentiment', methods=['POST'])
def analyze_sentiment():
    text = request.form.get('user-input')
    sentiment_score = perform_sentiment_analysis(text)
    return jsonify(sentiment_score)

def perform_sentiment_analysis(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment_score = analyzer.polarity_scores(text)
    return sentiment_score



@app.route('/custom_analyze', methods=['POST'])
def custom_analyze():
    try:
        data = request.get_json()
        url = data['url']

        # Define get_transcript function
        def get_transcript(url):
            video_id = url.split("v=")[1]
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return transcript

        # Define analyze_sentiment1 function
        def analyze_sentiment1(transcript):
            text = ' '.join([entry['text'] for entry in transcript])
            blob = TextBlob(text)
            sentiment = {
                'neg': blob.sentiment.polarity if blob.sentiment.polarity < 0 else 0,
                'neu': 0,  # Neutral can be calculated based on sentiment score ranges if needed
                'pos': blob.sentiment.polarity if blob.sentiment.polarity > 0 else 0,
                'compound': blob.sentiment.polarity
            }
            return sentiment

        transcript = get_transcript(url)
        if transcript:
            sentiment_score = analyze_sentiment1(transcript)
            return jsonify(sentiment_score)
        else:
            return jsonify({'error': 'Transcript not available for this video.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500







@app.route('/results.html', methods=['POST'])
def results():
    keyword = request.form['keyword'].strip()
    if not keyword:
        return "Error: No keyword provided.", 400  # Handle empty input

    # Search for subreddits
    search_results = reddit.subreddits.search(keyword, limit=1)
    subreddit_name = None

    for result in search_results:
        subreddit_name = result.display_name
        break

    if not subreddit_name:
        return "Error: No matching subreddit found.", 400

    try:
        subreddit = reddit.subreddit(subreddit_name)
    except Exception as e:
        return f"Error: {str(e)}", 400  # Handle invalid subreddit or other errors

    new_data_list = []
    time_series_sentiment_scores = []
    time_labels = []

    for post in subreddit.hot(limit=90):
        sentiment_score = perform_sentiment_analysis(post.title)
        new_data_list.append({
            "title": post.title,
            "author": post.author,
            "link": post.shortlink,
            "comment_ID": post.id,
            "time": datetime.datetime.fromtimestamp(post.created_utc)
        })
        time_series_sentiment_scores.append(sentiment_score['compound'])
        time_labels.append(datetime.datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M:%S'))

    field_names = ["title", "author", "link", "comment_ID", "time"]
    with open('product_sales.csv', 'w', newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(new_data_list)
    
    with open('product_sales.csv', 'r', encoding='utf-8') as csvfile:
        csvreader = csv.DictReader(csvfile)
        data = list(csvreader)
    
    # Example sentiment scores
    sentiment_scores = [0.1, 0.5, 0.4, 0.2]  # Replace with actual sentiment scores

    return render_template('results.html', keyword=keyword, data=data, sentiment_scores=sentiment_scores, time_series_sentiment_scores=time_series_sentiment_scores, time_labels=time_labels)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4000))
    app.run(host='0.0.0.0', port=port)
