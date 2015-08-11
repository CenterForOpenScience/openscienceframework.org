'use strict';

var $ = require('jquery');
require('./github-node-cfg.js');
var AddonHelper = require('js/addonHelper');

$(window.contextVars.githubSettingsSelector).on('submit',
    function(){
        AddonHelper.onSubmitSettings({
            successUpdateMsg: 'Github add-on successfully updated.',
            failUpdateMsg: 'Github add-on doesn\'t updated successfully. Please try again or check your internet connection.'
        });
    });
