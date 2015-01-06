var casper = require('casper').create({
    verbose: true,
    userAgent: 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36',
    logLevel: "debug",
    viewportSize : { width: 1280, height: 1024}
});

casper.start();

/* 
 * By sending the correct HTTP Basic Auth header, the SSO allows us to access private apps.
 * 
 * casper.setHttpAuth, or setting the user:password pair in the url
 * is not sufficient as casper only uses it for the actual url to load,
 * and not for all additionnal resources on that page
 */
casper.page.customHeaders = {
    'Authorization' : 'Basic YNH_BASIC_AUTH',
};

casper.open('YNH_APP_URL');

casper.then( function() {
    /* Wait for some time, for resources to be loaded correctly */
    casper.wait(3000, function() {
      this.echo(casper.getTitle());
      this.capture('YNH_SCREENSHOT_DIR/YNH_SCREENSHOT_FILENAME');
    });
});

casper.run();
