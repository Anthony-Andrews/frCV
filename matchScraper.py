# uses TheBlueAlliance website API to get 2 random match video URL's from each competition in the 2023 season. see https://www.thebluealliance.com/apidocs

# *with help from ChatGPT (am sleep depreived and doing this instead of hw)

# NOTE this code is extremely slow and could easily be made faster, but a run once/ automate kind of deal it dosent matter...

import requests, random, time, os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

season = 2023

matchPerComp = 2

driver = webdriver.Firefox()







def ssVid(url, match):
        # Open the YouTube video in full-screen mode.
        timeStamp = random.randrange(5,160)
        timeURL = url + '&t=' + str(timeStamp)

        wait = WebDriverWait(driver, 10)
        driver.get(timeURL)
        try:
            ActionChains(driver).move_to_element(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.ytp-chrome-controls")))).perform()

            time.sleep(1.5)

            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "button.ytp-fullscreen-button.ytp-button"))).click()

            time.sleep(2)

            # Take a screenshot of the full-screen video.
            ytTitle = driver.title.split(' ')
            if str(season) in ytTitle:

                driver.save_screenshot(dir+str(match)+'.png')
            else: print('Ad, skipping...')
            
        except: 
            print('Invalid Video '+match)
        






def getURL():
    competitions_url = f"https://www.thebluealliance.com/api/v3/events/{season}/simple"
    headers = {"X-TBA-Auth-Key": apiKey}
    response = requests.get(competitions_url, headers=headers)

    index = 1  # number each entry

    if response.status_code == 200:
        competitions = response.json()

        # Iterate through each competition
        for competition in competitions:
            eventKey = competition["key"]
                
            # Get a list of matches for the current competition
            matches_url = f"https://www.thebluealliance.com/api/v3/event/{eventKey}/matches/simple"
            response = requests.get(matches_url, headers=headers)
                
            if response.status_code == 200:
                matchData = response.json()
                    
                # Shuffle the list of matches to make them random
                random.shuffle(matchData)
                    
                matchCount = 0  # Track the number of matches for this competition
                selected_matches = set()  # Track selected match keys
                    
                # Iterate through each match
                for match in matchData:
                    matchKey = match["key"]
                        
                    # Check if we've reached the desired number of matches for this competition
                    if matchCount >= matchPerComp:
                        break
                        
                    # Check if the match has not been selected before
                    if matchKey not in selected_matches:
                        selected_matches.add(matchKey)
                            
                        # Get the match details to check for a YouTube video
                        matchURL = f"https://www.thebluealliance.com/api/v3/match/{matchKey}"
                        response = requests.get(matchURL, headers=headers)

                        if response.status_code == 200:
                            matchDetails = response.json()

                            # Check if there are videos for the match
                            if "videos" in matchDetails:
                                videos = matchDetails["videos"]

                                # Iterate through videos to find YouTube links
                                for video in videos:
                                    if video["type"] == "youtube":
                                        ytKey = video["key"]
                                        if len(ytKey) > 12:
                                            sanYT = ytKey.split('?')[0]
                                            ytURL = f"https://www.youtube.com/watch?v={sanYT}"
                                        else: ytURL = f"https://www.youtube.com/watch?v={ytKey}"

                                        print(f"{index:<6} Match: {matchKey:<18} Video: {ytURL}")

                                        ssVid(ytURL, matchKey)

                                        index += 1
                                        matchCount += 1

                        else:
                            print(f"Failed to retrieve videos for match {matchKey}. Status code: {response.status_code}")

            else:
                print(f"Failed to retrieve matches for {eventKey}. Status code: {response.status_code}")
    else:
        print(f"Failed to retrieve competitions. Status code: {response.status_code}")








if __name__ == "__main__":
    startTime = time.time()

    dir = os.path.dirname(os.path.abspath(__file__))+'\\images\\'
    print(dir)
    if not os.path.exists(dir):
    # Create the folder if it doesn't exist
        os.makedirs(dir)

    load_dotenv()
    apiKey = os.getenv('apiKey')

    getURL()

    endTime = time.time()
    elapsedTime2 = round(endTime - startTime, 2) 
    print(f"Done collecting images! {elapsedTime2} seconds elapsed.")