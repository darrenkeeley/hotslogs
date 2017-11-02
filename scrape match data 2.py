from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from bs4 import BeautifulSoup
import time, csv, datetime, json

#1) Open leaderboard in Firefox.
#2) Save the HTML for Soup scraping.
#3) Soup scrape number of pages and table data.
#4) Click next, save table data, iterate for pages - 1.
#
#Elements can have multiple classes, separated by spaces.
#The Next Page button has two classes, but I chose the unique one rgPageNext.

def leaderboard_ranks(region=3, gamemode=4, league='master', DIR = r'D:\App Data\hotslogs\\', save_page=False):
    driver = webdriver.Firefox()
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

    #print(player_ranks)
    return player_ranks

#1) Take in multiple functions as tuple.
#2) Iterate, execute and write output to .csv
def save_output_csv(func, name = 'korea_ranks', DIR =  r'D:\App Data\hotslogs\\'):
    f = open('{}{}.csv'.format(DIR, name), 'w', encoding = 'UTF-8')
    writer = csv.writer(f)
    writer.writerow(func)
    f.close()       

#1)Write as json
def save_output_json(func={'dummy':'dictionary'}, name = 'korea_matches', DIR =  r'D:\App Data\hotslogs\\'):
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
def scrape_matches(ranks = r'D:\App Data\hotslogs\korea_ranks.csv', 
                   str_date = '12/17/2015 12:00:00 AM', time_limit = 10800):
    #Get list of players.    
    ranks_reader = csv.reader(open(ranks, 'r', encoding = 'UTF-8'))
    
    #Check if korea_matches.json exists. If yes, read it.   
    try:
        data_file = open(r'D:\App Data\hotslogs\korea_matches.json', 'r', encoding = 'UTF-8')
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
                driver = webdriver.Firefox()
                driver.get('https://www.hotslogs.com/Player/MatchHistory?PlayerID={}'.format(playerID))
                html = driver.page_source
                
                soup = BeautifulSoup(html)
                table = soup.find('table', {'id':'ctl00_MainContent_RadGridMatchHistory_ctl00'})
    
                match_rows = table.find_all('tr',{'class':'rgRow'})
                
            except AttributeError:
                return 'No match history table found. Probably pageload error.'
            
            #counters and helpers
            row_counter = 0
            expand_counter = 1
            n_matches = 0
            match_id_list = [['match_id','map']]

            #For each row (match), check if it is in data. If not, click expand.
            for each in match_rows:
                row_counter += 1
                expand_counter += 3
                if expand_counter < 10: expand_counter_helper = 0
                else: expand_counter_helper = ''
                
                table_data = each.find_all('td')
                match_id = datetime.datetime.strptime(table_data[9].text, '%m/%d/%Y %I:%M:%S %p')
                if match_id > datetime.datetime.strptime(str_date, '%m/%d/%Y %I:%M:%S %p'):
                    n_matches += 1
                    match_id = json_serial(match_id)
                    match_id_list.append([match_id, table_data[2].get_text()])
                    
                    
                    #Click expand buttons. Because of load times, not all of them will be successfully clicked.
                    if match_id not in data:
                        try:
                            element = 'ctl00_MainContent_RadGridMatchHistory_ctl00_ctl{}{}_GECBtnExpandColumn'.format(expand_counter_helper, expand_counter)
                            time.sleep(8)                            
                            print('click {}'.format(expand_counter))
                            driver.find_element_by_id(element).click()
                        except StaleElementReferenceException or NoSuchElementException:
                            pass
            
            #Store html in BeautifulSoup again because webpage has been updated.
            #Try to find each Details Table, because not all are present.
            #Store the data.
            time.sleep(30)
            try: #if the last element doesn't load, close the driver and continue to the next player.
                html = driver.page_source
                soup = BeautifulSoup(html)
                table = soup.find('table', {'id':'ctl00_MainContent_RadGridMatchHistory_ctl00'}).find('tbody')
                
                for i in range(1, n_matches +1):
                    ctl_counter = 3 + i*3
                    if ctl_counter < 10: ctl_counter_helper = 0
                    else: ctl_counter_helper = ''
                    try:
                        #print('ctl00_MainContent_RadGridMatchHistory_ctl00_ctl{}{}_Detail{}'.format(ctl_counter_helper, ctl_counter, i*10))
                        detail_table = table.find('table', {'id':'ctl00_MainContent_RadGridMatchHistory_ctl00_ctl{}{}_Detail{}'.format(ctl_counter_helper, ctl_counter, i*10)})
                        detail_table = detail_table.find('tbody').find_all('tr')
                        #Read the details table for MMR and heroes.
                        #0 Winning team header, 1 - 5 Winning team, 6 Losing team header, 7 - 11 Losing team.
                        #First get MMR, then get hero list.
                        MMR_element = [detail_table[0].find_all('td')[1].get_text()[9:13], 
                                       detail_table[6].find_all('td')[1].get_text()[9:13]
                                       ]
                        Win_element = [detail_table[1].find_all('td')[2].find('a').get_text(),
                                       detail_table[2].find_all('td')[2].find('a').get_text(),
                                       detail_table[3].find_all('td')[2].find('a').get_text(),
                                       detail_table[4].find_all('td')[2].find('a').get_text(),
                                       detail_table[5].find_all('td')[2].find('a').get_text()
                                       ]
                        Lose_element = [detail_table[7].find_all('td')[2].find('a').get_text(),
                                       detail_table[8].find_all('td')[2].find('a').get_text(),
                                       detail_table[9].find_all('td')[2].find('a').get_text(),
                                       detail_table[10].find_all('td')[2].find('a').get_text(),
                                       detail_table[11].find_all('td')[2].find('a').get_text()
                                       ]
                        
                        match_id = match_id_list[i][0]
                        Map = match_id_list[i][1]
                        complete_row = {'MMR':MMR_element,
                                                  'Map':Map,
                                                  'Win':Win_element,
                                                  'Lose':Lose_element
                                        }
                                        
                        data[match_id] = complete_row
                        with open(r'D:\App Data\hotslogs\korea_matches.json', 'w', encoding = 'UTF-8') as data_file:
                            json.dump(data, data_file, sort_keys=True, indent=4)
                            data_file.close()
                    
                    except AttributeError:
                        pass #continue match lookup loop

            except AttributeError:
                    pass #continue player lookup loop
            
            driver.close()
    
    return 'End of rank list reached.' 
    


