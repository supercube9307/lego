import requests
import time

# This is a comment

list_file = open("Identified Lego Sets - List.csv", "r")
list_file_prices = open("Identified Lego Sets Prices.csv", "w")

list_text = list_file.read()
sets_list = list_text.split("\n")
sets_list.pop(0)
sets_list.pop()
price_list = ""

index = 0
sleep_time = 10

for set_data in sets_list:

    # if index == 20:
    # break
    # index += 1

    set_data_list = set_data.split(",")
    set_id = set_data_list[1]

    if set_data_list[-2].find("$") == -1:
        set_url = "https://brickset.com/sets/" + set_id + "-1/"
        set_link = requests.get(set_url)

        if str(set_link).find("429") != -1:
            print("Status 429: Set ID " + set_id)
            time.sleep(sleep_time)
            continue
        else:
            set_text = str(set_link.text)
            print("Status 200: Set ID " + set_id)

        RRP_index = set_text.find("RRP")
        set_text = set_text[RRP_index:RRP_index+100]
# print(set_text)

        dollar_index = set_text.find("$")
        set_text = set_text[dollar_index:]
# print(dollar_index)

        decimal_index = set_text.find(".")
        set_price = set_text[:decimal_index+3]
# print(decimal_index)
        print("Listed Price: " + set_price)

        time.sleep(sleep_time)
    else:
        print("Price Found: Set ID " + set_id)
        set_price = set_data_list[-2]

    set_data_list[-2] = set_price
    set_data_list = set_data_list[:-1]
    set_data = ",".join(set_data_list)
# print(set_data_list)

    price_list = price_list + set_data + "\n"

list_file_prices.write(price_list)

list_file.close()
list_file_prices.close()
