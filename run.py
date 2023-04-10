from bs4 import BeautifulSoup
from lxml import etree
import requests
from PyPDF2 import PdfReader
import json
import zulip
import re
import datetime
import os
import chevron
            
emoji_dict = {"favorit": " :piglet: :calf: ", 
              "vegetar": " :eggplant: :cheese: ", 
              "vegansk":  " :herb: :apple: ",
              "glutenfri": " :prohibited: :bread: ",
              "halal": " :moon: :calf: "}

menudict = {} 
dayslist = [] #add list empty list to hold the days in the coming week.
currentweek = []
            
def render_message(menudict):
    day_template = """```spoiler {{ day }}\n\n{{content}}```\n"""
    render = ""
    for day in range(0,len(menudict)-1): # -1 because of empty page
        content_str = ""
        for key in menudict:
            if key == 'days':
                continue
            content_str += "##" + emoji_dict[key] + str(key).upper() + emoji_dict[key]
            content_str += str(menudict[key][day])
        render += chevron.render(day_template, {'day': dayslist[day], 'content': content_str})
    return(render)

   
if os.name == 'nt':
    client = zulip.Client(config_file="zuliprc")
else:
    client = zulip.Client() #get creds from environment variable
 
BASE_URL =  "https://torvekoekken.dk"
FAVORIT_URL = "https://torvekoekken.dk/sjaelland/frokostordning/favorit-buffet"
PORTIONS_URL = "https://torvekoekken.dk/sjaelland/frokostordning/portionsanretninger"
  
HEADERS = ({'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',\
            'Accept-Language': 'en-US, en;q=0.5'})


urldict = {} 

webpage = requests.get(FAVORIT_URL, headers=HEADERS)
soup = BeautifulSoup(webpage.content, "html.parser")
dom = etree.HTML(str(soup))
urldict["favorit"] = dom.xpath('/html/body/main/div/div/div[1]/div/div[1]/div/div/div/div[2]/button[2]/@onclick')

  
webpage = requests.get(PORTIONS_URL, headers=HEADERS)
soup = BeautifulSoup(webpage.content, "html.parser")
dom = etree.HTML(str(soup))
urldict["vegetar"] = dom.xpath('/html/body/main/div/div/div[4]/div/div[1]/div/div/div/div[2]/button[2]/@onclick')
urldict["vegansk"] = dom.xpath('/html/body/main/div/div/div[6]/div/div[1]/div/div/div/div[2]/button[2]/@onclick')
urldict["glutenfri"] = dom.xpath('/html/body/main/div/div/div[5]/div/div[2]/div/div/div/div[2]/button[2]/@onclick')
urldict["halal"] = dom.xpath('/html/body/main/div/div/div[7]/div/div[2]/div/div/div/div[2]/button[2]/@onclick')

# ["location.href='/Files/Files/Branding RAPIDO/Favorit buffet menuer/Favorit buffet uge 9 2023.pdf'"]
# split by qoutation-mark
 
for category,url in urldict.items():
    url = BASE_URL + str(url).split('\'')[1]
    #print(url)
    r = requests.get(url, allow_redirects=True)
    open(category+'.pdf', 'wb').write(r.content)
    reader = PdfReader(category+'.pdf')
    menudict[category] = []
    for count, page in enumerate(reader.pages):
        text = reader.pages[count].extract_text()
        current_week = re.search(r'\w*UGE \w*',text)
        if current_week is None:
            continue
        if str(current_week[0]) not in currentweek:
            currentweek.append(current_week[0])   
        current_day = re.search(r'[a-åA-å]{3,4}\w*DAG\w*',text)
        if current_day is None:
            continue
        if str(current_day[0]) not in dayslist:
            dayslist.append(current_day[0])    
        text = re.sub(r'\(.*\)', '', text) # remove allergene markings
        text = re.sub(r'.*[a-åA-å]{3,4}\w*DAG\w*', '', text) # remove days
        text = text.split('Tallene')[0] #remove allergene text at the end of string
        menudict[category].append(text)
print(currentweek)
todaystext = render_message(menudict)    

stream_name = os.environ.get("STREAM")
print("sending menu of the day to:")
print(stream_name)

if os.name == 'nt':
    print("sending private message")
    user_id = 390558
    request = {
    "type": "private",
    "to": [user_id],
    "content": todaystext,
    }
    
    
else:
    request = {
        "type": "stream",
        "to": stream_name,
        "topic": str(current_week),
        "content": todaystext,
    }
    
    
result = client.send_message(request)
print(result)   
