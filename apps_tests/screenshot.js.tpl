var casper = require('casper').create();

casper.start('YNH_PORTAL_URL', function() {
  this.fill('form[name="input"]', 
    { user : "YNH_USER", password : "YNH_PASSWORD" },
    true);
});

casper.thenOpen('YNH_APP_URL', function() {
    this.echo(this.getTitle());
    this.viewport(1280, 1024).then( function() {
      this.capture( 'YNH_SCREENSHOT_DIR/YNH_SCREENSHOT_FILENAME' );
    });
});

casper.run();
