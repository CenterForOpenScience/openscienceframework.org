<link rel="stylesheet" href="/static/css/mailing-list-modal.css">
<% from framework.auth.core import User %>
<% from website.settings import PROJECT_MAILING_ENABLED %>
<% from website.notifications.model import NotificationSubscription %>
<% from modularodm import Q %>
% if PROJECT_MAILING_ENABLED:
    <div class="modal fade" id="mailingListContributorsModal">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                  <h3>Project mailing list email</h3>
                </div>

                <div class="modal-body">
                    <h4 class="row text-center">
                    <div class="btn-group">
                        <a href="mailto:${node['id']}@lists.mechanysm.com">${node['id']}@lists.mechanysm.com</a>
                    </div>
                    </h4>
                    <% unsubs = NotificationSubscription.find_one(Q('owner', 'eq', node['id']) & Q('event_name', 'eq', 'mailing_list_events')).none %>
                    % if len(unsubs):
                        <p>${len(node['contributors']) - len(unsubs)} out of ${len(node['contributors'])} contributors will receive any email sent to this address.</p>
                        <p>A contributor who is not subscribed to this mailing list will not receive any emails sent to it. To
                        % if user['is_admin']:
                            disable or 
                        % endif:
                            unsubscribe from this mailing list, visit the <a href="${node['url']}settings/#configureNotificationsAnchor" class="">${node['category']} settings</a>.
                        </p>
                        <div class="padded-list contrib-list">
                            Contributors not on this list: 
                            <a id="unsubToggle" role="button" data-toggle="collapse" href="#unsubContribs" aria-expanded="false" aria-controls="unsubContribs">
                                Show
                            </a>
                            <div id="unsubContribs" class="panel-collapse collapse" role="tabpanel" aria-expanded="false" aria-labelledby="unsubToggle">
                            % for each in unsubs:
                                <div class="padded-list">
                                    ${each}
                                   <!-- User.find_one(Q('id', 'eq', each)).username}-->
                                </div>
                            % endfor
                            </div>
                        </div>
                    % else:
                        <br/>
                        <p>All contributors are subscribed and will receive any email sent to this address.</p>
                    % endif

                </div><!-- end modal-body -->

                <div class="modal-footer">

                    <a href="#" class="btn btn-default" data-dismiss="modal">Close</a>

                </div><!-- end modal-footer -->
            </div><!-- end modal-content -->
        </div><!-- end modal-dialog -->
    </div><!-- end modal -->

    <script>
    $(document).ready(function() {
        $('#unsubContribs').on('hide.bs.collapse', function () {
            $('#unsubToggle').text('Show');
        });
        $('#unsubContribs').on('show.bs.collapse', function () {
            $('#unsubToggle').text('Hide');
        });
    });
    </script>

% endif
