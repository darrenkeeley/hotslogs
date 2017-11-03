from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from bs4 import BeautifulSoup
import time, csv, datetime, json, re

html = open(r'C:\DK Docs\projects\hotslogs\test page.html', 'r', encoding = 'UTF-8')
soup = BeautifulSoup(html)
detail_table = soup.find_all('tr',{'id':re.compile('MatchSummary_RadGridMatchDetails_ctl00__.*')})

detail_table_backup = detail_table
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