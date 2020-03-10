import requests
from bs4 import BeautifulSoup
from datetime import datetime

url = 'https://www.aucklandcouncil.govt.nz/rubbish-recycling/rubbish-recycling-collections/Pages/collection-day-detail.aspx?an=12342559369'

response = requests.get(url)

soup = BeautifulSoup(response.text, 'lxml')

# Find parent container for household disposal
container = soup.find('h3', class_="card-title h2").parent.parent

link_container = container.find('div', class_="links")

# Get string date representation
date_elem = link_container.find('span', class_="m-r-1")
is_rubbish_due = link_container.find('span', class_='icon-rubbish') != None
is_recycling_due = link_container.find('span', class_='icon-recycle') != None


print(date_elem.string)

datetime_format = "%A %d %B"
collection_date = datetime.strptime(date_elem.string, datetime_format)
collection_date = collection_date.replace(year=datetime.now().year)

print(collection_date)
print(is_rubbish_due)
print(is_recycling_due)
