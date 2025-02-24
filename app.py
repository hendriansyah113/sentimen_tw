from flask import Flask, render_template, request
from transformers import pipeline
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
from collections import Counter
import re

# Inisialisasi Flask
app = Flask(__name__)

# Load model IndoBERT dari Hugging Face
sentiment_analyzer = pipeline("sentiment-analysis", model="indobenchmark/indobert-base-p1")

# Fungsi Analisis Sentimen
def get_sentiment(text):
    result = sentiment_analyzer(text)
    label = result[0]['label']
    if label == 'LABEL_1':
        return 'Negatif'
    elif label == 'LABEL_2':
        return 'Netral'
    elif label == 'LABEL_3':
        return 'Positif'
    else:
        return 'Tidak Diketahui'

# Fungsi untuk Analisis Kata Kunci
def analyze_keywords(tweets):
    all_comments = " ".join(tweet['comment'] for tweet in tweets)
    words = re.findall(r'\b\w+\b', all_comments.lower())
    stopwords = set(['dan', 'yang', 'di', 'ke', 'dari', 'ini', 'itu', 'dengan', 'untuk', 'pada', 'adalah', 'dalam', 'juga', 'karena'])
    filtered_words = [word for word in words if word not in stopwords]
    word_counts = Counter(filtered_words)
    return word_counts.most_common(10)

# Fungsi untuk Scraping Postingan Twitter
def get_tweets(keyword):
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Aktifkan jika ingin headless
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    # Login Twitter
    driver.get("https://twitter.com/login")
    time.sleep(3)
    driver.find_element(By.NAME, 'text').send_keys("budionojabiren@gmail.com")
    driver.find_element(By.NAME, 'text').send_keys(Keys.ENTER)
    time.sleep(3)

    try:
        driver.find_element(By.NAME, 'text').send_keys("lalaries11_")
        driver.find_element(By.NAME, 'text').send_keys(Keys.ENTER)
        time.sleep(3)
    except:
        pass

    driver.find_element(By.NAME, 'password').send_keys("@Lisa1104")
    driver.find_element(By.NAME, 'password').send_keys(Keys.ENTER)
    time.sleep(5)

    # Cari Tweet berdasarkan keyword
    driver.get(f"https://twitter.com/search?q={keyword}&src=typed_query&f=live")
    time.sleep(5)

    tweets = []
    last_height = driver.execute_script("return document.body.scrollHeight")

    while len(tweets) < 30:
        elements = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
        for element in elements:
            try:
                username = element.find_element(By.XPATH, './/div[@dir="ltr"]/span').text
                comment = element.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
                
                link_element = element.find_element(By.XPATH, './/a[@role="link" and contains(@href, "/status/")]')
                link = link_element.get_attribute('href')
                
                if comment.strip():
                    sentiment = get_sentiment(comment)
                    tweets.append({
                        'username': username,
                        'comment': comment,
                        'sentiment': sentiment,
                        'link': link
                    })
            except Exception as e:
                print(f"Error saat mengambil data: {e}")
                continue

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break
        last_height = new_height

    driver.quit()
    return tweets

# Route Utama
@app.route('/', methods=['GET', 'POST'])
def index():
    tweets = []
    keyword = ""
    graph_html = ""
    word_graph_html = ""

    if request.method == 'POST':
        keyword = request.form['keyword']
        tweets = get_tweets(keyword)

    if not tweets:
        return render_template('index.html', tweets=tweets, graph_html="", word_graph_html="", keyword=keyword, message="Tidak ada data ditemukan!")

    df = pd.DataFrame(tweets)

    if 'sentiment' not in df.columns:
        print("Tidak ada kolom 'sentiment' pada DataFrame.")
        return render_template('index.html', tweets=tweets, graph_html="", word_graph_html="", keyword=keyword, message="Gagal memuat data sentimen!")

    # Analisis Sentimen
    sentiment_counts = df['sentiment'].value_counts()
    fig = go.Figure(data=[go.Pie(labels=sentiment_counts.index, values=sentiment_counts.values)])
    fig.update_layout(title='Distribusi Sentimen')
    graph_html = pio.to_html(fig, full_html=False)

    # Analisis Kata Kunci
    keyword_counts = analyze_keywords(tweets)
    words, counts = zip(*keyword_counts)
    word_fig = go.Figure(data=[go.Bar(x=words, y=counts)])
    word_fig.update_layout(title='Top 10 Kata Kunci', xaxis_title='Kata', yaxis_title='Frekuensi')
    word_graph_html = pio.to_html(word_fig, full_html=False)

    return render_template('index.html', tweets=tweets, graph_html=graph_html, word_graph_html=word_graph_html, keyword=keyword, message="")

if __name__ == '__main__':
    app.run(debug=True)
