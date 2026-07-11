import json
import requests
from time import sleep

class lego_set:

    def __init__(self, piece_list: list, id: str, name: str, status: str):
        self.piece_list = piece_list
        self.id = id
        self.name = name
        self.status = status
        self.current_price = ""
        self.retail_price = ""

    def bundle_json(self, **kwargs) -> str:

        piece_list_as_json = []
        for piece in self.piece_list:
            piece_list_as_json.append(json.loads(piece.bundle_json()))

        json_str = {"name":self.name, "id": self.id, "status": self.status, "piece_list":piece_list_as_json}

        return(json.dumps(json_str, **kwargs))

    def fetch_price_current(self, auth):

        if self.status.lower() == "new":
            status_letter = "N"
        else:
            status_letter = "U"

        url = f"https://api.bricklink.com/api/store/v1/items/set/{self.id}-1/price?guide_type=sold&new_or_used={status_letter}"

        response = requests.get(url, auth=auth)
        response_json = json.loads(response.text)

        set_message = "Bricklink, " + self.name + ": " + response_json["meta"]["message"]
        print(set_message)

        try:
            self.current_price = "$" + response_json["data"]["qty_avg_price"]
        except:
            self.current_price = "$0.00"

    def fetch_price_retail(self, auth):

        if self.retail_price != "":
            return

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

        try:
            self.retail_price = self.fetch_price_retail(auth)
        except:
            self.retail_price = "0.00"

class piece:
    def __init__(self, count: int, color: str, type: str):
        self.count = count
        self.color = color
        self.type = type

    def bundle_json(self) -> str:
        
        return json.dumps({"type": self.type, "color": self.color, "count": self.count})
    
    def check_valid(self, other):
        piece_id_valid = self.type == other.type
        piece_quantity_valid = other.count <= self.count
        if other.color != "":
            piece_color_valid = self.color == other.color
        else:
            piece_color_valid = True
        
        return(piece_id_valid and piece_color_valid and piece_quantity_valid)
