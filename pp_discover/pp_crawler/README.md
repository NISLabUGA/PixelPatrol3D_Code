capture_screenshots.js : That is the main script to run the crawler. To run the script

node capture_screenshots.js [URL] [ID] [TIMEOUT] [USER_AGENT] [CRAWLING_MODE]

URL: The URL to be crawled ID : the website id you can give it a number of your choice. It is used to create logs. When you visit the logs file in which all the logs related to that website crawl are held, the naming for the specific crawl folder consists of siteid and the current time. TIMEOUT: The amount of time in second for program to run at max 

USER_AGENT: choose one of the following: firefox_win, safari_mac, edge_win, chrome_win ,chrome_linux ,chrome_mac, chrome_android_phone, safari_iphone, safari_ipad, chrome_android_tab  (they are specified in the config.js file)

CRAWLING_MODE: Run the crawler to crawl either benign or SE webpages. This parameter is optional. It is by default "SE"

util.js: contains helper functions and classes used in the crawler

config.js: Contains configuration parameters and user agents and screen resolution related things. IF you want to change the user agent of the crawler, just copy the name of the device like “linux_chrome” and paste it into the agent_name.

tranco.csv: this is the CSV file containing the top 1 million websites and their popularity ranking. This file is changing by day. And we will use the current one when we will scale the project.


Screenshot and html naming convention: (their naming are the same)
X_Y_Z_WxH.E

X: UNIX time in milliseconds when the screenshot is taken for all the viewports

Y: URL hash value, which is the md5 hash of the URL after the parameters in the URL coming after the “?” mark excluded. The URL is the URL of the website in the screenshot.

Z: It is the tab location, which can take the following values:

-	FIRST: The first landing URL visited.
-	land* : The landing(first) tab before the *. Click. * is an integer. If it says “land1”, which means the screenshot of the landing page before the second click (indexes start from zero)
-	lafter* : The landing page after the click on the *. coordinate. That screenshot is taken by the crawler, if there is any html changes and url don’t change on the landing tab after the *. Click. For URL changes in the landing pages please refer the following location. 
-	lsame* : If the URL changes after the click on the *. Coordinate on the landing tab.
-	new* : if the click on the *. coordinate  on the landing tab opens a new tab. This can also denote to the click on the new tab before the click on the first coordinate (we are also doing additional clicks on the new tabs opened by the clicks on the landing page)
-	newBC* : On the new tab opened by the landing page; before the click on the *. coordinate calculated on that new tab
-	newNEXTBC* : On the new tab opened by the new tab; before the click on the *. Coordinate calculated on that second level new tab
-	newAC* : On the new tab opened by the landing page; after the click on the *. coordinate calculated on that new tab
-	newNEXTAC* : On the new tab opened by the new tab; after the click on the *. Coordinate calculated on  that second level new tab
-	newSAME* : If the URL changes on the new tab after the click on the *. Coordinate calculated on that new tab opened after the clicks done on the landing tab
-	newNEXTSAME* : If the URL changes on the new tab after the click on the *. Coordinate calculated on that new tab opened after the clicks done on the new tab opened.
-	newNEW* : if the click on the *. coordinate on the new tab opened by the landing tab opens a new tab. 
-	newNEWNEXT* : if the click on the *. coordinate  on the new tab opened by the new tab opens a new tab

The figure below summarizes the flow of the tabs: 

![tabs](https://user-images.githubusercontent.com/76975914/152900631-00b3fbb7-1ea3-4402-a005-9cd5538ce251.png)





W: the width of the screenshot or viewport of the tab

H: the height of the screenshot or viewport of the tab

E: the extension of the image, i.e., png




Browser flags:

'--hide-scrollbars'  -> defined, because it increases performance
 '--mute-audio' -> defined, because it increases performance
'--disable-infobars' -> defined, because it increases performance
 '--dns-log-details' -> to save dns queries to the netlogs
 `--log-net-log=${netlogfile}` -> to save netlogs to the specified json file
  '--no-sandbox' -> to reduce the security level in containers
'--disable-setuid-sandbox' -> to reduce the security level in containers
'--ignore-certificate-errors' to ignore ssl certificate errors on the visited pages
"--disable-web-security" -> to reduce the security level and to obtain more SE examples
"--allow-running-insecure-content" -> -> to reduce the security level and to obtain more SE examples
"--disable-features=IsolateOrigins" -> As of Chrome 81, it is mandatory to pass both --disable-site-isolation-trials and a non-empty profile path via --user-data-dir in order for --disable-web-security to take effect: to disable site isolation, disabling IsolateOrigins is required for some chrome versions
 "--disable-site-isolation-trials" -> to disable web security
"--allow-popups-during-page-unload" -> to reduce the security level for more SE examples
"--disable-popup-blocking"  -> to reduce the security level for more SE examples
 '--disable-gpu' -> to disable GPU hardware acceleration.
 `--window-size=${ width },${ height }` -> to specify default window size of the browser, when a new tab opens it uses that default size
  `--user-agent=${ useragent}` -> to specify the default user agent
 '--shm-size=3gb' -> I defined this to increase the performance of the unstable chromium, because it was crashing after many tabs opened
 `--user-data-dir=${config.home_dir}chrome_user/` -> to disable web security, user data directory is required.
