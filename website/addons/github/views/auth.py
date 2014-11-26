# -*- coding: utf-8 -*-

import os
import httplib as http

from flask import request

from framework.flask import redirect  # VOL-aware redirect
from framework.auth.decorators import must_be_logged_in
from framework.exceptions import HTTPError

from website import models
from website.project.decorators import (
    must_have_permission, must_not_be_registration, must_have_addon
)
from website.util import web_url_for
from website.util import api_url_for

from ..api import GitHub
from ..auth import oauth_start_url, oauth_get_token
from ..model import AddonGitHubOauthSettings
from ..views.config import serialize_settings


def get_profile_view(user_settings):
    return {
        'url': user_settings.url
    }


@must_have_permission('write')
@must_have_addon('github', 'user')
@must_have_addon('github', 'node')
def github_import_user_auth(user_addon, node_addon, **kwargs):
    user = get_current_user()
    node_addon.authorize(user_addon, save=True)
    return {
        'result': serialize_settings(node_addon, user),
        'message': 'Successfully imported access token from profile.',
    }, http.OK


@must_be_logged_in
<<<<<<< HEAD
def github_oauth_start(**kwargs):
    user = get_current_user()
=======
def github_oauth_start(auth, **kwargs):

    user = auth.user

>>>>>>> ce48dc2dc7ef27912e5f374de1b5557c0ae4427c
    nid = kwargs.get('nid') or kwargs.get('pid')
    node = models.Node.load(nid) if nid else None

    # Fail if node provided and user not contributor
    if node and not node.is_contributor(user):
        raise HTTPError(http.FORBIDDEN)

    user.add_addon('github')
    user_settings = user.get_addon('github')

    if node:
        github_node = node.get_addon('github')
        github_node.user_settings = user_settings
        github_node.save()

    authorization_url, state = oauth_start_url(user, node)

    user_settings.oauth_state = state
    user_settings.save()

    return redirect(authorization_url)


def create_and_attach_oauth(user_settings, access_token, token_type):
    """helper function to set the AddonGitHubOauthsettings and link it with
    AddonGitHubUserSettings

    :param AddonGitHubUserSettings user_settings: User settings record
    :param str access_token: OAuth access token
    :param str token_type: OAuth token type


    """
    gh = GitHub(access_token, token_type)
    github_user = gh.user()

    oauth_settings = AddonGitHubOauthSettings.load(github_user.id)

    if not oauth_settings:
        oauth_settings = AddonGitHubOauthSettings()
        oauth_settings.github_user_id = str(github_user.id)
        oauth_settings.save()

    user_settings.oauth_settings = oauth_settings

    #in user_settings
    user_settings.oauth_state = None

    #in oauth_settings
    user_settings.oauth_access_token = access_token
    user_settings.oauth_token_type = token_type
    user_settings.github_user_name = github_user.login

    user_settings.save()


def github_oauth_callback(**kwargs):

    user = models.User.load(kwargs.get('uid'))
    node = models.Node.load(kwargs.get('nid'))

    if user is None:
        raise HTTPError(http.NOT_FOUND)
    if kwargs.get('nid') and not node:
        raise HTTPError(http.NOT_FOUND)

    user_settings = user.get_addon('github')

    if user_settings is None:
        raise HTTPError(http.BAD_REQUEST)

    if user_settings.oauth_state != request.args.get('state'):
        raise HTTPError(http.BAD_REQUEST)

    node_settings = node.get_addon('github') if node else None

    code = request.args.get('code')
    if code is None:
        raise HTTPError(http.BAD_REQUEST)

    token = oauth_get_token(code)

    create_and_attach_oauth(user_settings, token['access_token'], token['token_type'])

    if node_settings:
        node_settings.user_settings = user_settings
        # previously connected to Github?
        if node_settings.user and node_settings.repo:
            node_settings.add_hook(save=False)
        node_settings.save()

    if node:
        return redirect(os.path.join(node.url, 'settings'))
    return redirect(web_url_for('user_addons'))

@must_be_logged_in
@must_have_addon('github', 'user')
def github_oauth_delete_user(auth, user_addon, **kwargs):
    user_addon.clear_auth(auth=auth, save=True)
    return {}


@must_have_permission('write')
@must_have_addon('github', 'node')
@must_not_be_registration
def github_oauth_deauthorize_node(auth, node_addon, **kwargs):
    node_addon.deauthorize(auth=auth, save=True)
    return {}


@must_be_logged_in
@must_have_addon('github', 'user')
def github_user_config_get(user_addon, auth, **kwargs):
    """View for getting a JSON representation of the logged-in user's
    Github user settings.
    """
    urls = {
        'create': api_url_for('github_oauth_start__user'),
        'delete': api_url_for('github_oauth_delete_user')
    }
    return {
        'result': {
            'userHasAuth': user_addon.has_auth,
            'urls': urls,
        },
    }, http.OK
