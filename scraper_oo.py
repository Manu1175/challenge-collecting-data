import csv
import re
import time
import random
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup as bs

class ImmoScraper:
    def __init__(self):
        # initiate attributes
        self.base_url = 'https://immovlan.be/'
        self.session = requests.Session()
        self.provinces = ['brussels', 'antwerp', 'east-flanders', 'vlaams-brabant', 'hainaut', 'liège', 'limburg', 'luxembourg', 'namur', 'brabant-wallon', 'west-flanders']
        #self.cities = []
        self.types = ['apartment', 'house']
        self.headers = {
           'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) '
            'Gecko/20100101 Firefox/115.0'
        ),
        'Accept': (
            'text/html,application/xhtml+xml,application/xml;q=0.9,'
            'image/avif,image/webp,*/*;q=0.8'
        ),
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'TE': 'trailers',
        }
        self.all_properties = []

    def initialize_csv(self, filename="result.csv"):
        # creates column headers
        with open(filename, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Localisation', 'Type property', 'Price', 'Number of rooms', 'Living Area',
                'Kitchen equipped', 'Furnished', 'Terrace', 'Terrace Area',
                'Garden', 'Garden Area', 'Land Area', 'Numb facades',
                'Swimming pool', 'State of the building'
            ])
            
    """def loading_cities(self):
        with open('./src/cities2.csv', newline='') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for row, col in enumerate(csv_reader):
                self.cities.append(f'{col[0]}-{col[1]}')
                #if row == 1:
                #    zip_code = f'{col[0]}-{col[1]}'
"""
    
    def get_total_pages(self, province, property_type):
        # obtains the number of listings and divides by 20
        url = urljoin(self.base_url, f'en/real-estate?transactiontypes=for-sale,in-public-sale&propertytypes={property_type}&provinces={province}')
        resp = self.session.get(url, headers=self.headers)
        soup = bs(resp.content, 'lxml')

        try:
            text = soup.find('div', {'class':'col-12 mb-2'}).get_text()
            total_props = int(re.findall(r'\d+', text)[0])
            total_pages = (total_props // 20) + (1 if total_props % 20 else 0)
            return total_pages
        except Exception as e:
            print(f"[!] Failed to get total pages for {province}-{property_type}: {e}")
            return 0

    def get_property_links(self, province, property_type, page):
        # obtains the link lists of total properties on landing page
        url = urljoin(self.base_url, f'en/real-estate?transactiontypes=for-sale,in-public-sale&propertytypes={property_type}&provinces={province}&page={page}')
        resp = self.session.get(url, headers=self.headers)
        soup = bs(resp.content, 'lxml')
        links = []

        for a in soup.find_all('a', href=True):
            if '/en/detail/' in a['href']:
                full_link = urljoin(self.base_url, a['href'].split('?')[0])
                if full_link not in links:
                    links.append(full_link)
        return links

    def parse_property(self, url, province, property_type):
        try:
            resp = self.session.get(url, headers=self.headers, timeout=15)
            if resp.status_code != 200:
                return None
            soup = bs(resp.content, 'lxml')
            # initiates dictionary
            result = {
                'Localisation': province,
                'Type property': property_type,
                'Price': 'none', 'Number of rooms': 'none', 'Living Area': 'none',
                'Kitchen equipped': 'none', 'Furnished': 'none',
                'Terrace': 'none', 'Terrace Area': 'none',
                'Garden': 'none', 'Garden Area': 'none',
                'Land Area': 'none', 'Numb facades': 'none',
                'Swimming pool': 'none', 'State of the building': 'none'
            }

            # Extract price
            try:
                price_tag = soup.find("div", {'class': 'financial w-100'}).find("ul").find("li")
                match = re.search(r"(\d[\d\s\u202f]*\d)", price_tag.get_text())
                if match:
                    price = int(re.sub(r"[\s\u202f]", "", match.group(1)))
                    result['Price'] = price
            except:
                pass

            data_tags = soup.find_all("div", {'class': 'data-row-wrapper'})
            for div in data_tags:
                h_tags = div.find_all("h4")
                p_tags = div.find_all("p")
                for h, p in zip(h_tags, p_tags):
                    label = h.get_text(strip=True)
                    value = p.get_text(strip=True)
                    combined = f"{label}: {value}"
                    
                    # extract rest of data
                    if 'Number of bedrooms' in label:
                        result['Number of rooms'] = int(re.search(r'\d+', value).group())
                    elif 'Livable surface' in label:
                        result['Living Area'] = int(re.search(r'\d+', value).group())
                    elif 'Kitchen equipment' in label:
                        result['Kitchen equipped'] = 1 if 'Super equipped' in value else 0
                    elif 'Furnished' in label and 'Yes' in value:
                        result['Furnished'] = 1
                    elif 'Surface terrace' in label:
                        result['Terrace'] = 1
                        result['Terrace Area'] = int(re.search(r'\d+', value).group())
                    elif 'Surface garden' in label:
                        result['Garden'] = 1
                        result['Garden Area'] = int(re.search(r'\d+', value).group())
                    elif 'Total land surface' in label:
                        result['Land Area'] = int(re.search(r'\d+', value).group())
                    elif 'Number of facades' in label:
                        result['Numb facades'] = int(re.search(r'\d+', value).group())
                    elif 'Swimming pool' in label and 'Yes' in value:
                        result['Swimming pool'] = 1
                    elif 'State of the property' in label:
                        result['State of the building'] = value
            return result

        except Exception as e:
            print(f"[!] Error scraping {url}: {e}")
            return None

    def scrape_all(self):
        # main function
        for province in self.provinces:
            for property_type in self.types:
                total_pages = self.get_total_pages(province, property_type)
                print(f"Scraping {province} - {property_type}: {total_pages} pages.")
                for page in range(1, total_pages + 1):
                    links = self.get_property_links(province, property_type, page)
                    for link in links:
                        print(f"  - {link}")
                        data = self.parse_property(link, province, property_type)
                        if data:
                            self.all_properties.append(data)
                            time.sleep(random.uniform(0.2, 0.4))

    def save_to_csv(self, filename="result.csv"):
        with open(filename, "a", newline='') as f:
            writer = csv.writer(f)
            for prop in self.all_properties:
                writer.writerow([prop[key] for key in prop])


if __name__ == "__main__":
    scraper = ImmoScraper()
    scraper.initialize_csv()
    #scraper.loading_cities()
    scraper.scrape_all()
    scraper.save_to_csv()