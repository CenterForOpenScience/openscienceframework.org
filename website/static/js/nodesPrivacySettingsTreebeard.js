'use strict';

var $ = require('jquery');
var m = require('mithril');
var ko = require('knockout');
var Treebeard = require('treebeard');
var $osf = require('js/osfHelpers');
var projectSettingsTreebeardBase = require('js/projectSettingsTreebeardBase');

function NodesPrivacyTreebeard(divID, data, nodesState, nodesOriginal) {
    /**
     * nodesChanged and nodesState are knockout variables.  nodesChanged will keep track of the nodes that have
     *  changed state.  nodeState is all the nodes in their current state.
     * */
    var tbOptions = $.extend({}, projectSettingsTreebeardBase.defaults, {
        divID: divID,
        filesData: data,
        naturalScrollLimit : 0,
        rowHeight : 35,
        hScroll : 0,
        columnTitles : function() {
            return [
                {
                    title: 'checkBox',
                    width: '4%',
                    sortType : 'text',
                    sort : true
                },
                {
                    title: 'project',
                    width : '96%',
                    sortType : 'text',
                    sort: true
                }
            ];
        },
        resolveRows: function nodesPrivacyResolveRows(item){
            var tb = this;
            var columns = [];
            var id = item.data.node.id;
            var nodesStateLocal = ko.toJS(nodesState());
            //this lets treebeard know when changes come from the knockout side (select all or select none)
            item.data.node.is_public = nodesStateLocal[id].public;
            columns.push(
                {
                    data : 'action',
                    sortInclude : false,
                    filter : false,
                    custom : function () {
                        return m('input[type=checkbox]', {
                            disabled : !item.data.node.can_write,
                            onclick : function() {
                                item.data.node.is_public = !item.data.node.is_public;
                                item.open = true;
                                nodesStateLocal[id].public = item.data.node.is_public;
                                if (nodesStateLocal[id].public !== nodesOriginal[id].local) {
                                    nodesStateLocal[id].changed = true;
                                }
                                else {
                                    nodesStateLocal[id].changed = false;
                                }
                                nodesState(nodesStateLocal);
                                tb.updateFolder(null, item);
                            },
                            checked: nodesState()[id].public
                        });
                    }
                },
                {
                    data: 'project',  // Data field name
                    folderIcons: true,
                    filter: true,
                    sortInclude: false,
                    hideColumnTitles: false,
                    custom: function () {
                        return m('span', item.data.node.title);
                    }
                }
            );
            return columns;
        }
    });

    var treebeardPromise = new Promise(function(resolve) {
      resolve(new Treebeard(tbOptions));
    });

    treebeardPromise.then(function(grid) {
        projectSettingsTreebeardBase.expandOnLoad.call(grid.tbController);
    });

}
module.exports = NodesPrivacyTreebeard;

