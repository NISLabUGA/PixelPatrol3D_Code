'use strict';

const csv = require('csv-parser')
const fs = require('fs')
var tldextract = require('tld-extract');

module.exports = {



 DefaultDict :class{
    constructor(defaultInit) {
        return new Proxy({}, {
         get: (target, name) => name in target ?
              target[name] :
              (target[name] = typeof defaultInit === 'function' ?
                new defaultInit().valueOf() :
                defaultInit)
          })
        }
},
//Round x to nearest multiple of 'base'
any_round:function(x, base=50){
    return base * Math.floor(x / base)

},

is_reg_dom_different:function(landing, visited){
  var landing_domain=tldextract(landing).domain
  var visited_domain=tldextract(visited).domain

  if(landing_domain!=visited_domain)
  {
    return true
  }else{
    return false
  }




},


//python sorted function ported
sorted:function(items, kwargs={}) {
    if(items.length==0){
       return items
    }

    const key = kwargs.key === undefined ? x => x : kwargs.key;
    const reverse = kwargs.reverse === undefined ? false : kwargs.reverse;
    const sortKeys = items.map((item, pos) => [key(item), pos]);
    const comparator =
        Array.isArray(sortKeys[0][0])
        ? ((left, right) => {
            for (var n = 0; n < Math.min(left.length, right.length); n++) {
                const vLeft = left[n], vRight = right[n];
                const order = vLeft == vRight ? 0 : (vLeft > vRight ? 1 : -1);
                if (order != 0) return order;
            }
            return left.length - right.length;
        })
        : ((left, right) => {
            const vLeft = left[0], vRight = right[0];
            const order = vLeft == vRight ? 0 : (vLeft > vRight ? 1 : -1);
            return order;
        });
    sortKeys.sort(comparator);
    if (reverse) sortKeys.reverse();
    return sortKeys.map((order) => items[order[1]]);
},



canonical_url:function(u){
  var url = require('url');
  // var url_normalized=normalizeUrl(u);
  var url_normalized=url.parse(u).hostname
  return url_normalized
},

/**
 * Returns a random number between min (inclusive) and max (exclusive)
 */
 between:function (min, max) {
    return Math.floor(
      Math.random() * (max - min) + min
    )
  },


  DefaultDict:class {
    constructor(defaultInit) {
      return new Proxy({}, {
        get: (target, name) => name in target ?
          target[name] :
          (target[name] = typeof defaultInit === 'function' ?
            new defaultInit().valueOf() :
            defaultInit)
      })
    }
  },

 hasVisited:function(visited_URLs,visited_URL){
  for (let item of visited_URLs.keys()) {
    if(item.toString() == visited_URL.toString())
       return true
    //true on match.
  }

  return false
 },

 shuffleArray:function (array) {
  for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
  }
  return array
},

getRandViewports:function (window_size) {
  var res1=[];
  var res2=[];
  var res3=[];
  var lngth;
  var array_multiplied;
  var width;
  var height;

  for (const q in window_size){
      for (const k in window_size[q]){
          width=window_size[q][k][0]
          height=window_size[q][k][1]
          lngth= window_size[q][k][2]
          array_multiplied=Array(lngth).fill([width,height])

          if (q==0)
              res1.push.apply(res1,array_multiplied)
          else if(q==1)
              res2.push.apply(res2,array_multiplied)
          else
              res3.push.apply(res3,array_multiplied)

        // console.log(width+'x'+height)
      }
  }

   res1=this.shuffleArray(res1)
   res2=this.shuffleArray(res2)
   res3=this.shuffleArray(res3)

  const randomViewport1 = res1[Math.floor(Math.random() * res1.length)];
  const randomViewport2 = res2[Math.floor(Math.random() * res2.length)];
  const randomViewport3 = res3[Math.floor(Math.random() * res3.length)];

  const random_viewports=[randomViewport1,randomViewport2,randomViewport3];

  return random_viewports

},

isValidHttpUrl:function (string) {
  let url;

  try {
    url = new URL(string);
  } catch (_) {
    return false;
  }

  return url.protocol === "http:" || url.protocol === "https:";
},



// toISOLocal:function (d) {
//   var z  = n =>  ('0' + n).slice(-2);
//   var zz = n => ('00' + n).slice(-3);
//   var off = d.getTimezoneOffset();
//   var sign = off > 0? '-' : '+';
//   off = Math.abs(off);

//   // return d.getFullYear() + '-'
//   //        + z(d.getMonth()+1) + '-' +
//   //        z(d.getDate()) + 'T' +
//   //        z(d.getHours()) + ':'  +
//   //        z(d.getMinutes()) + ':' +
//   //        z(d.getSeconds()) + '.' +
//   //        zz(d.getMilliseconds()) +
//   //        sign + z(off/60|0) + ':' + z(off%60);

//   return z(d.getMonth()+1) + '-' +
//   z(d.getDate()) + 'T' +
//   z(d.getHours()) + ':'  +
//   z(d.getMinutes()) + ':' +
//   z(d.getSeconds()) + '.' +
//   zz(d.getMilliseconds()) +
//   sign + z(off/60|0) + ':' + z(off%60);
// },



toISOLocal:function(d){
  var zz = n => ('00' + n).slice(-3)

  var hour   = d.getHours();
  var minute = d.getMinutes();
  var second = d.getSeconds();
  var ap = "AM";
  if (hour   > 11) { ap = "PM";             }
  if (hour   > 12) { hour = hour - 12;      }
  if (hour   == 0) { hour = 12;             }
  if (hour   < 10) { hour   = "0" + hour;   }
  if (minute < 10) { minute = "0" + minute; }
  if (second < 10) { second = "0" + second; }
  var ms=zz(d.getMilliseconds())
  var timeString = hour + ':' + minute + ':' + second+':' +ms+ " " + ap;
  return timeString;
},


getData:async function (file, type) {
  let data = [];
  return new Promise((resolve, reject) => {

      fs.createReadStream(file)
          .on('error', error => {
              reject(error);
          })
          .pipe(csv({headers: ['Ranking', 'Website'], separator: ',',}))
          .on('data', (row) => {
              data.push(row);

          })
          .on('end', () => {
              resolve(data);
          });

  });
},


CSVGetData:async function (){
  try {
    var results=[]

    results =await module.exports.getData("tranco.csv", {})

    return results


} catch (error) {
    console.error("testGetData: An error occurred: ", error.message);
}

},

filterCSVResults:function (website,data) {
  var filteredData =data.filter(d => d.Website == website);
  return filteredData
},

calculateRunningTime:function(startTime,endTime){
  var timeDiff = endTime - startTime;
  // strip the ms
   timeDiff /= 1000;
   // get seconds (Original had 'round' which incorrectly counts 0:28, 0:29, 1:30 ... 1:59, 1:0)
   var seconds = Math.round(timeDiff % 60);
   // remove seconds from the date
   timeDiff = Math.floor(timeDiff / 60);
   // get minutes
   var minutes = Math.round(timeDiff % 60);
   // remove minutes from the date
   timeDiff = Math.floor(timeDiff / 60);
   // get hours
   var hours = Math.round(timeDiff % 24);
   // remove hours from the date
   timeDiff = Math.floor(timeDiff / 24);
   // the rest of timeDiff is number of days
   var days = timeDiff ;
   return[hours,minutes,seconds]
},

url_hasher:function(url,current_time){
  // const current_time=new Date().getTime()
  let result_string = url.concat(current_time);
  var crypto = require('crypto');
  var result=crypto.createHash('md5').update(result_string).digest("hex");
  return result

},


json_log_append:async function (filename , data_after,data,previous_url,previous_url_id,tab_location,tab_id,visit_id) {

  if (fs.existsSync(filename)) {
      var read_data = await readFile(filename)
      if (read_data==false && read_data!="") {
          return 'not able to read json file'
      }
      else {

          if(data_after==null){

            if(data.element_clicked!=null){
               var el_obj={'description':data.element_clicked.description,
                           'reason_to_click':data.element_clicked.reason_to_click,
                           'bounding_box':data.element_clicked.bounding_box,
                           'click_coordinates':data.element_clicked.click_coordinates,
                           'screenshot_before_name':data.screenshot_name,
                           'screenshot_after_name':null
                          }
            }else{
              var el_obj=null
            }
            var json_data={'time':data.time,
                           'url':data.url,
                           'url_id':data.url_id,
                           'url_domain_id':data.url_domain_id,
                           'visit_id':visit_id,
                           'screenshot_name':data.screenshot_name,
                           'screenshot_size':data.ss_size,
                           'previous_url':previous_url,
                           'previous_url_id':previous_url_id,
                           'tab_location':tab_location,
                           'tab_id':tab_id,
                           'element_clicked':el_obj


                            }


          }
          else{

            var el_obj={  'description':data.element_clicked.description,
                          'reason_to_click':data.element_clicked.reason_to_click,
                          'bounding_box':data.element_clicked.bounding_box,
                          'click_coordinates':data.element_clicked.click_coordinates,
                          'screenshot_before_name':data.screenshot_name,
                          'screenshot_after_name':data_after.screenshot_name}


            var json_data={'time':data.time,
                          'url':data.url,
                          'url_id':data.url_id,
                          'url_domain_id':data.url_domain_id,
                          'visit_id':visit_id,
                          'screenshot_name':data.screenshot_name,
                          'screenshot_size':data.ss_size,
                          'previous_url':previous_url,
                          'previous_url_id':previous_url_id,
                          'tab_location':tab_location,
                          'tab_id':tab_id,
                          'element_clicked':el_obj
                           }

          }

          if(read_data!=""){
            read_data.push(json_data)
          }else{
           read_data=[json_data]
          }

          // read_data.push(data)
          dataWrittenStatus = await writeFile(filename, read_data)
          if( dataWrittenStatus == true) {
            return 'json data added successfully'
          }
         else{
            return 'json data adding failed'
          }
      }
  }
    else{
        var dataWrittenStatus = await writeFile(filename, [json_data])
        if (dataWrittenStatus == true ){
            return 'data added successfully'
        }
        else{
           return 'data adding failed'
         }
    }


    async function readFile  (filePath) {
      try {
        const data = await fs.promises.readFile(filePath, 'utf8')
        return JSON.parse(data)
      }
     catch(err) {
         return false;
      }
    }

    async function writeFile  (filename ,writedata) {
      try {
          await fs.promises.writeFile(filename, JSON.stringify(writedata,null, 4), 'utf8');
          return true
      }
      catch(err) {
          return false
      }
    }
 },


 json_url_append:async function (filename , landing,visited) {

  var different=(function(){
    var landing_domain=tldextract(landing).domain
    var visited_domain=tldextract(visited).domain

    if(landing_domain!=visited_domain)
    {
      return true
    }else{
      return false
    }




  })(landing, visited)

  if (fs.existsSync(filename)) {
      var read_data = await readFile(filename)
      if (read_data==false && read_data!="") {
          return 'not able to read json file'
      }
      else {

        var json_data={'url':visited,

        'is_different_sld':different,
       }


          if(read_data!=""){
            read_data.push(json_data)
          }else{
           read_data=[json_data]
          }

          // read_data.push(data)
          dataWrittenStatus = await writeFile(filename, read_data)
          if( dataWrittenStatus == true) {
            return 'json data added successfully'
          }
         else{
            return 'json data adding failed'
          }
      }
  }
    else{
        var dataWrittenStatus = await writeFile(filename, [json_data])
        if (dataWrittenStatus == true ){
            return 'data added successfully'
        }
        else{
           return 'data adding failed'
         }
    }


    async function readFile  (filePath) {
      try {
        const data = await fs.promises.readFile(filePath, 'utf8')
        return JSON.parse(data)
      }
     catch(err) {
         return false;
      }
    }

    async function writeFile  (filename ,writedata) {
      try {
          await fs.promises.writeFile(filename, JSON.stringify(writedata,null, 4), 'utf8');
          return true
      }
      catch(err) {
          return false
      }
    }
 },


single_url_hasher:function (url_i){
  var crypto = require('crypto');
  var result=crypto.createHash('md5').update(url_i.split('?')[0]).digest("hex");
  return result

},
unixtoDATE:function(unix_timestamp){

  // Create a new JavaScript Date object based on the timestamp
  // multiplied by 1000 so that the argument is in milliseconds, not seconds.
  var date = new Date(unix_timestamp * 1000);
  // Hours part from the timestamp
  var hours = date.getHours();
  // Minutes part from the timestamp
  var minutes = "0" + date.getMinutes();
  // Seconds part from the timestamp
  var seconds = "0" + date.getSeconds();

  // Will display time in 10:30:23 format
  var formattedTime = hours + ':' + minutes.substr(-2) + ':' + seconds.substr(-2);
  return formattedTime;
},
calculate:function(rank) {
  var config=require('./config')

  console.log("current rank:",rank)
  if(config.crawler_mode=="SE"){
      if(rank<config.tranco_threshold){
         console.log("Rank is smaller than the threshold")
         return true

      }else{
          console.log("Rank is bigger than the threshold")
          return false

      }

  }else{
      if(rank>=config.tranco_threshold){
          console.log("Rank is bigger equal than threshold")
          return true
       }else{
          console.log("Rank is smaller equal than threshold")
           return false

       }

  }
}


// json_log_append:function(json_file,data){

//   fs.readFile("./customer.json", "utf8", (err, jsonString) => {
//   if (err) {
//     console.log("File read failed:", err);
//     return;
//   }
//   console.log("File data:", jsonString);
// });

// }

}





// var currentSearchResult = 'example'

// fs.readFile('results.json', function (err, data) {
//     var json = JSON.parse(data)
//     json.push('search result: ' + currentSearchResult)

//     fs.writeFile("results.json", JSON.stringify(json))

//     fs.writeFile("results.json", JSON.stringify(json), function(err){
//       if (err)  console.log('cannot write a the json file');;
//       console.log('successful json write');
//     });
// })