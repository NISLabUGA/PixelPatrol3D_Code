const fs = require('fs')
var utils = require('./utils');
var Proxy = require('http-mitm-proxy');
var proxy = Proxy();
const starting_date = utils.toISOLocal(new Date())
// var proxyPort=8080
proxy.use(Proxy.wildcard);






// var forge = require('node-forge');
// forge.options.usePureJavaScript = true;

// var pki = forge.pki;
// var keys = pki.rsa.generateKeyPair(2048);
// var cert = pki.createCertificate();

// cert.publicKey = keys.publicKey;
// cert.serialNumber = '01';
// cert.validity.notBefore = new Date();
// cert.validity.notAfter = new Date();
// cert.validity.notAfter.setFullYear(cert.validity.notBefore.getFullYear()+1);

// var attrs = [
//      {name:'commonName',value:'example.org'}
//     ,{name:'countryName',value:'US'}
//     ,{shortName:'ST',value:'Virginia'}
//     ,{name:'localityName',value:'Blacksburg'}
//     ,{name:'organizationName',value:'Test'}
//     ,{shortName:'OU',value:'Test'}
// ];
// cert.setSubject(attrs);
// cert.setIssuer(attrs);
// cert.sign(keys.privateKey);

// var pem_pkey = pki.publicKeyToPem(keys.publicKey);
// var pem_cert = pki.certificateToPem(cert);





proxy.listen({port: 8083,forceSNI: true});











if (process.argv[2]) {
    var site_id =process.argv[2];
  }


const RES_REQ_PAIRS_DIR ="req_res_pairs/site_id:"+site_id+"_"+starting_date+"/"

if (!fs.existsSync(RES_REQ_PAIRS_DIR)){
  fs.mkdirSync(RES_REQ_PAIRS_DIR, { recursive: true });
}

var req_res_file=RES_REQ_PAIRS_DIR+starting_date+"_"+utils.toISOLocal(new Date())+'.txt'
var logger_rr = fs.createWriteStream(req_res_file, {
  flags: 'a' // 'a' means appending (old data will be preserved)
})



proxy.onError(function(ctx, err) {
  // console.error('proxy error:', err);
  var err_string='proxy error:', err
  logger_rr.write(err_string)
});
// req.connection.localAddress





proxy.onRequest(function(ctx, callback) {
  // console.log('>> '+ctx.clientToProxyRequest.method+" "+ctx.clientToProxyRequest.headers.host+ctx.clientToProxyRequest.url+ctx.clientToProxyRequest.ip +'\n');
  // var getClientAddress = (ctx.clientToProxyRequest.headers['x-forwarded-for'] || '').split(',')[0] || ctx.clientToProxyRequest.connection.remoteAddress;
  // var getClientAddress =ctx.clientToProxyRequest.ip.split(":").pop()
  // console.log('>>> '+ctx.proxyToServerRequest+'\n')
  // console.log('>>> '+ctx.clientToProxyRequest.socket.localAddress+'\n')
  // var requestt= '>> '+ctx.clientToProxyRequest.method+" "+ctx.clientToProxyRequest.headers.host+ctx.clientToProxyRequest.url+'\n'
  // console.log(requestt)
  // logger_rr.write(requestt)
   proxy.onResponse(function(tx, callback) {
    var requestt= '>> '+tx.clientToProxyRequest.method+" "+tx.clientToProxyRequest.headers.host+tx.clientToProxyRequest.url+"  RemoteIP:"+tx.proxyToServerRequest.socket.remoteAddress+'\n'
    logger_rr.write(requestt)
    return callback();

  });
  return callback();
});

proxy.onResponse(function(ctx, callback) {

  // var getClientAddress = (ctx.clientToProxyRequest.headers['x-forwarded-for'] || '').split(',')[0] || ctx.clientToProxyRequest.connection.remoteAddress;
  // console.log('<< '+ctx.proxyToClientResponse.statusCode+" "+ctx.proxyToClientResponse.req.headers.host+ctx.proxyToClientResponse.req.url+ctx.proxyToClientResponse.req.url+"   "+ctx.serverToProxyResponse.socket.remoteAddress+'\n');
  var content_type=ctx.serverToProxyResponse.headers['content-type']
  var responses='<< '+ctx.proxyToClientResponse.statusCode+" "+ctx.proxyToClientResponse.req.headers.host+ctx.proxyToClientResponse.req.url+"  RemoteIP:"+ctx.serverToProxyResponse.socket.remoteAddress+'\n'
  // if(content_type=="application/octet-stream"|| content_type=="binary/octet-stream"){
//     if(content_type=="application/octet-stream"){
//       config.log_download.info(responses)
//   }
  // console.log(responses)
  logger_rr.write(responses)
  return callback();
});
























// proxy.onRequest(function(ctx, callback) {



//   if (ctx.clientToProxyRequest.headers.host == 'www.google.com'
//     && ctx.clientToProxyRequest.url.indexOf('/search') == 0) {
//     ctx.use(Proxy.gunzip);

//     ctx.onResponseData(function(ctx, chunk, callback) {
//       chunk = new Buffer(chunk.toString().replace(/<h3.*?<\/h3>/g, '<h3>Pwned!</h3>'));
//       return callback(null, chunk);
//     });
//   }



//   return callback();
// });


// // Setup blocking of requests in proxy
// const proxyPort = 8000;
// const proxy = setupProxy(proxyPort);
// proxy.onRequest((context, callback) => {
//    if (blockRequests) {
//      const request = context.clientToProxyRequest;
//      // Log out blocked requests
//      console.log('Blocked request:', request.headers.host, request.url);

//      // Close the connection with custom content
//      context.proxyToClientResponse.end('Blocked');
//      return;
//    }
//    return callback();
// });




// // process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0"

// proxy.onCertificateRequired = function(hostname, callback) { return callback(null, { keyFile: path.resolve('key.pem'), certFile: path.resolve('cert.pem'), hosts: ["*"] }); };



// proxy.onCertificateRequired = function(hostname, callback) {
//   return callback(null, {
//     keyFile: path.resolve('/ca/certs/', hostname + '.key'),
//     certFile: path.resolve('/ca/certs/', hostname + '.crt')
//   });
// };


// proxy.onCertificateMissing = function(ctx, files, callback) {
//   return callback(null, {
//     keyFileData: keyFileData,
//     certFileData: certFileData,
//     hosts: ["*.mydomain.com"]
//   });
// };
