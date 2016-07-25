import Ember from 'ember';

/**
 * Modal that handles adding and removing contributors from a project
 * @class modal-add-contribs
 */
export default Ember.Component.extend({
    /**
     * @property {String} page Which page of the modal to display
     * @default whom|which|invite
     */
    page: 'whom',  // TODO: Replace this with components; temp feature

    //////////////////////////////////
    //  OPTIONS FOR THE WHOM PAGE   //
    //////////////////////////////////
    // The username to search for
    _searchText: null,
    // Store results array from search. TODO: Make this store a promise so we can check fulfilled status
    searchResults: null,

    // People to add as contributors
    contribsToAdd: Ember.A(),

    // Some computed properties
    canViewParent: Ember.computed.alias('model.parent'), // TODO : verify first whether user can view parent. May need a new model field.

    // TODO: This link should be hidden if the only search results returned are for people who are already contributors on the node
    // Was: addAllVisible, contribAdder.js
    showAddAll: true, // TODO: Implement

    actions: {
        selectPage(pageName) {
            this.set('page', pageName);
        }

        //////////////////////////////////
        //  Actions for the whom page   //
        //////////////////////////////////
        searchPeople() {
            // TODO: implement
            console.log('Performed a search');
            let text = this.get('_searchText');
            if (!text) {
                return;
            }
        },
        importContribsFromParent() {
            //TODO: Import contributors from parent
            console.log('Imported contributors!');
        },

        addAllContributors() {
            // TODO: Implement, was addAll in contribAdder.js
            console.log('Added all available results as contributors');
        },
        addOneContributor() {
            // TODO: Implement. Was $root.add
        },
        submitContributors() {
            // TODO: Implement. Send contribs list to server.

        },
        submitInvite() {
            // TODO: Not currently implemented pending required APIv2 capabilities
            console.log('User invited!');
        }
    }
});
