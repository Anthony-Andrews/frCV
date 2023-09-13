# uses TheBlueAlliance website API to get 2 random match video URL's from each competition in the 2023 season. see https://www.thebluealliance.com/apidocs

# *with help from ChatGPT

# NOTE this code is extremely slow and could easily be made faster, but for my purposes its fine and I'm not skilled enough to dare...

import requests, random, time, os, webbrowser, keyboard
from dotenv import load_dotenv

load_dotenv()
apiKey = os.getenv('apiKey')

# TheBlueAlliance API base URL
apiURL = "https://www.thebluealliance.com/api/v3"

season = 2023

matchPerComp = 2

# Get a list of competitions for the specified year
competitions_url = f"{apiURL}/events/{season}/simple"
headers = {"X-TBA-Auth-Key": apiKey}
response = requests.get(competitions_url, headers=headers)

index = 1  # number each entry
startTime = time.time()  # start the timer




def vidSS(url):
    timeStamp = random.randrange(5,160)
    timeURL = url + '&t=' + str(timeStamp)
    webbrowser.open_new(timeURL)
    time.sleep(5)
    keyboard.send('space')
    keyboard.send('f')
    time.sleep(2)
    keyboard.send()




if response.status_code == 200:
    competitions = response.json()

    # Iterate through each competition
    for competition in competitions:
        eventKey = competition["key"]
            
        # Get a list of matches for the current competition
        matches_url = f"{apiURL}/event/{eventKey}/matches/simple"
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
                    matchURL = f"{apiURL}/match/{matchKey}"
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
                                    vidSS(ytURL)
                                    index += 1
                                        
                                    matchCount += 1

                    else:
                        print(f"Failed to retrieve videos for match {matchKey}. Status code: {response.status_code}")

        else:
            print(f"Failed to retrieve matches for {eventKey}. Status code: {response.status_code}")

    endTime = time.time()
    elapsedTime = round(endTime - startTime, 2)

    print(f"Done in {elapsedTime} seconds.")

else:
    print(f"Failed to retrieve competitions. Status code: {response.status_code}")