import time
import json
import requests
from requests_oauthlib import OAuth1

with open("Identified Lego Sets - List.csv", "r") as list_file:
    list_text = list_file.read()

# convert .csv to doubly nested list
sets_list = list_text.split("\n")
# remove headers
sets_list.pop(0)
# remove ghost entry at bottom
sets_list.pop()

index = 0
for set_data in sets_list:
    set_data = set_data.split(",")
    sets_list[index] = set_data
    index += 1

# form oauth token
with open("credentials_file.txt") as credentials_file:
    [consumer_key, consumer_secret, token_value,
        token_secret] = credentials_file.read().split("\n")


auth = OAuth1(consumer_key, consumer_secret, token_value, token_secret)


def decompose_piece_list(pieces_list):
    # decompose user entry into list of pieces
    pieces_list = pieces_list.split(" ")
    index = 0

    for piece in pieces_list:

        # 4522 4006:11 2x58247:11 2x3849
        piece_count = ""
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
    return (pieces_list)


pieces_list_by_set = {}


def sets_piece_lists():
    # construct json file where piece lists per set are stored locally
    index = 0
    for set_data in sets_list:
        set_id = set_data[1]
        set_url = "https://api.bricklink.com/api/store/v1/items/set/" + set_id + "-1/subsets"
        response = requests.get(set_url, auth=auth)
        json_load = json.loads(response.text)

        set_message = set_id + ": " + json_load["meta"]["message"]
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
    with open("pieces_list_by_set.json", "r") as list_file:
        pieces_list_by_set = json.loads(list_file.read())
    if len(pieces_list_user[0]) == 1:
        pieces_list_user = [pieces_list_user]

    for set_data in sets_list:
        set_validity = 0
        set_id = set_data[1]
        pieces_list_json = pieces_list_by_set[set_id]

        for piece_user in pieces_list_user:
            piece_user_id = piece_user[0]
            piece_user_color = piece_user[1]
            piece_user_quantity = piece_user[2]

            for piece_json in pieces_list_json:
                piece_json_id = piece_json[0]
                piece_json_color = piece_json[1]
                piece_json_quantity = piece_json[2]

                if piece_json_id != piece_user_id:
                    set_validity = 0
                    print(piece_user_id + " NOT found in " + set_id)
                    break
                else:
                    print(piece_user_id + " found in " + set_id)

                if piece_json_color != piece_user_color:
                    set_validity = 0
                    print(piece_user_id + " WRONG color " + set_id)
                    break
                else:
                    print(piece_user_id + " with color " +
                          piece_user_color + " found in " + set_id)

                if piece_json_quantity < piece_user_quantity:
                    set_validity = 0
                    print(piece_user_id + " TOO many " + set_id)
                    break
                else:
                    print(piece_user_id + " with color " + piece_user_color +
                          " with <= " + piece_user_quantity + " found in " + set_id)

                set_validity = 1
                # print(set_validity)
                continue


# if piece_user in pieces_list_json:
# set_validity = 1
# else:
# set_validity = 0
# break

        if set_validity == 1:
            print(set_id)


while True:
    user_request = input("Prompt: ").lower()

    if user_request == "exit":
        break

    if user_request == "piece list":
        sets_piece_lists()

    else:
        piece_list = decompose_piece_list(user_request)
        filter_sets_by_piece_list(piece_list)
