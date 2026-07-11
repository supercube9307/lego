import json
import requests
import webbrowser
import os
from requests_oauthlib import OAuth1
from getpass import getpass
from class_defs import *

def import_user_set_list() -> list:
    # import user list of sets from .csv and extract set data
    with open("local_data/Identified Lego Sets - python_export.csv", "r") as list_file:
        list_text = list_file.read()

    # convert .csv to single list by set
    sets_list = list_text.split("\n")
    # remove headers
    set_headers = sets_list.pop(0).split(",")
    #remove ghost entry
    if sets_list[-1] == "":
        sets_list.pop()

    # convert single nested list to list of lego_set instances
    new_sets_list = []
    for set_data in sets_list:
        set_item_list = set_data.split(",")

        set_instance = lego_set(piece_list = [], name = set_item_list[0], id = set_item_list[1], status = set_item_list[2])
        set_instance.retail_price = set_item_list[3]
        set_instance.current_price = set_item_list[4]
        new_sets_list.append(set_instance)
        
    return (new_sets_list)
    
def write_set_json(set_instance):

    # construct json files where piece lists per set are stored locally
    set_url = "https://api.bricklink.com/api/store/v1/items/set/" + set_instance.id + "-1/subsets"
    response = requests.get(set_url, auth=verify_auth_bricklink())
    json_response = json.loads(response.text)

    set_message = set_instance.id + ": " + json_response["meta"]["message"]
    print(set_message)

    try:
        for piece_data in json_response["data"]:

            piece_id = piece_data["entries"][0]["item"]["no"]
            piece_color = str(piece_data["entries"][0]["color_id"])
            piece_quantity = int(piece_data["entries"][0]["quantity"])

            piece_instance = piece(count=piece_quantity, type=piece_id, color=piece_color)

            set_instance.piece_list.append(piece_instance)

    except KeyError:
        pass

    file_path = f"local_data/sets/set_{set_instance.id}.json"
    with open(file_path, "w") as local_file:
        local_file.write(set_instance.bundle_json(sort_keys=True, indent=4))

def update_prices(sets_list):
    # gather current prices from bricklink and brickset API

    output_text = "Name,ID,Status,Retail Price,Current Price\n"
    brickset_auth = verify_auth_brickset()
    for set_instance in sets_list:

        set_instance.fetch_price_current(verify_auth_bricklink())
        set_instance.fetch_price_retail(brickset_auth)

        line_text = f"{set_instance.name},{set_instance.id},{set_instance.status},{set_instance.retail_price},{set_instance.current_price}\n"
        
        output_text += line_text

    with open("local_data/Identified Lego Sets - python_export.csv", "w") as list_file:

        list_file.write(output_text)

def decompose_piece_list(pieces_list):

    # split user supplied list of pieces into list of pieces
    # pieces are stored as a list of [piece id, piece color, piece quantity]

    pieces_list = pieces_list.split(" ")

    return_pieces_list = []
    for piece_entry in pieces_list:
        return_pieces_list.append(parse_piece_input(piece_entry))

    return(return_pieces_list)

def parse_piece_input(piece_entry):
    # Example piece queries:
    # 4522 4006:11 2x58247:11 2x3849
    piece_count = 1
    piece_color = ""

    if "x" in piece_entry:
        piece_entry = str(piece_entry).split("x")
        piece_count = int(piece_entry.pop(0))
        piece_entry = piece_entry[0]

    if ":" in piece_entry:
        piece_entry = str(piece_entry).split(":")
        piece_color = piece_entry.pop(-1)
        piece_entry = piece_entry[0]

        piece_id = piece_entry

    return(piece(count=piece_count, color=piece_color, type=piece_id))

def filter_sets_by_piece_list(pieces_list_user, sets_list):

    # compare user supplied list of pieces to sets list and report matches
    for set_data in sets_list:

        with open(f"local_data/sets/set_{set_data.id}.json", "r") as set_file:
            set_json = json.loads(set_file.read())
        pieces_list_json = set_json["piece_list"]

        [found_pieces_list, found_piece_quantity] = compare_piece_lists(pieces_list_user, pieces_list_json)

        if found_pieces_list == pieces_list_user:
            if len(pieces_list_user) > 1:
                print("Found in set: " + set_data.id)
            else:
                print(str(found_piece_quantity) + " Found in set: " + set_data.id)
    
def compare_piece_lists(pieces_list_user, pieces_list_json):
    #declare found piece quantity here so it can be used for printing results
    found_piece_quantity = "0"
    found_pieces_list = []

    for piece_instance_user in pieces_list_user:

        for piece_json in pieces_list_json:

            piece_instance_json = piece(count = piece_json["count"], color = piece_json["color"], type=piece_json["type"])            

            if piece_instance_json.check_valid(piece_instance_user):
                found_pieces_list.append(piece_instance_user)
                if len(pieces_list_user) == 1:
                    found_piece_quantity = str(piece_instance_json.count)
                continue

    return(found_pieces_list, found_piece_quantity)

def verify_auth_bricklink():
    # form oauth token

    with open("local_data/credentials_file_bricklink.txt") as credentials_file:
        key_list = credentials_file.read().split("\n")
        [consumer_key, consumer_secret, token_value, token_secret] = [key_list[x] for x in range(4)]
    auth = OAuth1(consumer_key, consumer_secret, token_value, token_secret)

    return auth

def verify_auth_brickset():
    
    url = 'https://brickset.com/api/v3.asmx/'

    with open("local_data/credentials_file_brickset.txt") as credentials_file:
        apiKey = credentials_file.read().split("\n")[0]

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

def main_loop():

    welcome_message = """
Type a list of pieces as '[quantity]x[piece id]:[color]' for a list of sets that contain those pieces
    example inputs:'1x4522:11', '4522 4006:11 2x58247:11 2x3849'
Type 'piece list' to create local cache that contains pieces list for each set
Type 'set name [set id]' for the name of the provided set
Type 'update prices' to write the list of current and retail prices to 'sets_current_prices.csv'
Type 'color guide' to view the bricklink color guide
Type 'instructions [Set ID]' to view a set's instructions
Type 'help' to see this message again
Type 'exit' or 'quit' to exit"""

    print(welcome_message)
    
    sets_list = import_user_set_list()

    while True:
        user_request = input("\nPrompt: ").lower()

        if user_request == "exit" or user_request == "quit":
            break

        elif "piece list" in user_request:
            for set_instance in sets_list:
                if os.path.exists(f"local_data/sets/set_{set_instance.id}.json"):
                    continue
                write_set_json(set_instance)
            continue

        elif user_request == "help":
            print(welcome_message)

        elif "set name" in user_request:
            set_id = user_request.split(" ")[-1]

            with open(f"sets/set_{set_id}.json") as json_file:
                json_content = json.loads(json_file.read())
                set_name = json_content["name"]

            print(set_name)

        elif "update prices" in user_request:
            update_prices(sets_list)

        elif user_request == "color guide":
            webbrowser.open("https://v2.bricklink.com/en-us/catalog/color-guide")

        elif "instructions" in user_request:
            set_id = user_request.split(" ")[1]
            webbrowser.open(f"https://www.lego.com/en-us/service/building-instructions/" + set_id)

        else:
            piece_list = decompose_piece_list(user_request)
            filter_sets_by_piece_list(piece_list, sets_list)

if __name__ == "__main__":
    main_loop()
