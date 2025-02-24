from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from textblob import TextBlob
import plotly.graph_objs as go
import plotly.io as pio
import time

app = Flask(__name__)

# Ganti dengan username dan password Twitter kamu
USERNAME = "budionojabiren@gmail.com"
PASSWORD = "@Lisa1104"

def cari_tweet(kata_kunci, max_tweet=100):
    # Setup Selenium
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    
    # Login ke Twitter
    driver.get("https://twitter.com/login")
    time.sleep(5)

    # Isi username
    username_input = driver.find_element(By.NAME, "text")
    username_input.send_keys(USERNAME)
    username_input.send_keys(Keys.RETURN)
    time.sleep(3)

    # Isi password
    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.RETURN)
    time.sleep(5)

    # Cari tweet berdasarkan kata kunci
    driver.get(f"https://twitter.com/search?q={kata_kunci}&src=typed_query")
    time.sleep(5)

    # Scroll otomatis untuk memuat lebih banyak tweet
    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")

    tweets = []
    while len(tweets) < max_tweet:
        # Scroll ke bawah
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)

        # Ambil tweet
        tweet_elements = driver.find_elements(By.XPATH, "//article//div[@lang]")
        for tweet in tweet_elements:
            if tweet.text not in tweets:
                tweets.append(tweet.text)

        # Berhenti jika sudah cukup
        if len(tweets) >= max_tweet:
            break

        # Cek ketinggian setelah scroll
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # Berhenti jika tidak ada perubahan tinggi halaman
        last_height = new_height

    driver.quit()
    return tweets[:max_tweet]

def analisis_sentimen(tweets):
    positif = 0
    negatif = 0
    netral = 0

    for tweet in tweets:
        analisis = TextBlob(tweet)
        if analisis.sentiment.polarity > 0:
            positif += 1
        elif analisis.sentiment.polarity < 0:
            negatif += 1
        else:
            netral += 1

    return positif, negatif, netral

def buat_grafik(positif, negatif, netral):
    labels = ['Positif', 'Negatif', 'Netral']
    values = [positif, negatif, netral]

    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3)])
    fig.update_layout(title_text='Analisis Sentimen Tweet')

    # Convert to HTML
    grafik_html = pio.to_html(fig, full_html=False)
    return grafik_html

@app.route('/', methods=['GET', 'POST'])
def index():
    grafik_html = ""
    if request.method == 'POST':
        kata_kunci = request.form['kata_kunci']
        tweets = cari_tweet(kata_kunci)
        positif, negatif, netral = analisis_sentimen(tweets)
        grafik_html = buat_grafik(positif, negatif, netral)
    return render_template('index.html', grafik_html=grafik_html)

if __name__ == '__main__':
    app.run(debug=True)
