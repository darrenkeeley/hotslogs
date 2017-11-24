Hotslogs Scraping Script
======

#Why this script was written
Hotslogs.com is a website that generates tables and statistics from user-submitted data about the PC game Heroes of the Storm (HotS). I wrote this script back in 2015, and at the time Hotslogs didn't share it's raw data, only the processed tables and stats. I wanted to run my own analyses, so I wrote a script to scrape the tables on the webpage. Now the script is unnecessary because Hotslogs does regular data dumps, but I decided to update and upload it anyway for my resume.

#Packages: Beautiful Soup and Selenium
BS was chosen simply for it's HTML reading capabilities. However, I discovered that the data was not all stored in the HTML page, but in a Javascript table. I could only view a small subset of the data upon loading the page, and would have to interact with the Javascript table to get the remaining data. This required Selenium, which allowed me to interact with the page and click on elements from my browser.

A bulk of the complications of this project was simply reading the HTML tables. Often, the elements didn't have ID tags, so the process for finding the relevant data requires many iterations to parse through all the possible avenues. As such, the script is fragile; any updates to the structure of the table will necessitate an update to how the script locates elements. Since I don't update this script any longer, it may not work in it's current state. The last update was November 24th, 2017.

#Structure of the script
The script is divided into two functions: Leaderboard Ranks and Scrape Matches. Leaderboard Ranks calls the webpage and grabs the account numbers of the top players on a particular server. This way, I can get the match data from the best players. The leaderboard may be long hand have multiple Javascript tables behind the initial one. Selenium is used to click "Next" and get to the next table. The data is written to a csv.

Scrape Matches (SM) is the bulk of this project.
1) SM takes the list of account numbers and accesses the profile of the first player. The profile page is opened in Firefox for scraping. 
2) There is a table of matches, but very little data about them. To get more specifics, Selenium must find and click the expand icon to expand each table row (match). To do this, SM reads the table in Beautiful Soup to find the expand icons, then clicks them, then reads the newly expanded table 