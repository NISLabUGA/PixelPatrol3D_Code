'use strict';
var utils = require('./utils');
var config=require('./config');
const fs = require('fs')
const path = require('path');
const { Console } = require('console');

// const { Console } = require('console');
// const { JSHandle } = require('puppeteer');


// TODO: Try to remove elements whose parentElement <a> tag or the tag itself (href) points to home page.
//Images that are larger than 900 sq. pixels in area will be placed at the beginning of
// the Action list. The idea is that images and as are more likely to lead to links than others.
// TODO: Try to remove elements whose parentElement <a> tag or the tag itself (href) points to home page.
//Images that are larger than 900 sq. pixels in area will be placed at the beginning of
// the Action list. The idea is that images and as are more likely to lead to links than others.

var IMG_PREFERENCE_THRESHOLD = 900
var SHORT_PAUSE = 5
// //Tries to retain return elements with unique sizes, and unique mid-points
// //On some pages there are very close click-points that don't do anything different.
// //Hence we try to filter out elements that have spatially close click points.

async function get_unique_elements(elems){

    var skip_it=false
    var R = 100;  //Coarseness in pixels for determining unique click points
    var MAX_SAME_COORD = 2 //Don't allow more than 2 elements on same x or y coordinates.
    const ret_elems = []
    const prev_elems =new Set()  //Contains width and height of prev elements
    const prev_mid_points =new Set()
    const prev_x = new utils.DefaultDict(Number)
    const prev_y = new utils.DefaultDict(Number)
    var mp_rounded;
    for (const elem in elems){

         for (let item of prev_elems.keys()) {
            if(item.toString() == [elems[elem][3],elems[elem][2]].toString())
            skip_it=true
               continue
            //true on match.
          }
          if(skip_it==true){
            skip_it=false
            continue
          }
        const coords = [elems[elem][0], elems[elem][1]]

        mp_rounded = [utils.any_round(coords[0], R), utils.any_round(coords[1], R)]
        if (prev_mid_points.has(mp_rounded)){
            continue;
        }
        for (let item of prev_mid_points.keys()) {
          if(item.toString() == mp_rounded.toString())
          skip_it=true
             continue
          //true on match.
        }
        if(skip_it==true){
          skip_it=false
          continue
        }
        // prev_x doesn't make sense at all in pages where all different kinds of elements are vertically aligned
        //for example: https://onlinetviz.com/american-crime-story/2/1
        if (prev_y[elems[elem][1]] >= MAX_SAME_COORD){
            continue;
        }
        //print "debug, unique size elems", elem.size['width'], elem.size['height']
        ret_elems.push(elems[elem])
        prev_elems.add([elems[elem][3],elems[elem][2]])
        prev_mid_points.add(mp_rounded)
        prev_x[elems[elem][0]] += 1
        prev_y[elems[elem][1]] += 1
    }

    return ret_elems
};



function element_area(elem){
  return elem[2] * elem[3]
}


// //Given a list of elements, Sort the elements by area,
async function filter_elements(elems, imgs,width,height){
    const rest_imgs = []
    const selected_imgs = []
    for (const img in imgs){
      if (element_area(imgs[img]) > IMG_PREFERENCE_THRESHOLD){
          selected_imgs.push(imgs[img])
      }
      else{
          rest_imgs.push(imgs[img])
        }
  }
    imgs = utils.sorted(selected_imgs, {key: x=>x[2]*x[3], reverse: true})
    elems = elems.concat(rest_imgs)
    elems = utils.sorted(elems, {key: x=>x[2]*x[3], reverse: true})
    elems = imgs.concat(elems)
    elems =await get_unique_elements(elems)
    elems = elems.slice(0, 20);
    const elem_coords = []
    for (const elem in elems){
        elem_coords.push([elems[elem][0], elems[elem][1]])
     }
    if (elem_coords.length == 0){
       //width, height = config.USER_AGENTS[agent_name]['window_size_cmd']
       var click_point = [width/2, height/2]
       // elem_coords.push([click_point])
      elem_coords.push(click_point)
    }
    return elem_coords
}
process.on('unhandledRejection', error => {
    // Prints "unhandledRejection woops!"
    //  config.log.error("unhandledRejection woops! error is:"+error)
    //  config.log.error("in:"+config.site_id+' :: '+config.url)
    //  child.kill('SIGINT')
    //  config.logger_rr.end()
    //  config.logger_chrm.end()
 })



async function load_page(){


  config.log.info("Starting date is:"+config.starting_date)

  var rand_viewports=[]
  if(config.USER_AGENTS[config.agent_name]["mobile"]){
      rand_viewports=config.USER_AGENTS[config.agent_name]["window_size_cmd"]
  }else{
      rand_viewports=utils.getRandViewports(config.USER_AGENTS[config.agent_name]["window_size_cmd"])
  }


  var width=rand_viewports.slice(-1)[0][0]
  var height=rand_viewports.slice(-1)[0][1]
  config.log.info("The initial width*height is:"+width+"*"+height)






  const puppeteer = require('puppeteer-extra')
  const StealthPlugin = require('puppeteer-extra-plugin-stealth')

  const stealth = StealthPlugin()
  puppeteer.use(StealthPlugin())



   var count = 0

  //  const device_width = config.USER_AGENTS[agent_name]["device_size"][0]
  //  const device_height = config.USER_AGENTS[agent_name]["device_size"][1]
   const args = [
    // '--headless',

    '--hide-scrollbars',

    '--mute-audio',
    '--no-sandbox',
    // '--dns-log-details',
    // '--net-log-capture-mode=Everything',
    // `--log-net-log=${config.NET_LOG_DIR}${config.id}.json`,
    // '--single-process',
    '--disable-setuid-sandbox',
    '--disable-infobars',
    // '--window-position=0,0',
    '--ignore-certificate-errors',
    // `--ignore-certificate-errors-spki-list=${path.resolve('/home/irfan/.mitmproxy/mitmproxy-ca.pem')}`,
    // '--ignore-certificate-errors-spki-list',
    "--disable-web-security",
    "--allow-running-insecure-content",
    "--disable-popup-blocking",
    '--disable-dev-shm-usage',
    // '--enable-blink-features=HTMLImports',
    '--disable-gpu',
    `--window-size=${ width },${ height }`,
    `--user-agent=${ config.USER_AGENTS[config.agent_name]["user_agent"] }`,
     `--use-mobile-user-agent=${ config.USER_AGENTS[config.agent_name]["mobile"] }`,
     '--shm-size=3gb',

    // '--proxy-server=localhost:8089'
    // `--proxy-server=localhost:${server.port}`



   ];


    const options = {
      // ignoreDefaultArgs: true,
      headless: false,
      args,
      // executablePath:home_dir+'chromium/src/out/Irfan/chrome',
      ignoreHTTPSErrors: true,
      defaultViewport:{ width:  width,
                        height: height ,
                        deviceScaleFactor:config.USER_AGENTS[config.agent_name]["device_scale_factor"],
                        // isMobile:config.USER_AGENTS[agent_name]["mobile"],
                        // hasTouch:config.USER_AGENTS[agent_name]["mobile"],
                        // isLandscape: config.USER_AGENTS[agent_name]["isLandscape"]
                      },
                      // userDataDir:config.home_dir+'chrome_user/',
   };


  //  isLandscape: true



    await puppeteer.launch(options).then(async browser =>
     {


const waitTillHTMLRendered = async (page, timeout = config.PAGE_LOAD_TIMEOUT) => {
const checkDurationMsecs = 1000;
const maxChecks = timeout / checkDurationMsecs;
let lastHTMLSize = 0;
let checkCounts = 1;
let countStableSizeIterations = 0;
const minStableSizeIterations = 3;


while(checkCounts++ <= maxChecks){

 const html=await page.evaluate(()=>{
    if(document.body!=null){
      var html = document.body.innerHTML
      return html
    }else{
      return null
    }

  })

//  let html = await page.content();
 if(html==null){
   console.log("HERE IN WAITTILL")
   break
 }

 let currentHTMLSize = html.length;
 // let bodyHTMLSize = await page.evaluate(() => document.body.innerHTML.length);
 // console.log('last: ', lastHTMLSize, ' <> curr: ', currentHTMLSize, " body html size: ", bodyHTMLSize);
 if(lastHTMLSize != 0 && currentHTMLSize == lastHTMLSize)
   countStableSizeIterations++;
 else
   countStableSizeIterations = 0; //reset the counter

 if(countStableSizeIterations >= minStableSizeIterations) {
   console.log("Page rendered fully..");
   break;
 }

 lastHTMLSize = currentHTMLSize;
 await page.waitForTimeout(checkDurationMsecs);
}
};






  try{

       var the_interval = config.timeout *1000 //in milliseconds


       browser.on('targetcreated', async target => {

        if (target.type() == 'page') {
          var page = await target.page()
          await stealth.onPageCreated(page)

          await page.setDefaultNavigationTimeout(0)
          await page.setCacheEnabled(false)


          page.on('dialog', async dialog => {
            console.log('dialog');
            await dialog.accept();

          });



     }})

      const page = await browser.newPage(); //open new tab
      await (await browser.pages())[0].close(); //close first one, to overcome the bug in stealth library mentioned in
      //https://github.com/berstend/puppeteer-extra/issues/88
      var visited_URLs =new Set()
      var is_mobile= config.USER_AGENTS[config.agent_name]["mobile"]
      var wait_interval = 5000
      count=0

       // checks if the timeout has exceeded every few seconds
       var trigger = await setInterval(async function()
       {
           // close the browser if the run exfceeds timeout interval
           if (count >= the_interval )
           {
             config.log.info(new Date(Date.now()).toLocaleString())
             config.log.info('visit ended,exiting program')
             clearInterval(trigger);
             await process_ended(config.id,browser)

             return
           }
           count = count+wait_interval
       }, wait_interval);
       try{


        config.log.info('Crawling is started. Visiting page')
        config.log.info("Browser version is:"+(await page.browser().version()))
        config.log.info("User agent is:"+config.USER_AGENTS[config.agent_name]["user_agent"])
        await page.goto(config.url , { waitUntil: 'load'});
        await waitTillHTMLRendered(page)

        var [elems, imgs] = await page.evaluate(()=> {
            function elementDimensions(element, wHeight, wWidth) {
                var boundRect = element.getBoundingClientRect();
                var midy = boundRect.top + (boundRect.height / 2.0);
                var midx = boundRect.left + (boundRect.width / 2.0);
                if (boundRect.height != 0 && boundRect.width != 0 &&
                midy < wHeight && midx < wWidth && midy > 0 && midx > 0)
                return [midx, midy, boundRect.height, boundRect.width];
            else
            return [];
            }
            // Args: an array of element objects, window height and window width
            // This function filters out elements that are
            // (1) of size 0
            // (2) Outside the viewport vertically or horizontally.
            // Returns a array of arrays
            function filterElementArrays(elements, wHeight, wWidth) {
                var elem_sizes = [];
                for (var element of elements){
                    var elem = elementDimensions(element, wHeight, wWidth);
                if (elem.length > 0)
                   elem_sizes.push(elem);
            }
            return elem_sizes;
            }
            // Similar to filterElementArrays but takes xpathResult object as
            // one of the arguments
            function filterXpathResults(xpathResults, wHeight, wWidth) {
            var elem_sizes = [];
            var element = xpathResults.iterateNext();
            while (element) {
            var elem = elementDimensions(element, wHeight, wWidth);
            if (elem.length > 0)
              elem_sizes.push(elem);
              element = xpathResults.iterateNext();
            }
            return elem_sizes;
            }


            function getElementsByXpath(path) {
            var xpathres =  document.evaluate(
                      path, document, null,
                      XPathResult.UNORDERED_NODE_ITERATOR_TYPE, null);
            return xpathres;
            }


            // //Tries to retain return elements with unique sizes, and unique mid-points
            // //On some pages there are very close click-points that don't do anything different.
            // //Hence we try to filter out elements that have spatially close click points.

            function getElementData() {

                var wHeight = window.innerHeight;
                var wWidth = window.innerWidth;
                var element_data = [];
                var divs_xpath = getElementsByXpath('//div[not(descendant::div) and not(descendant::td)]');

                var divs = filterXpathResults(divs_xpath, wHeight, wWidth);
                var tds_xpath = getElementsByXpath('//td[not(descendant::div) and not(descendant::td)]');
                var tds = filterXpathResults(tds_xpath, wHeight, wWidth);
                var iframe_elems = document.getElementsByTagName('iframe');
                var iframes = filterElementArrays(iframe_elems, wHeight, wWidth);
                var a_elems = document.getElementsByTagName('a');
                var as = filterElementArrays(a_elems, wHeight, wWidth);
                element_data = element_data.concat(divs, tds);
                var img_elems = document.getElementsByTagName('img');
                var imgs = filterElementArrays(img_elems, wHeight, wWidth);
                var prefs = imgs.concat(as, iframes)
                return [element_data, prefs];
            }
            return getElementData()})

           var elem_coords =await filter_elements(elems, imgs,width,height)

          var url_first_tab= page.url()

           visited_URLs.add(url_first_tab)




          var select_elements=await page.evaluate(function(keywords){

            var matchingElementList=[]
                        // Similar to filterElementArrays but takes xpathResult object as
                        function elementDimensions(element, wHeight, wWidth) {
                          var boundRect = element.getBoundingClientRect();
                          var midy = boundRect.top + (boundRect.height / 2.0);
                          var midx = boundRect.left + (boundRect.width / 2.0);
                          if (boundRect.height != 0 && boundRect.width != 0 &&
                          midy < wHeight && midx < wWidth && midy > 0 && midx > 0)
                          return [midx, midy, boundRect.height, boundRect.width];
                      else
                      return [];
                      }
                     // one of the arguments
                     function filterXpathResults(xpathResults, wHeight, wWidth) {
                         var elem_sizes = [];
                         var element = xpathResults

                         var elem = elementDimensions(element, wHeight, wWidth);
                         if (elem.length > 0)
                             elem_sizes.push(elem);


                         return elem_sizes;
                        }

                        var xpath = ""

                        // var matchingElement =[]
                        var wHeight = window.innerHeight;
                        var wWidth = window.innerWidth;

                      for (const i in keywords) {
                        // matchingElement =[]
                        // xpath = "//a[contains(text(),'Detecting Chrome Headless')]";
                        xpath = "//a[contains(text(),'"+keywords[i]+"')]";
                        // xpath = "//a[contains(text(),'Toy')]";
                        var matchingElement =document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                        if(matchingElement==null){

                          continue
                        }else if(matchingElement  === undefined){
                          continue
                        }


                        matchingElement = filterXpathResults(matchingElement, wHeight, wWidth)

                        if(matchingElement[0]==null){
                          continue
                        }else if(typeof matchingElement[0] == 'undefined'){
                          continue
                        }
                        matchingElementList.push([matchingElement[0][0],matchingElement[0][1]])

                      }


                return matchingElementList
          },config.keywords)

          config.log.info("Elements coordinates that are found by searching specified keywords in landing page are:"+select_elements)




          // return
          if(select_elements.length!=0){

            elem_coords.splice(-1, select_elements.length);

            for(const i in select_elements){
              elem_coords.push(select_elements[i])
            }


          }
          var tabCount=(await browser.pages()).length



         var totaltabcount=0
         var totaltabcount_sess=0
         var differentDomainCount=0



          for (const i in elem_coords){




          url_next=page.url()

          if(url_next!=url_first_tab)
          {
            config.log.info("Landing url has changed, revisiting...")
            await page.goto(url_first_tab , { waitUntil: 'load'});
            await waitTillHTMLRendered(page)

          }
          config.log.info('\n\n')
          config.log.info(i+'. CLICK IS STARTING NOW')

          if (is_mobile){
                await page.touchscreen.tap(elem_coords[i][0], elem_coords[i][1])
            }
            else{
             await page.mouse.move(elem_coords[i][0], elem_coords[i][1])
             await page.waitForTimeout(500)
             await page.mouse.down()
            //  {button : "middle"}
             await page.waitForTimeout(150)
             await page.mouse.up()
            }
          //burasi
          await page.waitForTimeout(500)

          var url_next= page.url()



          if(url_next!=url_first_tab){

              config.log.info("new page opened in the same tab.the url is:",url_next)
              config.log.info("the domain is: ",utils.canonical_url(url_next))

              if(utils.canonical_url(url_first_tab)!=utils.canonical_url(url_next)){
                config.log.info("the domain has changed in the landing page")
                differentDomainCount=differentDomainCount+1
                config.log.info("different domains visited until now:"+differentDomainCount)

              }

            }
          else{
            config.log.info("clicked. But page has not changed. in landing page")

          }

          var tabCountClicked=(await browser.pages()).length
          totaltabcount=(tabCountClicked-1)
          totaltabcount_sess=totaltabcount+totaltabcount_sess

          config.log.info("tab count opened after "+i+". click:"+totaltabcount)
          config.log.info("NEW TAB count until  "+i+". click:"+totaltabcount_sess)
          while (tabCountClicked != tabCount){


              var page_next =(await browser.pages())[tabCountClicked-1]
              if(page_next.isClosed()){
                tabCountClicked=tabCountClicked-1
                continue
              }

              url_next= page_next.url()
              if (url_next=="about:blank" || url_next==""){
                  config.log.info("empty tab..skipping,the url is:"+url_next)
                  tabCountClicked=tabCountClicked-1
                  await page_next.close()
                  continue
                }
                if (!utils.isValidHttpUrl(url_next)){
                  config.log.info("INVALID URL CLOSING, URL IS:"+url_next)
                  tabCountClicked=tabCountClicked-1
                  await page_next.close()
                  continue

                }

                config.log.info("The URL in the new tab is:"+url_next)
                config.log.info("the domain is: ",utils.canonical_url(url_next))


                if(utils.canonical_url(url_first_tab)!=utils.canonical_url(url_next)){
                  config.log.info("the domain is different in the new tab")
                  differentDomainCount=differentDomainCount+1
                  config.log.info("different domains visited until now:"+differentDomainCount)

                }




                if(await page_next.isClosed()==true){

                  tabCountClicked=tabCountClicked-1



                 }else{

                  await page_next.close()
                  tabCountClicked=tabCountClicked-1
                 }

              }


              config.log.info(i+'. CLICK IS ENDED NOW\n\n')


          }




       }


       catch(err){

           console.log(err)
           config.log.info('visit ended')
           config.log.info("Browser is closed")

           config.log.info("End time:"+new Date(Date.now()).toLocaleString())
           clearInterval(trigger);
           await process_ended(config.id,browser)

           return
       }

       config.log.info("SESSION ENDED, TOTAL AMOUNT OF DIFFERENT DOMAINS VISITED:"+differentDomainCount)
       config.log.info("SESSION ENDED, TOTAL AMOUNT OF NEW TABS OPENED:"+totaltabcount_sess)

       console.log(new Date(Date.now()).toLocaleString())
       config.log.info("Browser is closed")

       clearInterval(trigger);
       await process_ended(config.id,browser)

       return {'tabsCount':totaltabcount_sess,'domainsCount':differentDomainCount}


     }
     catch(e){
      console.log(e)
      config.log.error("an error happened during crawling:"+e)
      await process_ended(id,browser)
      return {'tabsCount':totaltabcount_sess,'domainsCount':differentDomainCount}
     }
   })
}


async function process_ended(id,browser){


  try{
    const page_download = await browser.newPage(); //open new tab
    await page_download.goto("chrome://downloads/ ", { waitUntil: 'load'});
    await page_download.waitForTimeout(2000)
    await page_download.screenshot({ path: config.DOWNLOADS_DIR+config.id+"_"+utils.toISOLocal(new Date()), type: 'png' ,fullPage: true});
    await page_download.waitForTimeout(2000)
    await page_download.close()

  }catch(e){
    config.log.error("Error during download page")
    if(!(await page_download.isClosed())){
      await page_download.close()
    }

  }

  config.log.info('crawl process ended ::'+id)
  config.logger_rr.end()
  config.logger_chrm.end()
  config.logger_coor.end()
  config.log.info("browser closed")
  await browser.close()
  process.exit();
  return
}

async function crawl_url(){
   try{
     config.log.info('crawling started :: ' +config.id)
     res = await load_page()
     return res
   }

   catch(error){
    config.log.error("Error in craw_url function:"+error)
    process.exit()
   }


}

crawl_url();












