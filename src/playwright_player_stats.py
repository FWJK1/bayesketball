from playwright.sync_api import sync_playwright
import json

url = "https://stats.nba.com/stats/leaguedashplayerstats?College=&Conference=&Country=&DateFrom=&DateTo=&Division=&DraftPick=&DraftYear=&GameScope=&GameSegment=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&MeasureType=Base&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=PerGame&Period=0&PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&Season=2025-26&SeasonSegment=&SeasonType=Regular%20Season&ShotClockRange=&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight="

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # NBA blocks unknown User-Agents, so set one
    page.set_extra_http_headers({"User-Agent": "Mozilla/5.0"})

    page.goto(url)

    # Wait for the response and grab it
    response = page.wait_for_response(lambda r: "leaguedashplayerstats" in r.url)
    data = response.json()

    print(json.dumps(data, indent=2))

    browser.close()
