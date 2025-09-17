import time
import json
import requests
from requests_oauthlib import OAuth1

with open("Identified Lego Sets - List.csv", "r") as list_file:
    list_text = list_file.read()

sets_list = list_text.split("\n")
sets_list.pop(0)
sets_list.pop()
price_list = ""

index = 0

consumer_key = "EF0ADB3D01AF498D98F7713DAAC16F25"
consumer_secret = "5149E716679E443CB57D807C59F019DE"
#apartment
token = "E76508D01D0944B993B72DC3BBA11AEF"
token_secret = "392393EACFF24BA282A802D90227D0D5"
#school
#token = "0AF662912C5E488C81657A7E4CFF8D9E"
#token_secret = "E7E6A1F9DDD44243856A706C44731001" 

auth = OAuth1(consumer_key,
              consumer_secret,
              token,
              token_secret           
              )


for set_data in sets_list:
    
##    if index == 20:
##        break
##    index += 1 

    set_data = set_data.split(",")
    set_id = str(set_data[1])    
    set_url = "https://api.bricklink.com/api/store/v1/items/set/" + set_id + "-1/price?guide_type=sold&new_or_used=U"
               
    response = requests.get(set_url, auth=auth)
    print(response.text+"\n")
          
    qty_avg_price_index = response.text.find("qty_avg_price")
    unit_quantity_index = response.text.find("unit_quantity")
    qty_avg_price = response.text[qty_avg_price_index-1:unit_quantity_index-2]

    colon_index = qty_avg_price.find(":")
    qty_avg_price = qty_avg_price[colon_index+2:-1]

##    print(qty_avg_price)
    
    set_data[-1] = "$" + qty_avg_price
    
    set_data = ",".join(set_data)
    print(set_data+"\n\n\n")
    price_list = price_list + set_data +"\n"


with open("Identified Lego Sets Prices.csv", "w") as list_file_prices:
    list_file_prices.write(price_list)
