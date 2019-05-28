var jQuery = window.jQuery = window.$ = require('jquery');
/* vendor scripts */
require('./libs/bootstrap');
var LazyLoad = require('./libs/lazyload');

$(function(){
  var csses = ["https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css", "https://fonts.googleapis.com/css?family=Open+Sans"];
  for(var i = 0; i < csses.length; i++) {var cssName = csses[i];var cssLink = document.createElement('link');cssLink.rel = 'stylesheet';cssLink.href = cssName;cssLink.type = 'text/css';var cssElement = document.getElementsByTagName('link')[0];cssElement.parentNode.insertBefore(cssLink, cssElement);}

  new LazyLoad();

  var setPasswordField = function() {
    if($('#id_instance_type_0').is(':checked')) {
      $('#id_cloud_password').closest('.form-group').show();
    } else {
      $('#id_cloud_password').closest('.form-group').hide();
    }
  };

  $('[name=instance_type]').on('change', function(){
    setPasswordField();
  });

  setPasswordField();
});


