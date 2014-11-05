/**
 * Module that controls the Dropbox node settings. Includes Knockout view-model
 * for syncing data, and HGrid-folderpicker for selecting a folder.
 */


;(function (global, factory) {
    if (typeof define === 'function' && define.amd) {
        define(['knockout', 'jquery', 'js/folderPicker',
                'zeroclipboard', 'osfutils', 'knockoutpunches'], factory);
    } else if (typeof $script === 'function') {
        $script.ready(['folderPicker', 'zeroclipboard'], function() {
            global.FigshareNodeConfig  = factory(ko, jQuery, FolderPicker, ZeroClipboard);
            $script.done('figshareNodeConfig');
        });
    } else {
        global.FigshareNodeConfig  = factory(ko, jQuery, FolderPicker, ZeroClipboard);
    }
}(this, function(ko, $, FolderPicker, ZeroClipboard) {
    'use strict';
    ko.punches.attributeInterpolationMarkup.enable();
    /**
     * Knockout view model for the Figshare node settings widget.
     */
    var ViewModel = function(url, selector, folderPicker) {
        var self = this;
        // Auth information
        self.nodeHasAuth = ko.observable(false);
        self.userHasAuth = ko.observable(false);
	    self.userIsOwner = ko.observable(false);
        // Whether a user's oauth credentials are still valid
        self.validCredentials = ko.observable(true);
        // Currently linked folder, an Object of the form {name: ..., path: ...}
        self.linked = ko.observable({});
        self.ownerName = ko.observable('');
        self.urls = ko.observable({});
        // Flashed messages
        self.message = ko.observable('');
        self.messageClass = ko.observable('text-info');
        // Display names
        self.PICKER = 'picker';
        self.SHARE = 'share';
        // Current folder display
        self.currentDisplay = ko.observable(null);
        // CSS selector for the folder picker div
        self.folderPicker = folderPicker;
        // Currently selected folder, an Object of the form {name: ..., path: ...}
        self.selected = ko.observable(null);
        // Emails of contributors, can only be populated by activating the share dialog
        self.loading = ko.observable(false);
        // Whether the initial data has been fetched form the server. Used for
        // error handling.
        self.loadedSettings = ko.observable(false);
        // Whether the contributor emails have been loaded from the server
        self.disableShare = ko.computed(function() {
            return !self.urls().share;
        });
        /**
         * Update the view model from data returned from the server.
         */
        self.updateFromData = function(data) {
            self.ownerName(data.ownerName);
            self.nodeHasAuth(data.nodeHasAuth);
            self.userHasAuth(data.userHasAuth);
	        self.userIsOwner(data.userIsOwner);
            self.validCredentials(data.validCredentials);
	        self.linked(data.linked || {});
            self.urls(data.urls);
        };

        self.fetchFromServer = function() {
            $.ajax({
                url: url, type: 'GET', dataType: 'json',
                success: function(response) {
                    self.updateFromData(response.result);
                    self.loadedSettings(true);
                    if (!self.validCredentials()){
                        if (self.userIsOwner()) {
                            self.changeMessage('Could not retrieve Figshare settings at ' +
                            'this time. The Figshare addon credentials may no longer be valid.' +
                            ' Try deauthorizing and reauthorizing Figshare on your <a href="' +
                             self.urls().settings + '">account settings page</a>.',
                            'text-warning')
                        } else {
                            self.changeMessage('Could not retrieve Figshare settings at ' +
                            'this time. The Figshare addon credentials may no longer be valid.' +
                            ' Contact ' + self.ownerName() + ' to verify.',
                            'text-warning')
                        }
                 }
                },
                error: function(xhr, textStatus, error) {
                    self.changeMessage('Could not retrieve Figshare settings at ' +
                        'this time. Please refresh ' +
                        'the page. If the problem persists, email ' +
                        '<a href="mailto:support@osf.io">support@osf.io</a>.',
                        'text-warning');
                    Raven.captureMessage('Could not GET Figshare settings', {
                        url: url,
                        textStatus: textStatus,
                        error: error
                    });
                }
            });
        };

        // Initial fetch from server
        self.fetchFromServer();

        /**
         * Whether or not to show the Import Access Token Button
         */
        self.showImport = ko.computed(function() {
            // Invoke the observables to ensure dependency tracking
            var userHasAuth = self.userHasAuth();
            var nodeHasAuth = self.nodeHasAuth();
            var loaded = self.loadedSettings();
            return userHasAuth && !nodeHasAuth && loaded;
        });

        /** Whether or not to show the full settings pane. */
        self.showSettings = ko.computed(function() {
            return self.nodeHasAuth();
        });

        /** Whether or not to show the Create Access Token button */
        self.showTokenCreateButton = ko.computed(function() {
            // Invoke the observables to ensure dependency tracking
            var userHasAuth = self.userHasAuth();
            var nodeHasAuth = self.nodeHasAuth();
            var loaded = self.loadedSettings();
            return !userHasAuth && !nodeHasAuth && loaded;
        });

        /** Computed functions for the linked and selected folders' display text.*/

        self.folderName = ko.computed(function() {
            // Invoke the observables to ensure dependency tracking
            var nodeHasAuth = self.nodeHasAuth();
            var linked = self.linked();
            return (nodeHasAuth && linked)? linked.title : '';
        });

        self.selectedFolderName = ko.computed(function() {
            var userIsOwner = self.userIsOwner();
            var selected = self.selected();
            return (userIsOwner && selected) ? selected.title : '';
        });

        self.selectedFolderType = ko.computed(function(){
            var userHasAuth = self.userHasAuth();
                var selected = self.selected();
                return (userHasAuth && selected) ? selected.type : '';
        });

        function onSubmitSuccess(response) {
            self.changeMessage('Successfully linked "' + self.selected().title +
                '". Go to the <a href="' +
                self.urls().files + '">Files page</a> to view your files.',
                'text-success', 5000);
            // Update folder in ViewModel
	        self.linked(response.result.linked);
            self.urls(response.result.urls);
            self.cancelSelection();
        }

        function onSubmitError() {
            self.changeMessage('Could not change settings. Please try again later.', 'text-danger');
        }

        /**
         * Send a PUT request to change the linked Figshare folder.
         */
        self.submitSettings = function() {
            $.osf.putJSON(self.urls().config, ko.toJS(self))
                .done(onSubmitSuccess)
                .fail(onSubmitError);
        };

        /**
         * Must be used to update radio buttons and knockout view model simultaneously
         */
        self.cancelSelection = function() {
            self.selected(null);
            $(selector + ' input[type="radio"]').prop('checked', false);
        };

        /** Change the flashed message. */
        self.changeMessage = function(text, css, timeout) {
            self.message(text);
            var cssClass = css || 'text-info';
            self.messageClass(cssClass);
            if (timeout) {
                // Reset message after timeout period
                setTimeout(function() {
                    self.message('');
                    self.messageClass('text-info');
                }, timeout);
            }
        };

        /**
         * Send DELETE request to deauthorize this node.
         */
        function sendDeauth() {
            return $.ajax({
                url: self.urls().deauthorize,
                type: 'DELETE',
                success: function() {
                    // Update observables
                    self.nodeHasAuth(false);
                    self.cancelSelection();
                    self.currentDisplay(null);
                    self.changeMessage('Deauthorized Figshare.', 'text-warning', 3000);
                },
                error: function() {
                    self.changeMessage('Could not deauthorize because of an error. Please try again later.',
                        'text-danger');
                }
            });
        }

        /** Pop up a confirmation to deauthorize Figshare from this node.
         *  Send DELETE request if confirmed.
         */
        self.deauthorize = function() {
            bootbox.confirm({
                title: 'Deauthorize Figshare?',
                message: 'Are you sure you want to remove this Figshare authorization?',
                callback: function(confirmed) {
                    if (confirmed) {
                        return sendDeauth();
                    }
                }
            });
        };

        // Callback for when PUT request to import user access token
        function onImportSuccess(response) {
            var msg = response.message || 'Successfully imported access token from profile.';
            // Update view model based on response
            self.changeMessage(msg, 'text-success', 3000);
            self.updateFromData(response.result);
            self.activatePicker();
        }

        function onImportError() {
            self.message('Error occurred while importing access token.');
            self.messageClass('text-danger');
        }

        /**
         * Send PUT request to import access token from user profile.
         */
        self.importAuth = function() {
            bootbox.confirm({
                title: 'Import Figshare Access Token?',
                message: 'Are you sure you want to authorize this project with your Figshare access token?',
                callback: function(confirmed) {
                    if (confirmed) {
                        return $.osf.putJSON(self.urls().importAuth, {})
                            .done(onImportSuccess)
                            .fail(onImportError);
                    }
                }
            });
        };

        /** Callback for chooseFolder action.
        *   Just changes the ViewModel's self.selected observable to the selected
        *   folder.
        */
        function onPickFolder(evt, row) {
            evt.preventDefault();
            self.selected({title: row.name, type: row.type, id: row.id})
            return false; // Prevent event propagation
        }

        // Hide +/- icon for root folder
        FolderPicker.Col.Name.showExpander = function(item) {
            return item.path !== '/';
        };

        /**
         * Activates the HGrid folder picker.
         */
        self.activatePicker = function() {
            self.currentDisplay(self.PICKER);
            // Show loading indicator
            self.loading(true);
            $(self.folderPicker).folderpicker({
                onPickFolder: onPickFolder,
                // Fetch Figshare folders with AJAX
                data: self.urls().options, // URL for fetching folders
                // Lazy-load each folder's contents
                // Each row stores its url for fetching the folders it contains
                fetchUrl: function(row) {
                    return row.urls.fetch;
                },
                ajaxOptions: {
                   error: function(xhr, textStatus, error) {
                        self.loading(false);
                        self.changeMessage('Could not connect to Figshare at this time. ' +
                                            'Please try again later.', 'text-warning');
                        Raven.captureMessage('Could not GET Figshare contents', {
                            textStatus: textStatus,
                            error: error
                        });
                    }
                },
                init: function() {
                    // Hide loading indicator
                    self.loading(false);
                }
            });
        };

        /**
         * Toggles the visibility of the folder picker.
         */
        self.togglePicker = function() {
            // Toggle visibility of folder picker
            var shown = self.currentDisplay() === self.PICKER;
            if (!shown) {
                self.currentDisplay(self.PICKER);
                self.activatePicker();
            } else {
                self.currentDisplay(null);
                // Clear selection
                self.cancelSelection();
            }
        };
    };

    // Public API
    function FigshareNodeConfig(selector, url, folderPicker) {
        var self = this;
        self.url = url;
        self.folderPicker = folderPicker;
        self.viewModel = new ViewModel(url, selector, folderPicker);
        $.osf.applyBindings(self.viewModel, selector);
    }

    return FigshareNodeConfig;
}));
