from urllib.parse import urljoin

from bs4 import BeautifulSoup as bs

import requests
import csv
import re
import time
import random

session = requests.Session()
base_url = 'https://immovlan.be/'

"""
with open('./src/cities2.csv', newline='') as csvfile:

    csv_reader = csv.reader(csvfile, delimiter=';', quotechar='|')
    for row, col in enumerate(csv_reader):
        if row == 1:
            zip_code = f'{col[0]}-{col[1]}'
"""

list_provinces = ['brussels', 'antwerp', 'east-flanders', 'vlaams-brabant', 'hainaut', 'liège', 'limburg', 'luxembourg', 'namur', 'brabant-wallon', 'west-flanders']
province = 'brussels'

page = 1

#zip_code = '1000-Brussels'
# select only houses, appartments
type_property = ['apartment', 'house']
#property_endpoint = f'en/real-estate?transactiontypes=for-sale,in-public-sale&propertytypes=apartment&towns={zip_code}&page={page}noindex=1'



headers =  {
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

# Initialise CSV file (columns)
with open("result.csv", "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        'Localisation','Type property', 'Price', 'Number of rooms', 'Living Area',
        'Kitchen equiped', 'Furnished', 'Terrace', 'Terrace Area',
        'Garden', 'Garden Area', 'Land Area', 'Numb facades',
        'Swimming pool', 'State of the building'
    ])

for province in list_provinces:
    for type in type_property:
        # page 1 to get number of listings
        property_endpoint = f'en/real-estate?transactiontypes=for-sale,in-public-sale&propertytypes={type}&provinces={province}&page={page}'
        req = session.get(urljoin(base_url, property_endpoint), headers=headers)
        #time.sleep(5)
        print(req.status_code)
        # for specific elements: driver.find_elements_by_xpath(xpath_expression)
        soup = bs(req.content, 'lxml')

        # Get total listed properties for search
        texts = soup.find_all('div', {'class':'col-12 mb-2'})
        text_listed_properties = 0
        for text in texts:
            text_listed_properties = text.get_text()
            break
        
        # Get numbers of listed properties
        # This pattern matches the beginning of the string ^, skips any non-digit characters \D*, and then captures the first sequence of digits (\d+).
        parameter = r'^\D*(\d+)'
        try:
            total_listed_properties = int(re.findall(parameter, text_listed_properties)[0])
        except:
            print(f"Could not find number of listings for {province} - {type}")
            continue

        # Divide by 20 to assess number of pages
        numb_of_pages = int(total_listed_properties/20)
        if numb_of_pages%20 > 0:
            numb_of_pages += 1
        print(f"Total properties: {total_listed_properties} | Pages: {numb_of_pages}")

        link_list = [] #empties link list
        full_link = []

    #for type in type_property:
        
        for page in range(numb_of_pages):
            property_endpoint = f'en/real-estate?transactiontypes=for-sale,in-public-sale&propertytypes={type}&provinces={province}&page={page}'
            #house_endpoint = f'en/real-estate?transactiontypes=for-sale,in-public-sale&propertytypes=house&towns={zip_code}&noindex=1'

            req = session.get(urljoin(base_url, property_endpoint), headers=headers)
            print(req.status_code)
            soup = bs(req.content, 'lxml')

            for a in soup.find_all('a', href=True):
                if '/en/detail/' in a['href']:
                    #full_link = urljoin(base_url, a['href'])  # .split('?')[0]) Remove tracking/query params
                    full_link = a['href']
                    if full_link not in link_list:
                        link_list.append(full_link)
            print(property_endpoint)
            print(page)
            print(link_list)

            # Loop through the links and get the requested data
            df_all_properties = []
            
            # Define headers to mimic a browser (avoids blocks or bot detection)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36"
            }
            
        for prop in link_list:
            try:
                df_data = []
                df_property = {'Localisation':province, 'Type property':type,
                            'Price':'none',
                            'Number of rooms':'none',
                                'Living Area':'none',
                                'Kitchen equiped':'none',
                                'Furnished':'none',
                                'Terrace':'none',
                                'Terrace Area': 'none',
                                'Garden':'none',
                                'Garden Area': 'none',
                                'Land Area':'none',
                                'Numb facades':'none',
                                'Swimming pool':'none',
                                'State of the building':'none'}
                
                print(f"\n Checking: {prop}")
                detail_resp = session.get(prop, headers=headers, timeout=20)

                # HTTP status code check
                if detail_resp.status_code != 200:
                    print(f"Error: Received HTTP {detail_resp.status_code}")
                    continue

                detail_soup = bs(detail_resp.content, "lxml")
                
                #
                # Try finding the price element
                #
                
                # finding parent <ul> tag
                ul_tag = detail_soup.find("div", {'class':'financial w-100'}).find("ul")
                            
                # Checking ul tags
                if ul_tag:
                    # find li tags
                    li_tags = ul_tag.find_all("li") 
                    for li in li_tags:
                        if 'Price' in li.get_text():
                            text = li.get_text(strip=True)
                            print(text)   
                            # Regex to capture numbers
                            match = re.search(r"(\d[\d\s\u202f]*\d)", text)
                            raw_price = match.group(1)  # matching the first subgroup
                            price_property = int(re.sub(r"[\s\u202f]", "", raw_price)) #replaces empty except number and cinvert to int
                            df_property['Price']=price_property
                else:
                    print("ul tag not found")
                time.sleep(random.uniform(0.1, 0.3))   #second waiting 
                
                # find all divs with class "data-row-wrapper"
                div_tags = detail_soup.find_all("div", {'class': 'data-row-wrapper'})

                for div_tag in div_tags:
                    h_tags = div_tag.find_all("h4")
                    p_tags = div_tag.find_all("p")  # details

                    # Concatenate h4[i] + p[i] 
                    for h, p in zip(h_tags, p_tags):
                        text1 = h.get_text(strip=True)
                        text2 = p.get_text(strip=True) 
                        combined = f"{text1}: {text2}"
                        #print(combined)
                        df_data.append(combined)
                
            
            except requests.exceptions.RequestException as e:
                print(f"Network error: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")

            # looping from list, clean data             

            for df_el in df_data:
                if 'Number of bedrooms' in df_el:
                    # Regex to capture numbers
                    match = re.search(r'\d+', df_el)
                    numb_rooms_property = int(match.group()) #replaces empty except number and cinvert to int
                    df_property['Number of rooms']=numb_rooms_property
                    
                if 'Livable surface' in df_el:
                    # Regex to capture numbers
                    match = re.search(r'\d+', df_el)
                    #raw_livable = match.group()  # matching the first subgroup
                    livable_property = int(match.group()) #replaces empty except number and cinvert to int
                    df_property['Living Area']=livable_property

                if 'Kitchen equipment' in df_el:
                    if 'Super equipped' in df_el:
                        kitchen_equiped = 1
                    else:
                        kitchen_equiped = 0
                    df_property['Kitchen equiped']=kitchen_equiped
                
                if 'Furnished: Yes' in df_el:
                    furnished = 1
                    df_property['Furnished']=furnished
                
                if 'Surface terrace' in df_el:
                    terrace = 1
                    df_property['Terrace']=terrace
                    # Regex to capture numbers
                    match = re.search(r'\d+', df_el)
                    #surface_terrace_property = int(re.sub(pat_only_number, "", raw_terrace)) #replaces empty except number and cinvert to int
                    surface_terrace_property = int(match.group()) #replaces empty except number and cinvert to int
                    df_property['Terrace Area']=surface_terrace_property
                
                if 'Surface garden' in df_el:
                    garden = 1
                    df_property['Garden']=garden
                    # Regex to capture numbers
                    match = re.search(r'\d+', df_el)
                    surface_garden_property = int(match.group()) #replaces empty except number and cinvert to int
                    df_property['Garden Area']=surface_garden_property
                
                if 'Total land surface' in df_el:
                    # Regex to capture numbers
                    match = re.search(r'\d+', df_el)
                    #raw_land = match.group(1)  # matching the first subgroup
                    #surface_land_property = int(re.sub(pat_only_number, "", raw_land)) #replaces empty except number and cinvert to int
                    surface_land_property = int(match.group()) #replaces empty except number and cinvert to int
                    df_property['Land Area']=surface_land_property
                
                if 'Number of facades' in df_el:
                    # Regex to capture numbers
                    match = re.search(r'\d+', df_el)
                    facades_property = int(match.group()) #replaces empty except number and cinvert to int
                    df_property['Numb facades']=facades_property
                
                if 'Swimming pool: Yes' in df_el:
                    df_property['Swimming pool']=1
                    
                if 'State of the property' in df_el:
                    match = re.search(r'[^.+:]+$', df_el)
                    state_property = match.group()
                    df_property['State of the building']=state_property  
                    
            print(df_property)
            property_values = [df_property[key] for key in df_property]
            df_all_properties.append(property_values)        # per page
        
        with open("result.csv", "a", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(df_all_properties)