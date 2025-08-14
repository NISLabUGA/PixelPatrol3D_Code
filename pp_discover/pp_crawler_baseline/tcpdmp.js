var utils = require('./utils');
const fs = require('fs')

const starting_date = utils.toISOLocal(new Date())


// concurrently --kill-others "node capture_screenshots.js https://123moviesprime.com/123movies/ 20" "sudo node tcpdmp.js 20"


async function tcpdump(){
    const SimpleNodeLogger = require('simple-node-logger');
    if (process.argv[2]) {
        var site_id =process.argv[2];
      }

    const TCPDUMP_DIR ="tcpdump/site_id:"+site_id+"_"+starting_date+"/"



    if (!fs.existsSync(TCPDUMP_DIR)){
      fs.mkdirSync(TCPDUMP_DIR, { recursive: true });

    }


    const opts = {
        logFilePath:TCPDUMP_DIR+starting_date+"_"+utils.toISOLocal(new Date())+'.log',
        timestampFormat:'YYYY-MM-DD HH:mm:ss.SSS'
      };

    const log = SimpleNodeLogger.createSimpleLogger(opts);

    // tcpdump -i en0 -w /var/tmp/trace -W 48 -G 1800 -C 100 -K -n
    // This will rotate files (of names trace1, trace2, ...) cyclically, with period 48, either every 1800 seconds (=30 minutes) or every 100 MB, whichever comes first.
    const { spawn } = require('child_process');
    var rand_number=utils.between(0, 10000)
    // tcpdump -G 180 -Z root -w filename.pcap udp port 53
    // to analyze tcpdump -n -t -r /tmp/dns.pcap port 53
    const child = spawn('tcpdump', ['-G','180','-Z','root','-w',TCPDUMP_DIR+'site_id:'+site_id+'_time:%m-%dT%I:%M:%S'+rand_number+'.pcap','udp','port','53'])

    child.on('error', function(err) {
      log.error('error in tcpdump child process : ' + err);
    });


    var the_interval = 3600 *1000 //in milliseconds


    var wait_interval = 5000
    var count=0

    // checks if the timeout has exceeded every few seconds
    var trigger = await setInterval(async function()
    {
        // close the browser if the run exfceeds timeout interval
        if (count >= the_interval )
        {

        child.kill('SIGINT')
        log.info('TCPDUMP ENDED,TIME'+new Date(Date.now()).toLocaleString())
        clearInterval(trigger);
        return
        }
        count = count+wait_interval
    }, wait_interval);

}




tcpdump()


















// FIRST VERSION BELOW


//  // tcpdump -i en0 -w /var/tmp/trace -W 48 -G 1800 -C 100 -K -n
// // This will rotate files (of names trace1, trace2, ...) cyclically, with period 48, either every 1800 seconds (=30 minutes) or every 100 MB, whichever comes first.
// const { spawn } = require('child_process');
// var rand_number=utils.between(0, 10000)
// // tcpdump -G 180 -Z root -w filename.pcap udp port 53
// // to analyze tcpdump -n -t -r /tmp/dns.pcap port 53
// const child = spawn('tcpdump', ['-G','180','-Z','root','-w',config.TCPDUMP_DIR+'site_id'+site_id+'_time:%m-%dT%I:%M:%S'+rand_number+'.pcap','udp','port','53'])
// child.on('error', function(err) {
//   config.log.error('error in tcpdump child process : ' + err);
// });
