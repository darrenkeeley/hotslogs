Hotslogs Scraping Script, "scrape match data.py"
======
This script scrapes hotslogs.com for matches and their hero compositions, regarding the pc game Heroes of the Storm. The script first collects the IDs of the top players on a given server, then scrapes their match histories individually.

Why this script was written
------
Hotslogs.com is a website that generates tables and statistics from user-submitted data about the PC game Heroes of the Storm (HotS). I wrote this script back in 2015, and at the time Hotslogs didn't share it's raw data, only the processed tables and stats. I wanted to run my own analyses, so I wrote a script to scrape the tables on the webpage. Now the script is unnecessary because Hotslogs does regular data dumps, but I decided to update and upload it anyway for my resume.

A bulk of the complications of this project was simply reading the HTML tables. Often, the elements didn't have ID tags, so the process for finding the relevant data requires many iterations to parse through all the possible avenues. As such, the script is fragile; any updates to the structure of the table will necessitate an update to how the script locates elements. Since I don't update this script any longer, it may not work in it's current state. The last update was November 24th, 2017.

The data this script generates
------
The script generates a json output with match ID as the key, and the winning and losing team compositions and the map.

	"match id": {
		"Lose" : [List of heroes on the losing team], 
		"Map" : "map name", 
		"Win" : [List of heroes on the winning team]
	}

For example:

	"2017-10-02T04:55:45": {
        "Lose": [
            "Garrosh",
            "Greymane",
            "Xul",
            "Malfurion",
            "Ana"
        ],
        "Map": "Dragon Shire",
        "Win": [
            "Lt. Morales",
            "Nazeebo",
            "Kael'thas",
            "Stitches",
            "Johanna"
        ]
    }

Getting started
------
I used Anaconda 3.6, which already included BeautifulSoup4.

The Selenium package must be installed.

Running the script
------
In the repo, only "scrape match data.py" needs to be opened. It is composed of two main functions, "leaderboard_ranks" and "scrape_matches."

First, the player IDs are needed. Run leaderboard_ranks to get them. The default fields are the Korean server, ranked games, in Master league. This will write a csv. In the code:

	leaderboard_ranks(region=3, gamemode=4, league='master', DIR = os.getcwd()):

Last, run scrape_matches. This will write a json file (or update an existing json file automatically) with match IDs and the composition of the teams. The default fields are the location of the ID csv, the oldest match you're willing to collect (in this case, October 1st 2017 and up will be gathered), and the time limit in seconds. It could take half a day to gather all the data from a single league.

	scrape_matches(ranks = os.getcwd() + '\korea_ranks.csv', str_date = '10/1/2017 12:00:00 AM', time_limit = 45):


Packages chosen and the structure of the script
------
BS was chosen simply for it's HTML reading capabilities. However, I discovered that the data was not all stored in the HTML page, but in a Javascript table. Only a small subset of the data was in the html, and I would have to interact with the Javascript table to get the remaining data. This required Selenium, which allowed me to interact with the page and click on "next" on the table.

The script is divided into two functions: Leaderboard Ranks and Scrape Matches. Leaderboard Ranks opens the webpage in Firefox and grabs the account numbers of the top players on a particular server. The leaderboard table only displays the first 50 or so players, with the remainders waiting to be selected by the table. Selenium is used to click "Next" and update the table with new data. The IDs is written to a csv.

Scrape Matches (SM) is the bulk of this project.
1) SM takes the list of IDs and accesses the profile page of each player. The profile page is opened in Firefox for scraping. 
2) There is a table of matches, but very little data about them. To get more specifics, Selenium must find and click the expand icon to expand each table row (match). To do this, SM reads the table in Beautiful Soup to find the expand icons, then clicks them, then reads the newly expanded table.
3) SM reads each match and checks if it is already saved, since the same match could be returned by another player.
4) The match is read and massaged into a format for the json output.
5) Eventually, all the matches are iterated through. The json output is written along the way in case the internet goes out, which was a real concern as I have left this script running overnight in the past.
