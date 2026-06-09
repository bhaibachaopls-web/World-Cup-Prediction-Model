import time
import random
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import json

# Load the automatically scraped dictionary
with open('teams2.json', 'r') as f:
    TEAMS = json.load(f)

# TEAMS = {'elfenbeinkuste': '3591',
#  'neuseeland': '9171',
#  'gabun': '5704',
#  'uganda': '13497',
#  'benin': '3955',
#  'palastina': '17758',
#  'belarus': '3450',
#  'tadschikistan': '13975',
#  'libanon': '3586',
#  'nicaragua': '15351',
#  'republik-kongo': '3702',
#  'turkmenistan': '14248',
#  'athiopien': '13941',
#  'botsuana': '15229',
#  'jemen': '15922',
#  'fidschi': '13955',
#  'vanuatu': '15238',
#  'antigua-und-barbuda': '16028',
#  'bermuda': '15735',
#  'st-lucia': '17761',
#  'afghanistan': '3576',
#  'st-vincent-und-die-grenadinen': '17762',
#  'chinesisch-taipeh-taiwan-': '15363',
#  'tschad': '13978',
#  'macau': '16432',
#  'osttimor': '17757'}


START_YEAR = 2018
END_YEAR = 2026
OUTPUT_FILE = "test.csv"

def parse_squad_details_table(html_content, team_name, season, target_position="Total:"):
    """
    Parses the table and only returns rows matching the target_position.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    target_table = None
    
    for t in soup.find_all('table'):
        headers = [th.text.strip().lower() for th in t.find_all(['th', 'td'])]
        if 'position' in headers and 'ø-age' in headers:
            target_table = t
            break
            
    if not target_table:
        return []

    data = []
    
    # 1. Main body rows (Goalkeeper, Defender, Midfield, Attack)
    tbody = target_table.find('tbody')
    if tbody:
        for row in tbody.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 4:
                position_name = cols[0].text.strip()
                
                # --- THE FILTER ---
                # We convert both to lowercase so "goalkeeper" matches "Goalkeeper"
                if target_position.lower() in position_name.lower():
                    data.append({
                        "Team": team_name,
                        "Season": season,
                        "Position": position_name,
                        "ø-Age": cols[1].text.strip(),
                        "Market value": cols[2].text.strip(),
                        "ø-Market value": cols[3].text.strip()
                    })
                
    # 2. Extract the Total row (tfoot)
    tfoot = target_table.find('tfoot')
    if tfoot:
        for row in tfoot.find_all('tr'):
            cols = row.find_all(['td', 'th']) 
            if len(cols) >= 4:
                position_name = cols[0].text.strip()
                
                # --- THE FILTER ---
                if target_position.lower() in position_name.lower():
                    data.append({
                        "Team": team_name,
                        "Season": season,
                        "Position": position_name, 
                        "ø-Age": cols[1].text.strip(),
                        "Market value": cols[2].text.strip(),
                        "ø-Market value": cols[3].text.strip()
                    })
                
    return data

def scrape_all_teams():
    all_data = []
    
    with sync_playwright() as p:
        # headless=False is highly recommended for Transfermarkt to pass Cloudflare checks
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        for team_name, team_id in TEAMS.items():
            for year in range(START_YEAR, END_YEAR + 1):
                url = f"https://www.transfermarkt.com/{team_name}/kader/verein/{team_id}/plus/0/galerie/0?saison_id={year}"
                print(f"Scraping: {team_name.upper()} ({year})")
                
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    
                    # MANDATORY DELAY
                    time.sleep(random.uniform(4.0, 8.0)) 

                    # --- ULTRA-SPECIFIC PAUSE LOGIC ---
                    # Transfermarkt data is ALWAYS in a table with the class 'items'.
                    # If this specific table is missing, we are definitely blocked.
                    if page.locator("table.items").count() == 0:
                        print(f"\n🛑 PAUSED: CAPTCHA DETECTED ON {team_name.upper()} ({year}) 🛑")
                        print("1. Go to your open Brave browser window.")
                        print("2. Solve the image puzzle.")
                        print("3. Wait until the actual Transfermarkt squad data appears.")
                        input("4. Press ENTER right here in the terminal to resume... ")
                        
                        time.sleep(2) 
                    # --------------------------------
                    
                    # Basic accept cookies handling
                    try:
                        if page.locator("iframe[title='SP Consent Message']").is_visible():
                            page.frame_locator("iframe[title='SP Consent Message']").locator("button[title='Accept & continue']").click()
                            time.sleep(2)
                    except:
                        pass

                    html = page.content()
                    table_data = parse_squad_details_table(html, team_name, year, target_position="Total:")
                    
                    if table_data:
                        all_data.extend(table_data)
                        print(f"  -> Successfully grabbed table details.")
                        pd.DataFrame(all_data).to_csv(OUTPUT_FILE, index=False)
                    else:
                        print("  -> Could not find the 'SQUAD DETAILS BY POSITION' table.")
                        
                except Exception as e:
                    print(f"  -> Error: {e}")
                    time.sleep(10) # Extended sleep on error

        browser.close()
        print(f"Scraping complete. Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape_all_teams()
                    
