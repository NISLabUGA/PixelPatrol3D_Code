var utils = require("./utils");
const fs = require("fs");
const SimpleNodeLogger = require("simple-node-logger");

const version_number = "V2.0.6";
// V2.0.3: Empty Pages having only content "disabled" or "session is invalid" are skipped, added reason_to_click added area

const version_description =
  "Version " +
  version_number +
  "\nThis version uses default chromium shipped with the puppeteer.\nCompleted: This version’s logs DOES NOT contain unparsed net-logs,chrome console logs, element coordinates and clicked element in the dom also bounding box coordinates for the clicked element added, mhtml logs, saved console logs, screenshots , the screenshot of download page upon exiting, intercepted requests and responses and their headers using devtools, download headers, some problems are solved to enable traceback in the json logs in this version, Benign Crawling mode added, reduced crawling time; now exits after the first differend registered domain found, new user agents added,url json file added,mobile bug corrections  \nTo Do :Correct bugs after real-world runs\n\n\n\n";

// https://baixar-seguro.blogspot.com/
var crawler_mode = "SE"; // SE or benign

if (process.argv[2]) {
  var url = process.argv[2];
  var id = process.argv[3];
  var timeout = process.argv[4] * 1000;
  var agent_name = process.argv[5];

  if (process.argv[6]) {
    crawler_mode = process.argv[6];
  }

  var log_dir_name = process.argv[7];
}

// Viewport && Window size
// var agent_name="ipad_chrome"

if (crawler_mode == "SE") {
  var tranco_threshold = 5000;
} else {
  var tranco_threshold = 10000;
}

const starting_date_object = new Date();
const starting_date_unix = new Date().getTime();

// new Date().getTime()
const starting_date = utils.toISOLocal(starting_date_object);

const chrome_dir = "/home/user/chrome_user";

// // For non docker use
// var home_dir = "./pp_crawler_baseline/";

// For docker use
var home_dir = "./";

var MAIN_LOGS_DIR =
  home_dir +
  "logs/" +
  log_dir_name +
  "/" +
  starting_date_unix +
  "_" +
  version_number +
  "_siteID:" +
  id;
// var MAIN_LOGS_DIR=starting_date_unix+"_site"+id

const headless_flag = false;
const get_scrolled_ss = true;
const screenshot_timeout = 3000;
const max_num_scroll = 25;
const min_scroll_percent = 0.05;
const max_scroll_percent = 0.45;

var tab_loc_landing = "landing";
var tab_loc_newTAB = "new_tab";
var tab_loc_same = "same_tab";

const SCREENSHOT_DIR = MAIN_LOGS_DIR + "/screenshots/";
const HTML_LOGS_DIR = MAIN_LOGS_DIR + "/html_logs/";
const DOWNLOADS_DIR = MAIN_LOGS_DIR + "/downloads/";

const LOGS_DIR = MAIN_LOGS_DIR + "/logs/";
const RES_REQ_PAIRS_DIR = MAIN_LOGS_DIR + "/req_res_pairs/";
const CHROME_LOGS_DIR = MAIN_LOGS_DIR + "/chrome_logs/";
const ELEMENTS_COOR_DIR = MAIN_LOGS_DIR + "/element_coor/";
const NET_LOG_DIR = MAIN_LOGS_DIR + "/net_log/";
const JSON_LOGS = MAIN_LOGS_DIR + "/JSON_log/";

const VISITED_URLS_LOG = MAIN_LOGS_DIR + "/";

if (!fs.existsSync(MAIN_LOGS_DIR)) {
  fs.mkdirSync(MAIN_LOGS_DIR, { recursive: true });
}
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR);
}
if (!fs.existsSync(HTML_LOGS_DIR)) {
  fs.mkdirSync(HTML_LOGS_DIR);
}

if (!fs.existsSync(DOWNLOADS_DIR)) {
  fs.mkdirSync(DOWNLOADS_DIR);
}
if (!fs.existsSync(LOGS_DIR)) {
  fs.mkdirSync(LOGS_DIR);
}

if (!fs.existsSync(RES_REQ_PAIRS_DIR)) {
  fs.mkdirSync(RES_REQ_PAIRS_DIR);
}

if (!fs.existsSync(CHROME_LOGS_DIR)) {
  fs.mkdirSync(CHROME_LOGS_DIR);
}

if (!fs.existsSync(ELEMENTS_COOR_DIR)) {
  fs.mkdirSync(ELEMENTS_COOR_DIR);
}

if (!fs.existsSync(NET_LOG_DIR)) {
  fs.mkdirSync(NET_LOG_DIR);
}

if (!fs.existsSync(JSON_LOGS)) {
  fs.mkdirSync(JSON_LOGS);
}

const opts = {
  // logFilePath:LOGS_DIR+starting_date+"_"+utils.toISOLocal(new Date())+'.log',
  logFilePath: LOGS_DIR + starting_date_unix + "_" + id + ".log",
  timestampFormat: "YYYY-MM-DD HH:mm:ss.SSS",
};

const opts_download = {
  logFilePath: DOWNLOADS_DIR + starting_date_unix + "_" + id + ".log",
  timestampFormat: "YYYY-MM-DD HH:mm:ss.SSS",
};

const opts_req_res = {
  logFilePath: RES_REQ_PAIRS_DIR + starting_date_unix + "_" + id + ".log",
  timestampFormat: "YYYY-MM-DD HH:mm:ss.SSS",
};

const opts_chrome_log = {

  logFilePath: CHROME_LOGS_DIR + starting_date_unix + "_" + id + ".log",
  timestampFormat: "YYYY-MM-DD HH:mm:ss.SSS",
};

const opts_coor = {
  logFilePath: ELEMENTS_COOR_DIR + starting_date_unix + "_" + id + ".log",
  timestampFormat: "YYYY-MM-DD HH:mm:ss.SSS",
};

var json_file = JSON_LOGS + starting_date_unix + "_" + id + ".json";
var logger_json = fs.createWriteStream(json_file, {
  flags: "a", // 'a' means appending (old data will be preserved)
});

var json_file_visited_urls =
  VISITED_URLS_LOG +
  "visitedURLs" +
  "_" +
  starting_date_unix +
  "_" +
  id +
  ".json";
var logger_json = fs.createWriteStream(json_file_visited_urls, {
  flags: "a", // 'a' means appending (old data will be preserved)
});

const log = SimpleNodeLogger.createSimpleLogger(opts);
const log_download = SimpleNodeLogger.createSimpleLogger(opts_download);
var logger_rr = SimpleNodeLogger.createSimpleFileLogger(opts_req_res);
var logger_chrm = SimpleNodeLogger.createSimpleFileLogger(opts_chrome_log);
var logger_coor = SimpleNodeLogger.createSimpleFileLogger(opts_coor);

const keywords = [
  "not a robot",
  "NOT A ROBOT",
  "not a robot",
  "Activate now",
  "activate now",
  "ACTIVATE NOW",
  "Download",
  "download",
  "DOWNLOAD",
  "Accept and Continue",
  "accept and continue",
  "ACCEPT AND CONTINUE",
  "add to chrome",
  "Add to Chrome",
  "ADD TO CHROME",
  "ok",
  "Ok",
  "OK",
  "Next",
  "next",
  "NEXT",
  "Continue",
  "continue",
  "CONTINUE",
  "Update",
  "update",
  "UPDATE",
  "Browser update",
  "BROWSER UPDATE",
  "browser update",
  "Restart",
  "restart",
  "RESTART",
  "Skip Ad",
  "skip ad",
  "SKIP AD",
  "PLAY",
  "Play",
  "play",
  "Install",
  "install",
  "INSTALL",
  "Always Use",
  "always use",
  "ALWAYS USE",
  "Call",
  "CALL",
  "call",
  "SELECT",
  "Select",
  "select",
  "Yes",
  "YES",
  "yes",
  "Quick Support",
  "QUICK SUPPORT",
  "quick support",
  "Renew now",
  "RENEW NOW",
  "renew now",
  "Install & Register Now",
  "SEE MORE",
  "See More",
  "See more",
  "Proceed",
  "PROCEED",
  "proceed",
  "Create Account",
  "CREATE ACCOUNT",
  "create account",
  "Get it now",
  "GET IT NOW",
  "get it now",
  "Tap to proceed",
  "TAP TO PROCEED",
  "Virus",
  "VIRUS",
  "virus",
  "Delete",
  "DELETE",
  "delete",
  "Antivirus",
  "ANTIVIRUS",
  "antivirus",
  "free",
  "FREE",
  "Free",
  "Congratulations",
  "congratulations",
  "CONGRATULATIONS",
  "Offer",
  "offer",
  "OFFER",
  "Coupon",
  "COUPON",
  "coupon",
  "open",
  "OPEN",
  "Open",
  "accept",
  "Accept",
  "ACCEPT",
  "Countinue",
  "CONTINUE",
  "continue",
  "CAPCHA",
  "preCAPCHA",
  "claim",
  "CLAIM",
  "Claim",
];

const AFTER_CLICK_WAIT = 5000; //Time to wait after a succesful click
// The below will be used if there is no "frameStoppedLoading" event
const PAGE_LOAD_TIMEOUT = 30000; // Max time to wait for a page load
const PAGE_LOAD_TIMEOUT_TABS = PAGE_LOAD_TIMEOUT - AFTER_CLICK_WAIT; // Max time to wait for a page load
//AFTER_LOAD_WAIT = 5 # TO PAUSE FOR A LITTLE BIT AFTER PAGE LOAD MESSAGE
const WAIT_AFTER_RESIZE = 3000;
const WAIT_NEW_TAB_LOAD = 10000;
const PAGE_TIMEOUT = 30000;
var the_tab_interval = 360 * 1000;
var the_tab_interval2 = 360 * 1000;

USER_AGENTS = {
  firefox_win: {
    user_agent:
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0",
    window_size_cmd: [[1920, 1080, 4]],
    device_size: [1920, 1080],
    device_scale_factor: 1,
    mobile: false,
    isLandscape: false,
  },

  safari_mac: {
    user_agent:
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15",
    window_size_cmd: [[1920, 1080, 4]],
    device_size: [1920, 1080],
    device_scale_factor: 1,
    mobile: false,
    isLandscape: false,
  },

  edge_win: {
    user_agent:
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36 Edg/104.0.1293.47",
    window_size_cmd: [[1920, 1080, 4]],
    device_size: [1920, 1080],
    device_scale_factor: 1,
    mobile: false,
    isLandscape: false,
  },
  chrome_win: {
    user_agent:
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
    window_size_cmd: [[1920, 1080, 4]],
    device_size: [1920, 1080],
    device_scale_factor: 1,
    mobile: false,
    isLandscape: false,
  },
  chrome_linux: {
    user_agent:
      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
    window_size_cmd: [[1920, 1080, 4]],
    device_size: [1920, 1080],
    device_scale_factor: 1,
    mobile: false,
    isLandscape: false,
  },

  // "chrome_linux": {
  //     "user_agent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36',
  //     "window_size_cmd": [[1366,768],[1536,864],[1920,1080]],
  //     "device_size": [1920,1080],
  //     "device_scale_factor": 1,
  //     "mobile": true,
  //     'isLandscape': false

  // },
  chrome_mac: {
    user_agent:
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36",
    window_size_cmd: [[1920, 1080, 4]],
    device_size: [1920, 1080],
    device_scale_factor: 1,
    mobile: false,
    isLandscape: false,
  },
  chrome_android_phone: {
    user_agent:
      "Mozilla/5.0 (Linux; Android 12; SM-G988U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Mobile Safari/537.36",
    window_size_cmd: [
      [360, 800],
      [360, 640],
    ], //the most popular resolution
    device_size: [1440, 3200],
    device_scale_factor: 1, //maybe 1? to make images smaller
    mobile: true,
    isLandscape: false,
  },
  safari_iphone: {
    //11 pro max safari
    user_agent:
      "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/605.1 NAVER(inapp; search; 1000; 11.6.2; 11PROMAX)",
    window_size_cmd: [[414, 896]],
    device_size: [1242, 2688],
    device_scale_factor: 1,
    mobile: true,
    isLandscape: false,
  },
  safari_ipad: {
    user_agent:
      "Mozilla/5.0 (iPad; CPU OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Mobile/15E148 Safari/604.1",
    window_size_cmd: [
      [1024, 768],
      [768, 1024],
    ],
    device_size: [1536, 2048],
    device_scale_factor: 1,
    mobile: true,
    isLandscape: false,
  },
  // "user_agent": 'Mozilla/5.0 (iPad; CPU OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Mobile/15E148 Safari/604.1',
  // Samsung Galaxy Tab 10

  chrome_android_tab: {
    user_agent:
      "Mozilla/5.0 (Linux; Android 10; MRX-AL09) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.50 Safari/537.36",
    window_size_cmd: [
      [1280, 800],
      [800, 1280],
    ],
    device_size: [1600, 2560],
    device_scale_factor: 1,
    mobile: true,
    isLandscape: false,
  },

  // resources: https://www.mydevice.io/#compare-devices
  // https://www.whatismybrowser.com/guides/the-latest-user-agent/chrome?utm_source=whatismybrowsercom&utm_medium=internal&utm_campaign=latest-user-agent-index
  //https://gbksoft.com/blog/common-screen-sizes-for-responsive-web-design/
  // https://yesviz.com/viewport/
  // https://gs.statcounter.com/screen-resolution-stats/mobile/worldwide/#monthly-202010-202110
  // https://experienceleague.adobe.com/docs/target/using/experiences/vec/mobile-viewports.html?lang=en
  // https://www.icwebdesign.co.uk/common-viewport-sizes
  // https://www.deviceinfo.me/
  // https://myip.ms/view/comp_browsers/14504/Safari_15_1.html
  // https://screensiz.es/tablet
  // https://whatmyuseragent.com/device/hu/huawei-matepad-pro

  //   // Samsung Galaxy S7, S7 edge
  //   "chrome_android_s7":{
  //       "user_agent": 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G935F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Mobile Safari/537.36',
  //       "window_size_cmd": [[360,640]],  //the most popular resolution
  //       "device_size": [1440,2560],
  //       "device_scale_factor": 1,  //maybe 1? to make images smaller
  //       "mobile": true,
  //       'isLandscape': false

  //   },

  //   "chrome_android_s20":{
  //     "user_agent": 'Mozilla/5.0 (Linux; Android 12; SM-G988U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Mobile Safari/537.36',
  //     "window_size_cmd": [[360,800]],  //the most popular resolution
  //     "device_size": [1440,3200],
  //     "device_scale_factor": 1,  //maybe 1? to make images smaller
  //     "mobile": true,
  //     'isLandscape': false

  // },

  // "12promaxfortest":{
  //     "user_agent": 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G935F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Mobile Safari/537.36',
  //     "window_size_cmd": [[428, 926]],
  //     "device_size": [1284, 2778],
  //     "device_scale_factor": 3,
  //     "mobile": true,
  //     'isLandscape': false

  // },

  // "iphone_ios_chrome":{
  //     "user_agent": 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/94.0.4606.76 Mobile/15E148 Safari/604.1',
  //     "window_size_cmd": [[414,896]],
  //     "device_size": [1242, 2688],
  //     "device_scale_factor": 3,
  //     "mobile": true,
  //     'isLandscape': false

  // },
  // "nexus9tab_chrome":{
  //   "user_agent": 'Mozilla/5.0 (iPad; CPU OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Mobile/15E148 Safari/604.1',
  //     "window_size_cmd": [[1024,768],[768,1024]],
  //     "device_size": [1536,2048],
  //     "device_scale_factor": 1,
  //     "mobile": true,
  //     'isLandscape': false

  // },
};

// "ipad_chrome" to ipad_safari    ,"iphone_safari" added  "huaweitab_chrome" added

logger_coor.info(version_description);
logger_rr.info(version_description);
logger_chrm.info(version_description);
log_download.info(version_description);
log.info(version_description);

module.exports.tranco_threshold = tranco_threshold;
module.exports.crawler_mode = crawler_mode;
module.exports.tab_loc_landing = tab_loc_landing;
module.exports.tab_loc_newTAB = tab_loc_newTAB;
module.exports.tab_loc_same = tab_loc_same;

module.exports.json_file = json_file;
module.exports.json_file_visited_urls = json_file_visited_urls;

module.exports.JSON_LOGS = JSON_LOGS;
module.exports.the_tab_interval = the_tab_interval;
module.exports.the_tab_interval2 = the_tab_interval2;
module.exports.NET_LOG_DIR = NET_LOG_DIR;
module.exports.logger_coor = logger_coor;
module.exports.PAGE_TIMEOUT = PAGE_TIMEOUT;
module.exports.logger_chrm = logger_chrm;
module.exports.CHROME_LOGS_DIR = CHROME_LOGS_DIR;
module.exports.logger_rr = logger_rr;
module.exports.url = url;
module.exports.id = id;
module.exports.timeout = timeout;
module.exports.log_download = log_download;
module.exports.log = log;
module.exports.home_dir = home_dir;
module.exports.AFTER_CLICK_WAIT = AFTER_CLICK_WAIT;
module.exports.PAGE_LOAD_TIMEOUT = PAGE_LOAD_TIMEOUT;
module.exports.PAGE_LOAD_TIMEOUT_TABS = PAGE_LOAD_TIMEOUT_TABS;
module.exports.WAIT_AFTER_RESIZE = WAIT_AFTER_RESIZE;
module.exports.WAIT_NEW_TAB_LOAD = WAIT_NEW_TAB_LOAD;
module.exports.agent_name = agent_name;
module.exports.keywords = keywords;
module.exports.starting_date = starting_date;
module.exports.MAIN_LOGS_DIR = MAIN_LOGS_DIR;
module.exports.SCREENSHOT_DIR = SCREENSHOT_DIR;
module.exports.HTML_LOGS_DIR = HTML_LOGS_DIR;
module.exports.DOWNLOADS_DIR = DOWNLOADS_DIR;
module.exports.LOGS_DIR = LOGS_DIR;
module.exports.USER_AGENTS = USER_AGENTS;
module.exports.starting_date_unix = starting_date_unix;
module.exports.log_dir_name = log_dir_name;
module.exports.headless_flag = headless_flag;
module.exports.get_scrolled_ss = get_scrolled_ss;
module.exports.screenshot_timeout = screenshot_timeout;
module.exports.max_num_scroll = max_num_scroll;
module.exports.min_scroll_percent = min_scroll_percent;
module.exports.max_scroll_percent = max_scroll_percent;
module.exports.chrome_dir = chrome_dir;
