import sys
import time

from bs4 import BeautifulSoup as beauty
import cloudscraper
import json

FUTBIN_API = "https://www.futbin.org/futbin/api/23/"
FUTBIN_PLAYERS_LIST_PAGE = "https://www.futbin.com/players"

def get_params(player_id: int):
    return f"fetchPlayerInformationAndroid?ID={player_id}&platform=PC"


all_players_id = []

scraper = cloudscraper.create_scraper()
resp = scraper.get(FUTBIN_PLAYERS_LIST_PAGE)
soup = beauty(resp.text, 'html.parser')

try:
    total_pages = int(soup.select_one("ul.pagination.pg-blue.justify-content-end > li:nth-last-child(2) > a").text)
except:
    print("impossible to get total pages")
    sys.exit(999)


for page_num in range(1, total_pages+1):

    resp = scraper.get(FUTBIN_PLAYERS_LIST_PAGE+"?page="+str(page_num))
    soup = beauty(resp.text, 'html.parser')

    row_players = soup.select("#repTb > tbody > tr[data-url]")
    if len(row_players) == 0:
        print("trovato niente, forse bannato, riprovo")
        time.sleep(5)
        row_players = soup.select("#repTb > tbody > tr[data-url]")
        if len(row_players) == 0:
            print(f"niente ancora, vabbè\npagina {page_num} saltata")
            continue
    for player in row_players:
        try:
            player_url = player.attrs["data-url"]
            player_id = player_url.split("/")[-2]
            all_players_id.append(player_id)
        except Exception as e:
            print(e)

    dataObj = {
        "players": all_players_id,
        "total_pages": total_pages,
        "page_reached": page_num
    }

    with open("data.txt", "w") as file:
        json.dump(dataObj, file)

    print(f"page {page_num} fatta!!")

    time.sleep(2)



print("finished")

