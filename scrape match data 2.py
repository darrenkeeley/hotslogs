from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from bs4 import BeautifulSoup
import time, csv, datetime, json, re

#1) Open leaderboard in Firefox.
#2) Save the HTML for Soup scraping.
#3) Soup scrape number of pages and table data.
#4) Click next, save table data, iterate for pages - 1.
#
#Elements can have multiple classes, separated by spaces.
#The Next Page button has two classes, but I chose the unique one rgPageNext.

def leaderboard_ranks(region=3, gamemode=4, league='master', DIR = r'C:\DK Docs\projects\hotslogs\\', save_page=False):
    driver = webdriver.Firefox(executable_path = 'C:\DK Docs\projects\geckodriver.exe')
    driver.get("https://www.hotslogs.com/Rankings?Region={}&GameMode={}&League={}".format(region, gamemode, league))
    
    html = driver.page_source
    if save_page==True:
        f = open('{}leaderboard_{}{}{}{}.html'.format(DIR, region, gamemode, league, 1), 'w', encoding = 'UTF-8')
        f.write(html)
        f.close()
    
    soup = BeautifulSoup(html)
    table = soup.find('table', {'id':'ctl00_MainContent_RadGridRankings_ctl00'})
    players_and_pages = table.find('div',{'class':'rgWrap rgInfoPart'}).find_all('strong')
    players_and_pages = [int(players_and_pages[0].get_text()),int(players_and_pages[1].get_text())]
    
    player_ranks = []
    table_rows = table.find_all('tr',{'class':['rgRow','rgAltRow']})
    for each in table_rows:
        playerID = each.find('a')['href'][25:]
        player_ranks.append(playerID)

    if players_and_pages[1] > 1:
        for page in range(2, players_and_pages[1]+1):
            driver.find_element_by_class_name("rgPageNext").click()
            time.sleep(3)
            html = driver.page_source
            if save_page==True:
                f = open('{}leaderboard_{}{}{}{}.html'.format(DIR, region, gamemode, league, page), 'w', encoding = 'UTF-8')
                f.write(html)
                f.close()
            
            soup = BeautifulSoup(html)
            table = soup.find('table', {'id':'ctl00_MainContent_RadGridRankings_ctl00'})
            table_rows = table.find_all('tr',{'class':['rgRow','rgAltRow']})
            for each in table_rows:
                playerID = each.find('a')['href'][25:]
                player_ranks.append(playerID)
    driver.close()

    return player_ranks

#1) Take in multiple functions as tuple.
#2) Iterate, execute and write output to .csv
def save_output_csv(func, name = 'korea_ranks', DIR =  r'C:\DK Docs\projects\hotslogs\\'):
    f = open('{}{}.csv'.format(DIR, name), 'w', encoding = 'UTF-8')
    writer = csv.writer(f)
    writer.writerow(func)
    f.close()       

#1)Write as json
def save_output_json(func={'dummy':'dictionary'}, name = 'korea_matches', DIR =  r'C:\DK Docs\projects\hotslogs\\'):
    f = open('{}{}.json'.format(DIR, name), 'w', encoding = 'UTF-8')
    json.dump(func, f, sort_keys=True, indent=4)
    f.close()
    print('Finished writing as JSON!')


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    serial = obj.isoformat()
    return serial

#1)Open csv with ranks of players. Open Json doc of existing match data.
#2)For each row and each rank, go to the match history webpage and read table data.
#3)Check if match already exists by date. If not, click Expand and copy match data.
#4)Add new match data to match data in RAM. Save as new json doc.
#NOTE: rows count by 1, expand buttons count 4+3
#NOTE: table class = 'rgDetailTable'
#id = 'ctl00_MainContent_RadGridMatchHistory_ctl00__1'
#id = 'ctl00_MainContent_RadGridMatchHistory_ctl00_ctl09_Detail20'
#Detail = (Before_Row + 1)*10
#id = 'ctl00_MainContent_RadGridMatchHistory_ctl00_ctl15_Detail40'
#ctl 6+3, detail 10+10
#id = ctl00_MainContent_RadGridMatchHistory_ctl00_ctl112_GECBtnExpandColumn
#id = ctl00_MainContent_RadGridMatchHistory_ctl00_ctl112_GECBtnExpandColumn
def scrape_matches(ranks = r'C:\DK Docs\projects\hotslogs\korea_ranks.csv', 
                   str_date = '10/1/2017 12:00:00 AM', time_limit = 45): #time_limit=10800
    #Get list of players.    
    ranks_reader = csv.reader(open(ranks, 'r', encoding = 'UTF-8'))
    
    #Check if korea_matches.json exists. If yes, read it.   
    try:
        data_file = open(r'C:\DK Docs\projects\hotslogs\korea_matches.json', 'r', encoding = 'UTF-8')
        data = json.load(data_file)
        with open(r'D:\App Data\hotslogs\korea_matches_backup.json', 'w', encoding = 'UTF-8') as data_file_backup:
            json.dump(data, data_file_backup, sort_keys=True, indent=4)
            data_file_backup.close()
        data_file.close()        
        
    except FileNotFoundError:
        data = {}
        
    
    start_time = time.time()
     
    for row in ranks_reader:
        for playerID in row:
            run_time = time.time() - start_time
            #If the operation has been running for more than 3 hours, eject data.
            if run_time > time_limit:
                return 'Time limit reached.'
            
            #Look up webpage.
            print('Looking up {}. Run time is {} seconds.'.format(playerID, run_time))
            try:
                driver = webdriver.Firefox(executable_path = 'C:\DK Docs\projects\geckodriver.exe')
                driver.get('https://www.hotslogs.com/Player/MatchHistory?PlayerID={}'.format(playerID))
                html = driver.page_source
                
                soup = BeautifulSoup(html)
                match_rows = soup.find_all('tr',{'class':['odd rgRow','even rgAltRow']})
                
            except AttributeError:
                return 'No match history table found. Probably pageload error.'
            
            #counters and helpers
            row_counter = -1
            n_matches = 0
            match_id_list = [['match_id','map']]

            #For each row (match), check if it is in data. If not, click expand.
            for each in match_rows:
                row_counter += 1
                
                table_data = each.find_all('td')

                match_id = datetime.datetime.strptime(table_data[10].text, '%m/%d/%Y %I:%M:%S %p')
                
                if match_id > datetime.datetime.strptime(str_date, '%m/%d/%Y %I:%M:%S %p'): #checking if game is too old
                    n_matches += 1
                    match_id = json_serial(match_id)
                    match_id_list.append([match_id, table_data[2].get_text()]) #adds [match_id, map] to list of ids. This list keeps track of which matches we're looking at
                    
                    #Click expand buttons. Because of load times, not all of them will be successfully clicked. Then collect all data in another sweep
                    if match_id not in data:
                        try:                        
                            print('click {}'.format(row_counter))
                            driver.find_element_by_id('__{}'.format(row_counter)).find_element_by_class_name('details-control').click()
                            time.sleep(1.5) #Just to be sure it opens
                        except StaleElementReferenceException or NoSuchElementException:
                            pass
            
            #Store html in BeautifulSoup again because webpage has been updated by clicking expand buttons.
            #Try to find each Details Table, because not all are present.
            #Store the data.

            try: #if the last element doesn't load, close the driver and continue to the next player.
                html = driver.page_source
                soup = BeautifulSoup(html)
                detail_table = soup.find_all('tr',{'id':re.compile('MatchSummary_RadGridMatchDetails_ctl00__.*')})
                while len(detail_table) > 0:
                    try: #pop the first 10 rows. Only issue is sometimes there is only on 'a' tag instead of two. The player name 'a' tag is sometimes missing, leaving on the hero 'a' tag
                        ten_rows_one_match = [detail_table.pop(0),detail_table.pop(0),detail_table.pop(0),detail_table.pop(0),detail_table.pop(0),detail_table.pop(0),detail_table.pop(0),detail_table.pop(0),detail_table.pop(0),detail_table.pop(0)]

                        Win_element = [ten_rows_one_match[0].find_all('a')[1].get_text(),
                                       ten_rows_one_match[1].find_all('a')[1].get_text(),
                                       ten_rows_one_match[2].find_all('a')[1].get_text(),
                                       ten_rows_one_match[3].find_all('a')[1].get_text(),
                                       ten_rows_one_match[4].find_all('a')[1].get_text()
                                       ]
                        Lose_element =[ten_rows_one_match[5].find_all('a')[1].get_text(),
                                       ten_rows_one_match[6].find_all('a')[1].get_text(),
                                       ten_rows_one_match[7].find_all('a')[1].get_text(),
                                       ten_rows_one_match[8].find_all('a')[1].get_text(),
                                       ten_rows_one_match[9].find_all('a')[1].get_text()
                                       ]
                        
                        tuple_from_match_ud_list = match_id_list.pop(0)
                        match_id = tuple_from_match_ud_list[0]
                        Map = tuple_from_match_ud_list[1]
                        complete_row = {'Map':Map,
                                        'Win':Win_element,
                                        'Lose':Lose_element
                                        }
                        
                        data[match_id] = complete_row
                        with open(r'C:\DK Docs\projects\hotslogs\korea_matches.json', 'w', encoding = 'UTF-8') as data_file:
                            json.dump(data, data_file, sort_keys=True, indent=4)
                            data_file.close()
                    
                    except AttributeError:
                        pass #continue match lookup loop

            except AttributeError:
                    pass #continue player lookup loop
            
            #driver.close()
    
    return 'End of rank list reached.' 
    


