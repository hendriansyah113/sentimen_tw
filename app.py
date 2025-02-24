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

# Fungsi untuk Scraping Postingan Twitter
# Fungsi untuk Scraping Komentar Twitter
def get_tweets(keyword):
    # Setup Selenium
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
                # Ambil isi postingan, bukan komentar
                comment = element.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
                
                # Ambil link tweet
                link_element = element.find_element(By.XPATH, './/a[@role="link" and contains(@href, "/status/")]')
                link = link_element.get_attribute('href')
                
                # Cek jika postingan tidak kosong
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

        # Scroll ke bawah untuk memuat lebih banyak tweet
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break
        last_height = new_height

    driver.quit()
    print(f"Data yang berhasil diambil: {tweets}")
    return tweets

    # Setup Selenium
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment jika ingin headless
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

    # Cari Postingan berdasarkan keyword
    driver.get(f"https://twitter.com/search?q={keyword}&src=typed_query&f=live")
    time.sleep(5)

    tweets = []
    last_height = driver.execute_script("return document.body.scrollHeight")

    while len(tweets) < 30:
        elements = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
        for element in elements:
            try:
                username = element.find_element(By.XPATH, './/div[@dir="ltr"]/span').text
                # Mengambil postingan (teks utama tweet)
                comment = element.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
                
                # Cek jika postingan tidak kosong
                if comment.strip():
                    sentiment = get_sentiment(comment)
                    tweets.append({
                        'username': username,
                        'comment': comment,
                        'sentiment': sentiment
                    })
            except Exception as e:
                print(f"Error saat mengambil data: {e}")
                continue

        # Scroll ke bawah untuk memuat lebih banyak tweet
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break
        last_height = new_height

    driver.quit()
    print(f"Data yang berhasil diambil: {tweets}")  # Debugging
    return tweets

# Route Utama
@app.route('/', methods=['GET', 'POST'])
def index():
    tweets = []
    keyword = ""
    if request.method == 'POST':
        keyword = request.form['keyword']
        tweets = get_tweets(keyword)

    # Jika tidak ada tweet, tampilkan pesan
    if not tweets:
        return render_template('index.html', tweets=tweets, graph_html="", keyword=keyword, message="Tidak ada data ditemukan!")

    # Buat DataFrame untuk visualisasi
    df = pd.DataFrame(tweets)

    # Tambahkan validasi untuk memastikan kolom sentiment ada
    if 'sentiment' not in df.columns:
        print("Tidak ada kolom 'sentiment' pada DataFrame.")  # Debugging
        return render_template('index.html', tweets=tweets, graph_html="", keyword=keyword, message="Gagal memuat data sentimen!")

    sentiment_counts = df['sentiment'].value_counts()

    # Buat Grafik Pie
    fig = go.Figure(data=[go.Pie(labels=sentiment_counts.index, values=sentiment_counts.values)])
    fig.update_layout(title='Distribusi Sentimen')

    # Konversi Grafik ke HTML
    graph_html = pio.to_html(fig, full_html=False)

    return render_template('index.html', tweets=tweets, graph_html=graph_html, keyword=keyword, message="")

if __name__ == '__main__':
    app.run(debug=True)
