from flask import Flask, render_template, request
import sqlite3
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
import string

nltk.download('punkt')

app = Flask(__name__)

# SQLite database setup
conn = sqlite3.connect('feedback.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS feedback_data 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  summary TEXT,
                  feedback TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()
conn.close()

@app.route("/")
def about():
    return render_template('home.html')

@app.route("/submit", methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        try:
            doc = request.form['text']
            feedback = request.form.get('feedback', '')  # Get feedback if present, else default to empty string

            sentences = sent_tokenize(doc)
            words = word_tokenize(doc.lower())
            stop_words = set(stopwords.words('english'))
            punctuation = set(string.punctuation)

            words = [word for word in words if word.isalnum() and word not in stop_words and word not in punctuation]

            word_freq = FreqDist(words)
            max_freq = max(word_freq.values()) if word_freq else 1  # Check for empty word_freq
            normalized_freq = {word: freq / max_freq for word, freq in word_freq.items()}

            sentence_scores = {}
            for sentence in sentences:
                sentence_words = word_tokenize(sentence.lower())
                sentence_score = sum(normalized_freq.get(word, 0) for word in sentence_words)
                sentence_scores[sentence] = sentence_score

            summary_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:5]
            summary = ' '.join(summary_sentences)

            # Store feedback in the database
            conn = sqlite3.connect('feedback.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO feedback_data (summary, feedback) VALUES (?, ?)", (summary, feedback))
            conn.commit()
            conn.close()

            return render_template('submit.html', predictionText=summary)
        
        except Exception as e:
            return f"An error occurred: {str(e)}"

    return render_template('submit.html')

if __name__ == '__main__':
    app.run(debug=True)
