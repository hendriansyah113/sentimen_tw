from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from textblob import TextBlob
import plotly.graph_objects as go
import time

app = Flask(__name__)

# Data Login Twitter
TWITTER_USERNAME = "lalaries11_"
TWITTER_EMAIL = "budionojabiren@gmail.com"
TWITTER_PASSWORD = "@Lisa1104"

# Fungsi untuk Analisis Sentimen
def get_sentiment(text):
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0:
        return 'Positif'
    elif analysis.sentiment.polarity == 0:
        return 'Netral'
    else:
        return 'Negatif'

# Fungsi untuk Scraping Tweet
def scrape_tweets(keyword):
    # Setup Selenium
    options = Options()
    # options.add_argument("--headless")  # Jangan gunakan headless untuk menampilkan Chrome
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://twitter.com/login")
    time.sleep(5)
    
    # Masukkan Email terlebih dahulu
    email_input = driver.find_element(By.NAME, "text")
    email_input.send_keys(TWITTER_EMAIL)
    email_input.send_keys(Keys.RETURN)
    time.sleep(3)
    
    # Cek apakah diminta Username
    try:
        username_input = driver.find_element(By.NAME, "text")
        username_input.send_keys(TWITTER_USERNAME)
        username_input.send_keys(Keys.RETURN)
        time.sleep(3)
        print("Username diminta, sudah dimasukkan.")
    except:
        print("Tidak diminta username, lanjut ke password.")

    # Masukkan Password
    try:
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(TWITTER_PASSWORD)
        password_input.send_keys(Keys.RETURN)
        time.sleep(5)
    except:
        print("Gagal menemukan input password")

    # Cari Keyword
    search_url = f"https://twitter.com/search?q={keyword}&src=typed_query"
    driver.get(search_url)
    time.sleep(5)

    # Scroll untuk memuat lebih banyak tweet
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

    # Ambil Data Tweet
    tweets = driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")
    data = []
    for tweet in tweets:
        try:
            username = tweet.find_element(By.XPATH, ".//div[@dir='ltr']/span").text
            comment = tweet.find_element(By.XPATH, ".//div[@lang]").text
            sentiment = get_sentiment(comment)
            data.append((username, comment, sentiment))
        except:
            continue

    driver.quit()
    return data

# Routing Web
@app.route('/', methods=['GET', 'POST'])
def index():
    tweets_data = []
    if request.method == 'POST':
        keyword = request.form['keyword']
        tweets_data = scrape_tweets(keyword)

        # Membuat Grafik
        sentiments = [tweet[2] for tweet in tweets_data]
        sentiment_counts = { 'Positif': sentiments.count('Positif'), 
                             'Netral': sentiments.count('Netral'), 
                             'Negatif': sentiments.count('Negatif') }

        fig = go.Figure([go.Bar(x=list(sentiment_counts.keys()), 
                                y=list(sentiment_counts.values()))])
        fig.update_layout(title_text=f'Analisis Sentimen untuk "{keyword}"')
        graph_html = fig.to_html(full_html=False)

        return render_template('index.html', tweets_data=tweets_data, graph_html=graph_html)
    
    return render_template('index.html', tweets_data=tweets_data)

if __name__ == '__main__':
    app.run(debug=True)
