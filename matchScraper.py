# A Selenium/Firefox based web scraper for FRC matches. Gets screenshots of a random point during each match for training a model. https://selenium-python.readthedocs.io/index.html
# Uses TheBlueAlliance API. https://www.thebluealliance.com/apidocs

# *with help from ChatGPT (am sleep depreived and doing this instead of hw)

import requests, random, time, os, cv2 # dependency bullcrap
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from cv2 import dnn_superres


season = 2023 # specify which FRC season to scrape

matchPerComp = 3 # specify how many matches per competition to retreive

headless = True # set to True to run in background silently without browser window (this is currently recommended as otherwise images will be the resolution of your main monitor)

muted = True # mute audio

upscale2x = True # super resoltion 4x upscaling of the images using ESPCN_x4 model

dir = os.path.dirname(os.path.abspath(__file__)) # get path of script.

options = webdriver.FirefoxOptions() # specify options for the automated Firefox windows


# if running in headless mode, mute browser and set to headless mode
if headless == True:
    print('Starting FRC match scraper... (headless mode)') # print status
    options.add_argument('--headless')
    options.add_argument('--start-maximized')
    options.set_preference('media.volume_scale', '0.0')
    options.add_argument('--width=1920')
    options.add_argument('--height=1080')
    os.environ['MOZ_HEADLESS_WIDTH'] = '1920'
    os.environ['MOZ_HEADLESS_HEIGHT'] = '1080'

elif muted == True:
    print('Starting FRC match scraper... (muted)')
    options.set_preference('media.volume_scale', '0.0')

else: print('Starting FRC match scraper...')

driver = webdriver.Firefox(options = options) # specify Firefox geckodriver for scraping.

driver.install_addon(f'{dir}\\geckodriver\\ublock_origin-1.52.0.xpi') # install uBlock Origin extension in Firefox to block ads. https://addons.mozilla.org/en-US/firefox/addon/ublock-origin/






def superRes(imgLocation):
    # Create an SR object
    sr = dnn_superres.DnnSuperResImpl_create()

    # Read image
    image = cv2.imread(imgLocation)

     # Read the desired model
    path = f'{dir}\\superRes\\ESPCN_x2.pb'
    sr.readModel(path)

    #sr.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA) # gpu stuff (not needed and not fully supported)
    #sr.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

    # Set the desired model and scale to get correct pre- and post-processing
    sr.setModel("espcn", 2) # x2 scale

    # Upscale the image
    result = sr.upsample(image)

    # Save the image, overriding the original.
    cv2.imwrite(imgLocation, result)





# function that takes in Youtube URL of a match, goes to a random point between auton and endgame, and takes a screenshot
def ssVid(url, match):

        timeStamp = random.randrange(5,155) # use yt's timestamp url postfix from 5-155 seconds before even loading the page
        timeURL = url + '&t=' + str(timeStamp)

        wait = WebDriverWait(driver, 10) # specify the timeout time for waiting for elements to load *note this may need to change depending on the computer and if you are getting inconsitant results
        driver.get(timeURL) # load the video page

        try:

            assert str(season) in driver.title # typically the year will be the the title of the match, this is a small precaution to avoid ss of non frc vids in case something happens

            ActionChains(driver).move_to_element(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.ytp-chrome-controls')))).perform() # wait until the toolbar is loaded

            time.sleep(2) # *note this may need to change depending on the computer and if you are getting inconsitant results

            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'button.ytp-fullscreen-button.ytp-button'))).click() # click the fullscreen button

            time.sleep(0.5) # *note this may need to change depending on the computer and if you are getting inconsitant results

            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ytp-settings-button'))) # wait until the settings button is visible

            driver.find_element(By.CSS_SELECTOR, '.ytp-settings-button').click() # click the settigns button

            settings_menu = driver.find_element(By.CSS_SELECTOR, '.ytp-popup.ytp-settings-menu') # find the "quality" sub-menu

            settings_menu.find_element(By.XPATH, '//div[contains(text(),"Quality")]').click() # click on the "quality" sub-menu

            time.sleep(1) # *note this may need to change depending on the computer and if you are getting inconsitant results

            # try changing the video to the highest resolution, if resolution is below 480p it will skip the video:
            qualityOptions = ["2160p", "2160p60p", "2160p50p", "1440p", "1440p60p", "1440p50p", "1080p", "1080p60p", "1080p50p", "720p", "720p60p", "720p50p", "480p"] # tries setting the video to the highest resoltion, if below 480p skip.
            try:
                for option in qualityOptions:
                    try:
                        driver.find_element(By.XPATH, f'//span[text()="{option}"]').click()
                        break  # Exit the loop if a quality option is found and clicked
                    except:
                        continue  # Continue to the next quality option if the current one is not found
            except:
                print('Resolution too low, skipping...')
                return None
            

            time.sleep(5) # wait until video overlay disapears *NOTE this may need to change depending on the computer and if you are getting inconsitant results

            driver.save_screenshot(dir+'\\images\\'+str(match)+'.png') # save a screenshot of the current page to dir/images/match.png
            
            print(f"Image saved to {dir}\images\{str(match)}.png") # print status
            global successIndex
            successIndex += 1 # iterate the counter of succesful images saved

            if upscale2x == True:
                superRes(f"{dir}\images\{str(match)}.png")

            assert 'Invalid video, skipping... ' not in driver.page_source # print if video is somehow invalid
            
        except Exception as error: 
            print(f'Playback error: {error}') # general error (ex. private)
        





# function to retrive match urls
def getURL():
    competitionsURL = f"https://www.thebluealliance.com/api/v3/events/{season}/simple" # url of TBA API
    headers = {"X-TBA-Auth-Key": apiKey}
    response = requests.get(competitionsURL, headers=headers) # stuff idk i didnt write this part

    if response.status_code == 200: # 200 means good
        competitions = response.json()

        # Iterate through each competition
        for competition in competitions:
            eventKey = competition["key"]
                
            # Get a list of matches for the current competition
            matchURL = f"https://www.thebluealliance.com/api/v3/event/{eventKey}/matches/simple"
            response = requests.get(matchURL, headers=headers)
                
            if response.status_code == 200:
                matchData = response.json()
                    
                # Shuffle the list of matches to make them random
                random.shuffle(matchData)
                    
                matchCount = 0  # Track the number of matches for this competition
                matches = set()  # Track selected match keys
                    
                # Iterate through each match
                for match in matchData:
                    matchKey = match["key"]
                        
                    # Check if we've reached the desired number of matches for this competition
                    if matchCount >= matchPerComp:
                        break
                        
                    # Check if the match has not been selected before
                    if matchKey not in matches:
                        matches.add(matchKey)
                            
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

                                        if len(ytKey) > 12: # if the url already has a timestamp, sanitize it
                                            sanYT = ytKey.split('?')[0]
                                            ytURL = f"https://www.youtube.com/watch?v={sanYT}"
                                        else: ytURL = f"https://www.youtube.com/watch?v={ytKey}" # dear god this code is atrocious,  10 nested if/ for statements

                                        print(f"Match: {matchKey} Video: {ytURL}")

                                        ssVid(ytURL, matchKey) # call the first function with the arugments

                                        matchCount += 1 # iterate the match counter

                        else:
                            print(f"Failed to retrieve videos for match {matchKey}. Status code: {response.status_code}") # error stuff

            else:
                print(f"Failed to retrieve matches for {eventKey}. Status code: {response.status_code} Did you enter in an API key?") # error stuff
    else:
        print(f"Failed to retrieve competitions. Status code: {response.status_code} Did you enter in an API key?") # error stuff






def preLoad():
    try:
        wait = WebDriverWait(driver, 15)
        driver.get('https://youtu.be/NYMEL3RhIls?si=LLhvWRl4kL0PGbN4')
        time.sleep(4)
        driver.switch_to.window(driver.window_handles[0])
        ActionChains(driver).move_to_element(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.ytp-chrome-controls')))).perform()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'button.ytp-fullscreen-button.ytp-button'))).click()
        time.sleep(2)
    except:
            print('Error... is geckodriver insalled correctly?')
            exit()






if __name__ == "__main__":
    startTime = time.time()

    if not os.path.exists(dir+'\\images\\'):
    # Create the folder if it doesn't exist
        os.makedirs(dir+'\\images\\')

    load_dotenv() # load API key
    apiKey = os.getenv('apiKey') # load API key pt.2

    preLoad() # loads a sample video to avoid yt pop ups or inital slowdowns (this is a bad way of solving this problem)

    successIndex = 0  # number each image

    getURL() # call the api function
    driver.quit() # close the browser once script is done

    endTime = time.time() # calculate elapsed time
    elapsedTime = round(endTime - startTime, 2) 

    print(f"Done! Scraped {successIndex} images in {elapsedTime} seconds.") # print elapsed time and number of succesfuly scraped videos