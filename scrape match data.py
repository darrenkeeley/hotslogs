from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from bs4 import BeautifulSoup
import time, csv, datetime, json, re, os

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    serial = obj.isoformat()
    return serial

#Leaderboard ranks gets the account IDs of the top players on a particular server, then writes them to a csv.
def leaderboard_ranks(region=3, gamemode=4, league='master', DIR = os.getcwd() ):
    #Open page with table of top players in firefox and read it with Beautiful Soup
    driver = webdriver.Firefox(executable_path = os.getcwd() + '\geckodriver.exe')
    driver.get("https://www.hotslogs.com/Rankings?Region={}&GameMode={}&League={}".format(region, gamemode, league))
    html = driver.page_source
    soup = BeautifulSoup(html)
    
    #Find the table with player IDs
    table = soup.find('table', {'id':'ctl00_MainContent_RadGridRankings_ctl00'})
    players_and_pages = table.find('div',{'class':'rgWrap rgInfoPart'}).find_all('strong')
    players_and_pages = [int(players_and_pages[0].get_text()),int(players_and_pages[1].get_text())]
    
    #Using the table, locate the player IDs and put them in a list
    player_ranks = []
    table_rows = table.find_all('tr',{'class':['rgRow','rgAltRow']})
    for each in table_rows:
        playerID = each.find('a')['href'][25:]
        player_ranks.append(playerID)
    
    #The table may have multiple pages. If so, the remaining pages are scraped.
    if players_and_pages[1] > 1:
        for page in range(2, players_and_pages[1]+1):
            driver.find_element_by_class_name("rgPageNext").click()
            time.sleep(3)
            html = driver.page_source
            
            soup = BeautifulSoup(html)
            table = soup.find('table', {'id':'ctl00_MainContent_RadGridRankings_ctl00'})
            table_rows = table.find_all('tr',{'class':['rgRow','rgAltRow']})
            for each in table_rows:
                playerID = each.find('a')['href'][25:]
                player_ranks.append(playerID)
                
    driver.close()
    
    #Write the list of IDs to a csv
    f = open(DIR + '\korea_ranks.csv', 'w', encoding = 'UTF-8')
    writer = csv.writer(f)
    writer.writerow(player_ranks)
    f.close()
    print("Player IDs written to csv")

#NOTE: table class = 'rgDetailTable'
#id = 'ctl00_MainContent_RadGridMatchHistory_ctl00__x', and x goes from 0 to 9.
def scrape_matches(ranks = os.getcwd() + '\korea_ranks.csv', str_date = '10/1/2017 12:00:00 AM', time_limit = 45): #time_limit=10800
    ranks_reader = csv.reader(open(ranks, 'r', encoding = 'UTF-8'))
    
    #Check if match data has already been scraped by a previous operation and saved to the local disc as json.
    #If so, read it and add to it. If not, the script will create a new json file from scratch.   
    try:
        data_file = open(os.getcwd() + '\korea_matches.json', 'r', encoding = 'UTF-8')
        data = json.load(data_file)
        with open(os.getcwd() + 'korea_matches_backup.json', 'w', encoding = 'UTF-8') as data_file_backup:
            json.dump(data, data_file_backup, sort_keys=True, indent=4)
            data_file_backup.close()
        data_file.close()        
        
    except FileNotFoundError:
        data = {}
    
    #Use the list of player IDs to look up their profile pages
    start_time = time.time()
    for row in ranks_reader:
        for playerID in row:
            run_time = time.time() - start_time
            if run_time > time_limit:
                return 'Time limit reached.'
            
            print('Looking up {}. Run time is {} seconds.'.format(playerID, run_time))
            try:
                driver = webdriver.Firefox(executable_path = os.getcwd() + '\geckodriver.exe')
                driver.get('https://www.hotslogs.com/Player/MatchHistory?PlayerID={}'.format(playerID))
                html = driver.page_source
                soup = BeautifulSoup(html)
                match_rows = soup.find_all('tr',{'class':['odd rgRow','even rgAltRow']})
                
            except AttributeError:
                return 'No match history table found. Probably pageload error.'
            
            #Counters and list of all the games that have been already looked at.
            row_counter = -1
            n_matches = 0
            match_id_list = [['match_id','map']]

            #For each row (match), check if it's ID is already in the data. If not, click expand.
            #Match IDs are simply the dates of the match.
            for each in match_rows:
                row_counter += 1
                table_data = each.find_all('td')
                match_id = datetime.datetime.strptime(table_data[10].text, '%m/%d/%Y %I:%M:%S %p')
                
                #Check if this match is within the desired timeframe.
                if match_id > datetime.datetime.strptime(str_date, '%m/%d/%Y %I:%M:%S %p'):
                    n_matches += 1
                    match_id = json_serial(match_id)
                    #Adds [match_id, map] to list of ids. This list keeps track of which matches we're looking at.
                    match_id_list.append([match_id, table_data[2].get_text()])
                    
                    #Click expand buttons. Because of load times, not all of them will be successfully clicked. Then collect all data in another sweep.
                    if match_id not in data:
                        try:                        
                            print('click {}'.format(row_counter))
                            driver.find_element_by_id('__{}'.format(row_counter)).find_element_by_class_name('details-control').click()
                            time.sleep(1.5) #Just to be sure it opens
                        except StaleElementReferenceException or NoSuchElementException:
                            pass
            
            #Store html in BeautifulSoup again because webpage has been updated by clicking expand buttons.
            #Try to find each Details Table, because not all are present.
            #If the last element doesn't load, close the driver and continue to the next player.
            try: 
                html = driver.page_source
                soup = BeautifulSoup(html)
                detail_table = soup.find_all('tr',{'id':re.compile('MatchSummary_RadGridMatchDetails_ctl00__.*')})
                while len(detail_table) > 0:
                    #pop the first 10 rows. Only issue is sometimes there is only on 'a' tag instead of two.
                    #The player name 'a' tag is sometimes missing, leaving on the hero 'a' tag.
                    try:
                        ten_rows_one_match = [detail_table.pop(0),detail_table.pop(0),detail_table.pop(0),detail_table.pop(0),detail_table.pop(0),detail_table.pop(0),detail_table.pop(0),detail_table.pop(0),detail_table.pop(0),detail_table.pop(0)]
                        def get_hero(r):
                            if ten_rows_one_match[r].find_all('a')[1].get_text() == '':
                                return ten_rows_one_match[r].find_all('a')[0].get_text()
                            else:
                                return ten_rows_one_match[r].find_all('a')[1].get_text()
                            
                        Win_element = [get_hero(0),
                                       get_hero(1),
                                       get_hero(2),
                                       get_hero(3),
                                       get_hero(4)
                                       ]
                        Lose_element =[get_hero(5),
                                       get_hero(6),
                                       get_hero(7),
                                       get_hero(8),
                                       get_hero(9)
                                       ]
                        #Get the match ID
                        tuple_from_match_ud_list = match_id_list.pop(0)
                        match_id = tuple_from_match_ud_list[0]
                        Map = tuple_from_match_ud_list[1]
                        complete_row = {'Map':Map,
                                        'Win':Win_element,
                                        'Lose':Lose_element
                                        }
                        
                        data[match_id] = complete_row
                        
                        #Whenever a row is completed, write it to the json.
                        with open(os.getcwd() + '\korea_matches.json', 'w', encoding = 'UTF-8') as data_file:
                            json.dump(data, data_file, sort_keys=True, indent=4)
                            data_file.close()
                            print('Wrote match to json')
                    
                    #Continue match lookup loop if page doesn't load.
                    except AttributeError:
                        pass 
            #Continue player lookup loop is page doesn't load.
            except AttributeError:
                    pass 
            
            driver.close()
    
    return 'End of rank list reached.' 
    


