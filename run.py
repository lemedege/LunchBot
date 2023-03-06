from bs4 import BeautifulSoup
from lxml import etree
import requests
from PyPDF2 import PdfReader
import json
import zulip
import re
import datetime
import os

client = zulip.Client(config_file="zuliprc")
 
BASE_URL =  "https://torvekoekken.dk"
FAVORIT_URL = "https://torvekoekken.dk/sjaelland/frokostordning/favorit-buffet"
VERDENS_URL = "https://torvekoekken.dk/sjaelland/frokostordning/favorit-buffet"
PORTIONS_URL = "https://torvekoekken.dk/sjaelland/frokostordning/portionsanretninger"
  
HEADERS = ({'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',\
            'Accept-Language': 'en-US, en;q=0.5'})
  
webpage = requests.get(PORTIONS_URL, headers=HEADERS)
soup = BeautifulSoup(webpage.content, "html.parser")
dom = etree.HTML(str(soup))
urldict = {} 
urldict["favorit"] = dom.xpath('/html/body/main/div/div/div[3]/div/div[2]/div/div/div/div[2]/button[2]/@onclick')
urldict["vegetar"] = dom.xpath('/html/body/main/div/div/div[4]/div/div[1]/div/div/div/div[2]/button[2]/@onclick')
urldict["gluten"] = dom.xpath('/html/body/main/div/div/div[5]/div/div[2]/div/div/div/div[2]/button[2]/@onclick')
urldict["vegansk"] = dom.xpath('/html/body/main/div/div/div[6]/div/div[1]/div/div/div/div[2]/button[2]/@onclick')
urldict["halal"] = dom.xpath('/html/body/main/div/div/div[7]/div/div[2]/div/div/div/div[2]/button[2]/@onclick')


# ["location.href='/Files/Files/Branding RAPIDO/Favorit buffet menuer/Favorit buffet uge 9 2023.pdf'"]
# split by qoutation-mark

    
menudict = {} 
   
   
for category,url in urldict.items():
    url = BASE_URL + str(url).split('\'')[1]
    #print(url)
    r = requests.get(url, allow_redirects=True)
    open(category+'.pdf', 'wb').write(r.content)
    reader = PdfReader(category+'.pdf')
    menudict[category] = []
    for count, page in enumerate(reader.pages):
        text = reader.pages[count].extract_text()
        text = re.sub(r'\(.*\)', '', text) # remove allergene markings
        text = re.sub(r'.*([a-åA-å]{3,4}[DAG])\w+', '', text) # remove allergene markings
        text = text.split('Tallene')[0] #remove allergene text at the end of string
        menudict[category].append(text)
    
  

today = datetime.datetime.now()
todaystext = today.strftime("%A").upper() + " WEEK " + today.strftime("%W")
todaystext += ("\n\n")


for key in menudict:
    text = str(key).upper()
    text += '\n'
    text += str(menudict[key][today.weekday()])
    text += '\n'
    todaystext += (text)


stream_name = os.environ.get("STREAM")

print("sending menu of the day to:")
print(stream_name)

request = {
    "type": "stream",
    "to": stream_name,
    "topic": "Week "+ today.strftime("%W"),
    "content": todaystext,
}

#result = client.send_message(request)

