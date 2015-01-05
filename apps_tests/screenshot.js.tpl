var casper = require('casper').create();

casper.setHttpAuth("YNH_USER", "YNH_PASSWORD");

casper.thenOpen('YNH_APP_URL', function() {
    this.echo(this.getTitle());
    this.viewport(1280, 1024).then( function() {
      this.capture( 'YNH_SCREENSHOT_DIR/YNH_SCREENSHOT_FILENAME' );
    });
});

casper.run();
