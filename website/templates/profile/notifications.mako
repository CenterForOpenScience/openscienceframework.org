<%inherit file="base.mako"/>
<%def name="title()">Notifications</%def>

<%def name="content()">
<% from website import settings%>
<h2 class="page-header">Settings</h2>

<div id="notificationSettings" class="row">
    <div class="col-sm-3 affix-parent">
      <%include file="include/profile/settings_navpanel.mako" args="current_page='notifications'"/>
    </div>

    <div class="col-sm-9 col-md-7">
        <div class="panel panel-default scripted" id="selectLists">
            <div class="panel-heading clearfix"><h3 class="panel-title">Configure Email Preferences</h3></div>
            <div class="panel-body">
                 <h3>Emails</h3>
                 </br>
                 <div class="form-group">
                     <div data-bind="if: subscribed.indexOf('${settings.MAILCHIMP_GENERAL_LIST}') != -1 ">
                         <input type="checkbox"
                             data-bind="checked: subscribed"
                             value="${settings.MAILCHIMP_GENERAL_LIST}" />
                         <label>${settings.MAILCHIMP_GENERAL_LIST}</label>
                         <p class="text-muted" style="padding-left: 15px">Receive general notifications about the OSF every 2-3 weeks.</p>
                     </div>
                     <div class="form-group" data-bind="if: subscribed.indexOf('${settings.MAILCHIMP_GENERAL_LIST}') == -1 " style="margin-bottom: 0px;">
                         <!-- Begin Mailchimp Signup Form -->
                         <div id="mc_embed_signup">
                         <form style="display: none;" action="https://cos.us9.list-manage.com/subscribe/post?u=4ea2d63bcf7c2776e53a62167&amp;id=c5fabe3548" method="post" id="mc-embedded-subscribe-form" name="mc-embedded-subscribe-form" class="validate" target="_blank" novalidate>
                             <div id="mc_embed_signup_scroll">
                                 <!-- real people should not fill this in and expect good things - do not remove this or risk form bot signups-->
                                 <div style="position: absolute; left: -5000px;" aria-hidden="true"><input type="text" name="b_4ea2d63bcf7c2776e53a62167_c5fabe3548" tabindex="-1" value=""></div>
                                     <input type="email" style="display: none;" value="${user_name}" name="EMAIL" class="email form-control" id="mce-EMAIL" placeholder="email address" required >
                                     <div class="clear" style="display: none;"  ><input type="submit" style="display: none;"  value="Resubscribe" name="subscribe" id="mc-embedded-subscribe" class="btn btn-success form-control"></div>
                                 </div>
                             </div>
                         </form>
                         <div data-bind="click: resubscribeToGeneral">
                             <input type="checkbox" value="${settings.MAILCHIMP_GENERAL_LIST}"/>
                             <label>${settings.MAILCHIMP_GENERAL_LIST}</label>
                             <p class="text-muted" style="padding-left: 15px">Receive general notifications about the OSF every 2-3 weeks.</p>
                        </div>
                     </div>
                 </div>
                <form>
                    <div class="form-group">
                        <input type="checkbox"
                            data-bind="checked: subscribed"
                            value="${settings.OSF_HELP_LIST}"/>
                          <label>${settings.OSF_HELP_LIST}</label>
                        <p class="text-muted" style="padding-left: 15px">Receive helpful tips on how to make the most of the OSF, up to once per week.</p>
                    </div>
                    <div class="p-t-md p-b-md">
                    <button
                        type="submit"
                        class="btn btn-success"
                        data-bind="click: submit"
                    >Save</button>
                    </div>
                </form>
                <!-- Flashed Messages -->
                <div data-bind="html: message, attr: {class: messageClass}"></div>
            </div><!--view model scope ends -->
        </div>
        <div class="panel panel-default">
            <div class="panel-heading clearfix"><h3 class="panel-title">Configure Notification Preferences</h3></div>
            <div class="panel-body">
                <div class="help-block">
                     <p class="text-muted"> NOTE: Regardless of your selected preferences, OSF will continue to provide transactional and administrative service emails.</p>
                </div>
                <form id="selectNotifications" class="osf-treebeard-minimal">
                    <div id="grid">
                        <div class="spinner-loading-wrapper">
                            <div class="ball-scale ball-scale-blue">
                                <div></div>
                            </div>
                            <p class="m-t-sm fg-load-message"> Loading notification settings... </p>
                        </div>
                    </div>
                    <div class="help-block" style="padding-left: 15px">
                            <p id="configureNotificationsMessage"></p>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
</%def>

<%def name="javascript()">
    <% import website %>
    ${parent.javascript()}
    <script type="text/javascript">
        window.contextVars = $.extend({}, window.contextVars, {
            'mailingLists': ${ [website.settings.MAILCHIMP_GENERAL_LIST, website.settings.OSF_HELP_LIST] | sjson, n }
        });
    </script>
</%def>

<%def name="javascript_bottom()">
    ${parent.javascript_bottom()}
    <script src="${"/static/public/js/notifications-config-page.js" | webpack_asset}"></script>
</%def>
