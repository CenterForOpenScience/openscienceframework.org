# -*- coding: utf-8 -*-

import httplib as http
import itertools

from flask import request

from framework.auth.decorators import must_be_logged_in
from framework.status import push_status_message
from framework.exceptions import HTTPError

from website.project.decorators import must_have_permission
from website.project.decorators import must_not_be_registration
from website.project.decorators import must_have_addon
# from website.addons.github.utils import serialize_urls
from website.addons.github.utils import get_repo_dropdown
from website.addons.github.serializer import GitHubSerializer

from ..api import GitHub



@must_be_logged_in
def github_get_user_accounts(auth):
    """View for getting a JSON representation of the logged-in user's
    GitHub user settings.
    """
    user_settings = auth.user.get_addon('github')
    return GitHubSerializer(user_settings=user_settings).serialized_user_settings


@must_have_permission('write')
@must_have_addon('github', 'node')
@must_not_be_registration
def github_set_config(node_addon, **kwargs):


    auth = kwargs['auth']
    user = auth.user

    node = node_addon.owner
    user_settings = node_addon.user_settings

    # If authorized, only owner can change settings
    if user_settings and user_settings.owner != user:
        raise HTTPError(http.BAD_REQUEST)

    # Parse request
    github_user_name = request.json.get('github_repo', '').split('/')[0].strip()
    github_repo_name = request.json.get('github_repo', '').split('/')[1].strip()

    # Verify that repo exists and that user can access
    connection = GitHub.from_settings(node_addon.api.account)
    repo = connection.repo(github_user_name, github_repo_name)
    if repo is None:
        if user_settings:
            message = (
                'Cannot access repo. Either the repo does not exist '
                'or your account does not have permission to view it.'
            )
        else:
            message = (
                'Cannot access repo.'
            )
        return {'message': message}, http.BAD_REQUEST

    if not github_user_name or not github_repo_name:
        raise HTTPError(http.BAD_REQUEST)

    changed = (
        github_user_name != node_addon.user or
        github_repo_name != node_addon.repo
    )

    # Update hooks
    if changed:

        # Delete existing hook, if any
        node_addon.delete_hook()

        # Update node settings
        node_addon.user = github_user_name
        node_addon.repo = github_repo_name

        # Log repo select
        node.add_log(
            action='github_repo_linked',
            params={
                'project': node.parent_id,
                'node': node._id,
                'github': {
                    'user': github_user_name,
                    'repo': github_repo_name,
                }
            },
            auth=auth,
        )

        # Add new hook
        if node_addon.user and node_addon.repo:
            node_addon.add_hook(save=False)

        node_addon.save()

    return GitHubSerializer(
            node_settings=node_addon,
            user_settings=auth.user.get_addon('github'),
        ).serialized_node_settings

@must_have_addon('github', 'node')
@must_have_permission('read')
def github_get_config(auth, node_addon, **kwargs):
    return GitHubSerializer(
        node_settings=node_addon,
        user_settings=auth.user.get_addon('github')
    ).serialized_node_settings


@must_be_logged_in
@must_have_addon('github', 'user')
def github_remove_user_settings(user_addon, **kwargs):
    success = user_addon.revoke_auth(save=True)
    if not success:
        push_status_message(
            'Your GitHub credentials were removed from the OSF, but we were '
            'unable to revoke your OSF information from GitHub. Your GitHub '
            'credentials may no longer be valid.'
        )
        return {'message': 'reload'}, http.BAD_REQUEST


# WIP, need to get repo_list stuff from model.py into here
@must_be_logged_in
@must_have_addon('github', 'node')
@must_have_permission('write')
@must_not_be_registration
def github_repo_list(auth, node_addon, **kwargs):
    user = auth.user
    user_settings = node_addon.user_settings
    # If authorized, only owner can change settings
    if user_settings and user_settings.owner != user:
        raise HTTPError(http.BAD_REQUEST)

    connection = GitHub.from_settings(node_addon.api.account)
    repos = itertools.chain.from_iterable((connection.repos(), connection.my_org_repos()))
    repo_names = [
        '{0} / {1}'.format(repo.owner.login, repo.name)
        for repo in repos
    ]

    return {
        'repo_names': repo_names
    }


@must_have_permission('write')
@must_have_addon('github', 'node')
def github_set_privacy(node_addon, **kwargs):

    github = kwargs['node_addon']
    private = request.form.get('private')

    if private is None:
        raise HTTPError(http.BAD_REQUEST)

    connection = GitHub.from_settings(node_addon.api.account)

    connection.set_privacy(github.user, github.repo, private)

