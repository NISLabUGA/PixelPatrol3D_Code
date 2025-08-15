Steps to run:

install reletively recent version of Node.js - experiments are run with V20.18.3

cd ./pp_crawler

run npm i to create appropriate node modules

might need to download a few extra packages to make sure chrome and pupeeter as installed an avaliable but npm should prompt you here. 

set config.js -> const headless_flag = true for testing

test with node capture_screenshots.js http://site1.sdktest.com 123 10000 chrome_win SE

if run finished crawler code should be working properly

cd ..

now run docker login or manually pull down the docker conatiner sking115422/pp_crawler_cont:v1

create a docker nw called pp_nw

adjust the config.yaml file to point to the CSV of urls you wish you crawl and any other parameters of interest.

run python run_op_at_scale.py to start crawling. This will instantiate docker instances to crawl the urls