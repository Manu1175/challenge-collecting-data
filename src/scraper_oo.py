import re
import csv
import time
import pandas as pd
from urllib.parse import urljoin

from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class immo_scraper:
    def __init__(self, zip_file:str):
        self.base_url:str = 'https://immovlan.be/'
        self.zip_code = self._load_zip(zip_file)
        self.driver = self._init_driver()
        self.wait = WebDriverWait(self.driver, 20)
        self.data = []
    
    def __str__(self):
        pass

    def _load_zip(self, csv_path: str) -> str:
          with open(csv_path, newline='') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for row, col in enumerate(csv_reader):
                if row == 1:
                    return f'{col[0]}-{col[1]}'
            raise ValueError("No ZIP code found in CSV.")
    
    def _init_driver(self):
        options = Options()
        options.headless = True
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        return webdriver.Chrome(options=options)
    
    def _get_listing_page(self):
        endpoint = f'en/real-estate?transactiontypes=for-sale,in-public-sale&propertytypes=house,apartmen&towns={self.zip_code}&noindex=1'
        full_url = urljoin(self.BASE_URL, endpoint)
        self.driver.get(full_url)
        try:
            cookie_button = self.wait.until(EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button")))
            cookie_button.click()
        except Exception:
            pass  # Cookie banner may not appear
        time.sleep(2)
        return self.driver.page_source
    
    def extract_property_links():
        links = set()
        for a in soup.find_all('a', href=True):
            if '/en/detail/' in a['href']:
                full_link = urljoin(self.BASE_URL, a['href'].split('?')[0])
                links.add(full_link)
        return list(links)
    
    def _get_total_pages(self, soup):
        divs = soup.find_all('div', {'class': 'col-12 mb-2'})
        for div in divs:
            match = re.search(r'^\D*(\d+)', div.get_text())
            if match:
                total_props = int(match.group(1))
                return (total_props // 20) + (1 if total_props % 20 else 0)
        return 1
    
    def _extract_price_from_page(self, url: str) -> int:
        try:
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "detail__header_price_data")))
            price_elem = self.driver.find_element(By.CLASS_NAME, "detail__header_price_data")
            match = re.search(r'\d[\d\s,.]*', price_elem.text)
            if match:
                number_str = re.sub(r'[^\d]', '', match.group(0))
                return int(number_str)
        except Exception as e:
            print(f"Error extracting price from {url}: {e}")
        return None  
    
    def scrape(self):
        html = self._get_listing_page()
        soup = bs(html, "lxml")

        num_pages = self._get_total_pages(soup)
        print(f"🔎 Found {num_pages} pages")

        all_links = set()
        for page in range(1, num_pages + 1):
            print(f"📄 Scraping page {page}")
            if page > 1:
                paged_url = f"{self.BASE_URL}en/real-estate?page={page}&transactiontypes=for-sale,in-public-sale&propertytypes=house,apartmen&towns={self.zip_code}&noindex=1"
                self.driver.get(paged_url)
                time.sleep(2)
                soup = bs(self.driver.page_source, "lxml")
            links = self._extract_property_links(soup)
            all_links.update(links)

        print(f"🔗 Total property links: {len(all_links)}")

        for link in all_links:
            price = self._extract_price_from_page(link)
            self.data.append({"url": link, "price": price})
  
        
    def connect(self, zip_code):
        
        #session = requests.Session()
        #base_url = 'https://immovlan.be/'

        with open('./src/cities2.csv', newline='') as csvfile:

            csv_reader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for row, col in enumerate(csv_reader):
                if row == 1:
                    zip_code = f'{col[0]}-{col[1]}'

        #zip_code = '1000-Brussels'
        # select only houses, appartments
        prop_endpoint = f'en/real-estate?transactiontypes=for-sale,in-public-sale&propertytypes=house,apartmen&towns={zip_code}&noindex=1'

        options = webdriver.ChromeOptions()
        # to make the browser appear more like a regular user-controlled browser and less like an automated bot
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        driver = webdriver.Chrome(options=options)
        driver.get(urljoin(self.base_url, prop_endpoint))


        wait = WebDriverWait(driver, 2)
        cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@id='didomi-notice-agree-button']")))
        cookie_button.click()


        #<div class="col-12 mb-2">529&nbsp;results&nbsp;(1&nbsp;-&nbsp;20)</div>
        #<div class="col-12 mb-2">680&nbsp;results&nbsp;(1&nbsp;-&nbsp;20)</div>
        #r'(\d+)|\[(?:.+?(?<!\\)\]\()'
        url = driver.page_source
        # for specific elements: driver.find_elements_by_xpath(xpath_expression)
        soup = bs(url, 'lxml')

        # Get total listed properties for search
        texts = soup.find_all('div', {'class':'col-12 mb-2'})
        for text in texts:
            text_listed_properties = text.get_text()

        # Get numbers of listed properties
        # This pattern matches the beginning of the string ^, skips any non-digit characters \D*, and then captures the first sequence of digits (\d+).
        parameter = r'^\D*(\d+)'
        total_listed_properties = int(re.findall(parameter, text_listed_properties)[0])
        print(total_listed_properties)

        # Divide by 20 to assess number of pages
        numb_of_pages = int(total_listed_properties/20)
        if numb_of_pages%20 > 0:
            numb_of_pages += 1
        print(numb_of_pages)

        link_list = []
        full_link = []

        for a in soup.find_all('a', href=True):
                if '/en/detail/' in a['href']:
                        full_link = urljoin(base_url, a['href'].split('?')[0])  # Remove tracking/query params
                if full_link not in link_list:
                    link_list.append(full_link)

        # Loop through the links and get the prices
        for prop in link_list:
            try:
                driver.get(prop)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "detail__header_price_data"))
                )
                # Gets price if present in html
                price_elem = driver.find_element(By.CLASS_NAME, "detail__header_price_data")
                print(f"{prop} => {price_elem.text}")

            except Exception as e:
                print(f"{prop} => Error: {e}")

        #driver.quit()

    def save():
        # Put results into a dataframe
        df = pd.DataFrame(list_of_strings)
        # Export to CSV
        df.to_csv('output/results.csv')
        
"""
    Locality
    Type of property (House/apartment)
    Subtype of property (Bungalow, Chalet, Mansion, ...)
    Price
    Type of sale (Exclusion of life sales)
    Number of rooms
    Living Area
    Fully equipped kitchen (Yes/No)
    Furnished (Yes/No)
    Open fire (Yes/No)
    Terrace (Yes/No)
        If yes: Area
    Garden (Yes/No)
        If yes: Area
    Surface of the land
    Surface area of the plot of land
    Number of facades
    Swimming pool (Yes/No)
    State of the building (New, to be renovated, ...)
    
    
    # === Usage ===
if __name__ == "__main__":
    scraper = ImmovlanScraper("./src/cities2.csv")
    scraper.scrape()

    df = scraper.to_dataframe()
    print(df.head())
    df.to_csv("immovlan_prices.csv", index=False)

    scraper.quit()
"""