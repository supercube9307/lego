import webbrowser
import json
import requests
from requests_oauthlib import OAuth1
from getpass import getpass
from time import sleep

class lego_set:

    def __init__(self, piece_list: list, id: str, name: str, status: str):
        self.piece_list = piece_list
        self.id = id
        self.name = name
        self.status = status

    def bundle_json(self, **kwargs) -> str:

        piece_list_as_json = []
        for piece in self.piece_list:
            piece_list_as_json.append(json.loads(piece.bundle_json()))

        json_str = {"name":self.name, "id": self.id, "status": self.status, "piece_list":piece_list_as_json}

        return(json.dumps(json_str, **kwargs))
    
    def view_instructions(self):
        webbrowser.open(f"https://www.lego.com/en-us/service/building-instructions/{self.id}")

    def fetch_price_current(self, auth) -> str:

        if self.status.lower() == "new":
            status_letter = "N"
        else:
            status_letter = "U"

        url = f"https://api.bricklink.com/api/store/v1/items/set/{self.id}-1/price?guide_type=sold&new_or_used={status_letter}"

        response = requests.get(url, auth=auth)
        response_json = json.loads(response.text)

        set_message = "Bricklink, " + self.name + ": " + response_json["meta"]["message"]
        print(set_message)

        if response_json["meta"]["message"] == "OK":
            qty_avg_price = response_json["data"]["qty_avg_price"]
        else:
            qty_avg_price = "0.00"

        return("$" + qty_avg_price)

    def fetch_price_retail(self, auth) -> str:

        sleep(0.1)

        apiKey = auth["apiKey"]
        userHash = auth["userHash"]

        url = 'https://brickset.com/api/v3.asmx/'
        
        params_query = {'setNumber': f'{self.id}-1'}
        params_request = {"apiKey": apiKey, "userHash": userHash, "params": json.dumps(params_query)}

        response = requests.post(url+"getSets", params_request)
        response_json = json.loads(response.text)

        set_message = "Brickset, " + self.name + ": " + response_json["status"]
        print(set_message)

        if response_json["status"] == "success":
            retail_price = str(response_json["sets"][0]["LEGOCom"]["US"]['retailPrice'])
        else:
            retail_price = "0.00"
        
        return("$" + retail_price)



class piece:
    def __init__(self, count: int, color: str, type: str):
        self.count = count
        self.color = color
        self.type = type

    def bundle_json(self) -> str:
        
        return json.dumps({"type": self.type, "color": self.color, "count": self.count})



def verify_auth_bricklink():
    # form oauth token

    with open("local_data/credentials_file_bricklink.txt") as credentials_file:
        key_list = credentials_file.read().split("\n")
        [consumer_key, consumer_secret, token_value, token_secret] = [key_list[x] for x in range(4)]
    auth = OAuth1(consumer_key, consumer_secret, token_value, token_secret)

    return auth

def get_brickset_apiKey() -> str:

    with open("local_data/credentials_file_brickset.txt") as credentials_file:
        apiKey = credentials_file.read().split("\n")[0]

    return apiKey

def verify_auth_brickset():
    
    url = 'https://brickset.com/api/v3.asmx/'

    apiKey = get_brickset_apiKey()

    auth_verified = False
    while auth_verified == False:
        username = input("Please input Brickset Username: ")
        password = getpass("Please input Brickset Password: ")
        response = requests.post(url+"/login", {"apiKey": apiKey, "username": username, "password": password})
        
        try:
            hash = json.loads(response.text)["hash"]
        except KeyError: 
            print("Invalid Login. Try Again")
            continue
        auth_verified = True

    return({"apiKey":apiKey, "userHash":hash})
