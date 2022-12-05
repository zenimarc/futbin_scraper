import sys
import time

from bs4 import BeautifulSoup as beauty
import cloudscraper
import json
import requests
from tinydb import TinyDB, Query

FUTBIN_API = "https://www.futbin.org/futbin/api/23/"
FUTBIN_PLAYERS_LIST_PAGE = "https://www.futbin.com/players"
REQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
}

def get_params(player_id: int):
    return f"fetchPlayerInformationAndroid?ID={player_id}&platform=PC"

print("1. aggiorna lista players ID\n2. scarica dati completi")
sel = int(input())

if sel == 1:
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

if sel == 2:
    db = TinyDB("players_db.json")
    file = open("data.txt", "r")
    player_id_list = json.load(file)["players"]
    progress = {
        "reached_idx": 0,
        "errors": []
    }
    try:
        progress_file = open("progress.txt", "r")
        progress = json.load(progress_file)
    except:
        pass

    def log_error(p_id):
        print("Error get data for player: "+p_id)

    def log_progress_to_file(prg):
        with open("progress.txt", "w") as f:
            json.dump(progress, f)

    Player = Query()
    for idx, player_id in enumerate(player_id_list):
        try:
            progress["reached_idx"] = idx
            # check if id already present
            res = db.search(Player.ID == int(player_id))
            if len(res) != 0:
                # already present
                continue
            resp = requests.get(FUTBIN_API + get_params(player_id), headers=REQ_HEADERS)

            if resp.status_code != 200:
                progress["errors"].append(player_id)
                log_error(player_id)
                log_progress_to_file(progress)
                time.sleep(3)
                continue
            api_resp = resp.json()
            if api_resp["errorcode"] != "200":
                progress["errors"].append(player_id)
                log_error(player_id)
                log_progress_to_file(progress)
                time.sleep(3)
                continue

            # all good here
            players_data = api_resp["data"]
            for player_data in players_data:
                db.insert(player_data)
                print(f"{player_id}: {player_data['Player_Fullname']} {player_data['Revision']} aggiunto correttamente")
            log_progress_to_file(progress)


            time.sleep(3)
        except:
            print("generic error")
            progress["errors"].append(player_id)
            log_progress_to_file(progress)




