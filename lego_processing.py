import time
import json
import requests
from requests_oauthlib import OAuth1


def import_user_set_list():
    # import user list of sets from .csv and extract set data
    with open("Identified Lego Sets - python_export.csv", "r") as list_file:
        list_text = list_file.read()

    # convert .csv to single list by set
    sets_list = list_text.split("\n")
    # remove headers
    set_headers = sets_list.pop(0).split(",")
    #remove ghost entry
    if sets_list[-1] == "":
        sets_list.pop()

    # convert single nested list to list of dictionaries
    new_sets_list = []
    for set_data in sets_list:
        new_set_data = {}
        set_item_list = set_data.split(",")
        set_item_index = 0
        for set_item in set_item_list:
            new_set_data[set_headers[set_item_index]] = set_item
            set_item_index += 1
        new_sets_list.append(new_set_data)
    return (new_sets_list)


def name_from_id(user_id):
    # return set name from user supplied ID
    #
    sets_list = import_user_set_list()

    for set_item in sets_list:
        set_id = set_item["ID"]
        if set_id == user_id:
            return(set_item["Name"])
            break


def verify_oauth():
    # form oauth token

    with open("credentials_file.txt") as credentials_file:
        [consumer_key, consumer_secret, token_value,
            token_secret] = credentials_file.read().split("\n")
    auth = OAuth1(consumer_key, consumer_secret, token_value, token_secret)

    return auth


def bricklink_prices():
    # gather current prices from bricklink API

    price_list = "Name,ID,Status,Retail Price,Current Price\n"

    sets_list = import_user_set_list()
    for set_item in sets_list:

        set_id = set_item["ID"]
        set_status = set_item["Status"]
        if set_status == "New":
            set_status = "N"
        else:
            set_status = "U"

        set_url = "https://api.bricklink.com/api/store/v1/items/set/" + \
            set_id + "-1/price?guide_type=sold&new_or_used=" + set_status

        response = requests.get(set_url, auth=verify_oauth())
        response_json = json.loads(response.text)

        set_message = name_from_id(set_id) + ": " + response_json["meta"]["message"]
        print(set_message)

        if response_json["meta"]["message"] == "OK":
            qty_avg_price = response_json["data"]["qty_avg_price"]
        else:
            qty_avg_price = "0.00"

        set_item["Current Price"] = "$" + qty_avg_price

        set_data = ",".join(set_item.values())
        price_list = price_list + set_data + "\n"

    with open("Identified Lego Sets - python_export.csv", "w") as list_file_prices:
        list_file_prices.write(price_list)


def decompose_piece_list(pieces_list):

    # split user supplied list of pieces into list of pieces
    # pieces are stored as a list of [piece id, piece color, piece quantity]

    pieces_list = pieces_list.split(" ")
    index = 0

    for piece in pieces_list:

        # 4522 4006:11 2x58247:11 2x3849
        piece_count = "1"
        piece_color = ""

        if "x" in piece:
            piece = str(piece).split("x")
            piece_count = piece.pop(0)
            piece = piece[0]

        if ":" in piece:
            piece = str(piece).split(":")
            piece_color = piece.pop(-1)
            piece = piece[0]

        piece_id = piece

        pieces_list[index] = [piece_id, piece_color, piece_count]
        index += 1

    if len(pieces_list[0]) == 1:
        pieces_list = [pieces_list]

    return (pieces_list)


def sets_piece_lists():

    # construct json file where piece lists per set are stored locally

    sets_list = import_user_set_list()

    pieces_list_by_set = {}
    for set_data in sets_list:
        set_id = set_data["ID"]
        set_url = "https://api.bricklink.com/api/store/v1/items/set/" + set_id + "-1/subsets"
        response = requests.get(set_url, auth=verify_oauth())
        json_load = json.loads(response.text)

        set_message = name_from_id(set_id) + ": " + json_load["meta"]["message"]
        print(set_message)

        pieces_list = []

        for piece in json_load["data"]:
            piece_id = piece["entries"][0]["item"]["no"]
            piece_color = str(piece["entries"][0]["color_id"])
            piece_quantity = str(piece["entries"][0]["quantity"])

            pieces_list.append([piece_id, piece_color, piece_quantity])
        pieces_list_by_set[set_id] = pieces_list

    with open("pieces_list_by_set.json", "w") as list_file:
        list_file.write(json.dumps(pieces_list_by_set, indent=4))


def filter_sets_by_piece_list(pieces_list_user):

    # compare user supplied list of pieces to sets list and report matches

    sets_list = import_user_set_list()

    with open("pieces_list_by_set.json", "r") as list_file:
        pieces_list_by_set = json.loads(list_file.read())

    for set_data in sets_list:
        set_id = set_data["ID"]
        pieces_list_json = pieces_list_by_set[set_id]

        #declare found piece quantity here so it can be used for printing results
        found_piece_quantity = "0"
        found_pieces_list = []

        for piece_user in pieces_list_user:
            piece_user_id = piece_user[0]
            piece_user_color = piece_user[1]
            piece_user_quantity = piece_user[2]
            for piece_json in pieces_list_json:
                piece_json_id = piece_json[0]
                piece_json_color = piece_json[1]
                piece_json_quantity = piece_json[2]

                # check validity of user piece vs. json list
                piece_id_valid = piece_json_id == piece_user_id
                piece_quantity_valid = piece_user_quantity <= piece_json_quantity
                if piece_user_color != "":
                    piece_color_valid = piece_user_color == piece_json_color
                else:
                    piece_color_valid = True

                if piece_id_valid and piece_color_valid and piece_quantity_valid:
                    found_pieces_list.append(piece_user)
                    if len(pieces_list_user) == 1:
                        found_piece_quantity = piece_json_quantity
                    continue

        if found_pieces_list == pieces_list_user:
            if len(pieces_list_user) > 1:
                print("Found in set: " + name_from_id(set_id))
            else:
                print(found_piece_quantity + " Found in set: " + name_from_id(set_id))


def main_loop():
    
    print("")
    print(
        "Type a list of pieces as '[quantity]x[piece id]:[color]' for a list of sets that contain those pieces")
    print("    example inputs:'1x4522:11', '4522 4006:11 2x58247:11 2x3849'")
    print(
        "Type 'piece list' to create local cache that contains pieces list for each set")
    print("Type 'set name [set id]' for the name of the provided set")
    print("Type 'bricklink prices' to write the list of bricklink prices to 'sets_current_prices.csv'")
    print("Type 'exit' or 'quit' to exit")

    while True:
        print("")
        user_request = input("Prompt: ").lower()

        if user_request == "exit" or user_request == "quit":
            break

        elif "piece list" in user_request:
            sets_piece_lists()

        elif "set name" in user_request:
            user_id = user_request.split(" ")[-1]
            print(name_from_id(user_id))

        elif "bricklink prices" in user_request:
            bricklink_prices()

        else:
            piece_list = decompose_piece_list(user_request)
            filter_sets_by_piece_list(piece_list)


if __name__ == "__main__":
    main_loop()
