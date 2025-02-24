from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Setup Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Buka halaman Twitter/X dan cari kata kunci
url = "https://twitter.com/search?q=python&src=typed_query"
driver.get(url)
time.sleep(5)

# Scroll beberapa kali untuk load lebih banyak tweet
for i in range(3):
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
    time.sleep(3)

# Ambil tweet
tweets = driver.find_elements(By.XPATH, "//div[@data-testid='tweetText']")
for index, tweet in enumerate(tweets):
    print(f"{index+1}. {tweet.text}")

# Tutup browser
driver.quit()
