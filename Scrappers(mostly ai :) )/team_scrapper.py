import time
import random
import json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def scrape_team_ids():
    teams_dict = {}
    
    # Using your Brave browser setup
    BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    MAC_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, executable_path=BRAVE_PATH) 
        context = browser.new_context(user_agent=MAC_USER_AGENT, viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # There are usually around 210 teams, displaying 25 per page (so 9 pages total)
        for current_page in range(0, 9):
            url = f"https://www.transfermarkt.com/statistik/weltrangliste?ajax=yw1&page={current_page}"
            print(f"Scanning World Ranking Page {current_page}...")
            
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
                    
                    time.sleep(10)
                # Cookie popup handler
                try:
                    if page.locator("iframe[title='SP Consent Message']").is_visible():
                        page.frame_locator("iframe[title='SP Consent Message']").locator("button[title='Accept & continue']").click()
                        time.sleep(10)
                except:
                    pass 

                # Parse the page
                soup = BeautifulSoup(page.content(), 'html.parser')
                
                # Team names are kept inside table cells with the class 'hauptlink'
                links = soup.select('td.hauptlink a')
                
                if not links:
                    print("  -> No links found. Might be the end of the list or a page load error.")
                    break

                for link in links:
                    href = link.get('href')
                    # Example href: /brazil/startseite/verein/3439
                    
                    if href and 'verein' in href:
                        parts = href.split('/')
                        
                        # The URL structure usually puts the name at index 1
                        team_name = parts[1] 
                        
                        # Safely find the ID which comes right after 'verein'
                        verein_idx = parts.index('verein')
                        team_id = parts[verein_idx + 1]
                        
                        teams_dict[team_name] = team_id
                
                print(f"  -> Extracted {len(teams_dict)} teams so far.")

            except Exception as e:
                print(f"  -> Error on page {current_page}: {e}")
                time.sleep(10)

        browser.close()
        
        # Save the dictionary to a JSON file
        with open('teams2.json', 'w') as f:
            json.dump(teams_dict, f, indent=4)
            
        print(f"\nSuccess! Saved {len(teams_dict)} teams to teams.json")

if __name__ == "__main__":
    scrape_team_ids()
