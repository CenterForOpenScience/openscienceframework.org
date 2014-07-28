# -*- coding: utf-8 -*-

import os
import logging
import unicodedata
import httplib as http
from flask import request, redirect, make_response

from framework.mongo import db
from framework.exceptions import HTTPError
from framework.analytics import update_counters

from website.project.decorators import (
    must_be_contributor_or_public, must_not_be_registration,
    must_have_permission, must_have_addon,
)
from website.util import rubeus
from website.util.permissions import WRITE
from website.models import NodeLog
from website.project.views.file import get_cache_content
from website.addons.base import AddonError
from website.addons.base.views import check_file_guid
from website.project import utils

from website.addons.base.services.fileservice import FileServiceError

from website.addons.gitlab import utils_files
from website.addons.gitlab import utils as gitlab_utils
from website.addons.gitlab import settings as gitlab_settings
from website.addons.gitlab.model import GitlabGuidFile
from website.addons.gitlab.services import fileservice


route_collection = db['gitlab-compat-routes']

logger = logging.getLogger(__name__)


def get_cache_file(path, sha):
    return u'{0}_{1}.html'.format(path, sha)


def get_guid(node_addon, path, ref):
    """

    """
    try:
        return GitlabGuidFile.get_or_create(node_addon, path, ref)
    except AddonError:
        raise HTTPError(http.NOT_FOUND)


def gitlab_upload_log(node, action, auth, data, branch):
    """

    """
    node_logger = gitlab_utils.GitlabNodeLogger(
        node, auth=auth, path=data['file_path'],
        branch=branch,
    )
    node_logger.log(action)


@must_have_permission(WRITE)
@must_not_be_registration
@must_have_addon('gitlab', 'node')
def gitlab_upload_file(auth, node_addon, **kwargs):

    node = kwargs['node'] or kwargs['project']

    # Lazily configure Gitlab
    gitlab_utils.setup_user(auth.user)
    gitlab_utils.setup_node(node, check_ready=True)
    user_addon = auth.user.get_addon('gitlab')

    path = gitlab_utils.kwargs_to_path(kwargs, required=False)
    branch = utils_files.ref_or_default(node_addon, request.args)

    upload = request.files.get('file')

    file_service = fileservice.GitlabFileService(node_addon)
    try:
        action, response = file_service.upload(
            path,
            upload,
            branch=branch,
            user_addon=user_addon,
        )
    except FileServiceError:
        return {
            'actionTaken': None,
            'name': upload.filename,
        }

    status = http.CREATED if action == NodeLog.FILE_ADDED else http.OK
    action_taken = 'file_added' if action == NodeLog.FILE_ADDED else 'file_updated'
    gitlab_upload_log(node, action, auth, response, branch)

    # File created or modified
    head, tail = os.path.split(response['file_path'])
    grid_data = gitlab_utils.item_to_hgrid(
        node,
        {
            'type': 'blob',
            'name': tail,
        },
        path=head,
        permissions={
            'view': True,
            'edit': True,
        },
        branch=branch,
        action_taken=action_taken,
    )
    return grid_data, status


def gitlab_hgrid_root(node_addon, auth, **kwargs):
    """Private helper returning the root container for a GitLab repo.

    """
    node = node_addon.owner

    #
    branch, sha = gitlab_settings.DEFAULT_BRANCH, None
    branches = [gitlab_settings.DEFAULT_BRANCH]

    #
    if node_addon.project_id is not None:
        # TODO: Improve error handling
        file_service = fileservice.GitlabFileService(node_addon)
        gitlab_branches = file_service.list_branches()
        if gitlab_branches:
            branches = [
                each['name']
                for each in gitlab_branches
            ]
            branch, sha = utils_files.get_branch_and_sha(node_addon, kwargs)

    permissions = {
        'edit': node.can_edit(auth=auth) and not node.is_registration,
        'view': True,
    }
    urls = gitlab_utils.build_full_urls(
        node, {'type': 'tree'}, path='',
        branch=branch, sha=sha
    )

    extra = gitlab_utils.render_branch_picker(branch, sha, branches)

    return [rubeus.build_addon_root(
        node_addon,
        name=None,
        urls=urls,
        permissions=permissions,
        extra=extra,
    )]


@must_be_contributor_or_public
@must_have_addon('gitlab', 'node')
def gitlab_hgrid_root_public(**kwargs):
    """View function returning the root container for a GitLab repo. This
    view is exposed to allow switching between branches in the file grid
    interface.

    """
    node_settings = kwargs['node_addon']
    auth = kwargs['auth']
    data = request.args.to_dict()

    return gitlab_hgrid_root(node_settings, auth=auth, **data)


@must_be_contributor_or_public
@must_have_addon('gitlab', 'node')
def gitlab_list_files(node_addon, auth, path='', **kwargs):

    node = kwargs['node'] or kwargs['project']

    # Don't crash if Gitlab project hasn't been created yet
    if not node_addon.project_id:
        return []

    branch = request.args.get('branch')
    sha = request.args.get('sha')

    file_service = fileservice.GitlabFileService(node_addon)
    try:
        tree = file_service.list_files(path, sha, branch)
    except FileServiceError:
        return []

    permissions = {
        'view': True,
        'edit': (
            node.has_permission(auth.user, WRITE)
            and not node.is_registration
        )
    }

    return gitlab_utils.gitlab_to_hgrid(
        node, tree, path, permissions, branch, sha
    )


@must_be_contributor_or_public
@must_have_addon('gitlab', 'node')
def gitlab_file_commits(node_addon, **kwargs):
    """

    """
    branch = request.args.get('branch')
    sha = request.args.get('sha')
    ref = utils_files.ref_or_default(node_addon, request.args)

    path = gitlab_utils.kwargs_to_path(kwargs, required=True)
    guid = get_guid(node_addon, path, ref)

    file_service = fileservice.GitlabFileService(node_addon)
    try:
        commits = file_service.list_commits(branch, path)
    except fileservice.ListCommitsError:
        raise HTTPError(http.BAD_REQUEST)
    sha = sha or commits[0]['id']

    commit_data = [
        gitlab_utils.serialize_commit(
            node_addon.owner, path, commit, guid, branch
        )
        for commit in commits
    ]

    return {
        'sha': sha,
        'commits': commit_data,
    }


@must_be_contributor_or_public
@must_have_addon('gitlab', 'node')
def gitlab_view_file(auth, node_addon, **kwargs):

    node = node_addon.owner

    path = gitlab_utils.kwargs_to_path(kwargs, required=True)
    _, filename = os.path.split(path)

    branch = request.args.get('branch')

    # SHA cannot be None here, since it will be used in `get_cache_file`
    # below
    sha = (
        request.args.get('sha')
        or utils_files.get_default_file_sha(node_addon, path=path)
    )

    guid = get_guid(node_addon, path, sha)

    redirect_url = check_file_guid(guid)
    if redirect_url:
        return redirect(redirect_url)

    file_service = fileservice.GitlabFileService(node_addon)
    try:
        contents = file_service.download(path, sha)
    except FileServiceError:
        raise HTTPError(http.NOT_FOUND)

    # Get file URL
    commits_url = node.api_url_for(
        'gitlab_file_commits',
        path=path, branch=branch, sha=sha
    )

    guid_urls = gitlab_utils.build_guid_urls(guid, branch=branch, sha=sha)
    full_urls = gitlab_utils.build_full_urls(
        node, {'type': 'blob'}, path, branch=branch, sha=sha
    )

    # Get or create rendered file
    cache_file = get_cache_file(path, sha)
    rendered = get_cache_content(node_addon, cache_file)
    if rendered is None:
        # TODO: Skip large files
        rendered = get_cache_content(
            node_addon, cache_file, start_render=True,
            file_path=filename, file_content=contents,
            download_path=guid_urls['download'],
        )

    out = {
        'file_name': filename,
        'commits_url': commits_url,
        'render_url': full_urls['render'],
        'download_url': guid_urls['download'],
        'rendered': rendered,
    }
    out.update(utils.serialize_node(node, auth, primary=True))
    return out


@must_be_contributor_or_public
@must_have_addon('gitlab', 'node')
@update_counters(u'download:{target_id}:{path}:{sha}')
@update_counters(u'download:{target_id}:{path}')
def gitlab_download_file(node_addon, **kwargs):

    path = gitlab_utils.kwargs_to_path(kwargs, required=True)
    ref = utils_files.ref_or_default(node_addon, request.args)

    file_service = fileservice.GitlabFileService(node_addon)
    try:
        contents = file_service.download(path, ref)
    except FileServiceError:
        raise HTTPError(http.NOT_FOUND)

    # Build response
    resp = make_response(contents)

    # Build headers
    # Note: Response headers must be in latin-1 encoding, which requires
    # unicode to be normalized to composite form.
    _, filename = os.path.split(path)
    normalized_filename = unicodedata.normalize('NFKC', filename)
    encoded_filename = normalized_filename.encode('latin-1', 'ignore')
    disposition = 'attachment; filename={0}'.format(encoded_filename)
    resp.headers['Content-Disposition'] = disposition

    # Add binary MIME type if extension missing
    _, ext = os.path.splitext(filename)
    if not ext:
        resp.headers['Content-Type'] = 'application/octet-stream'

    return resp


@must_have_permission(WRITE)
@must_not_be_registration
@must_have_addon('gitlab', 'node')
def gitlab_delete_file(auth, node_addon, **kwargs):

    node = kwargs['node'] or kwargs['project']
    path = gitlab_utils.kwargs_to_path(kwargs, required=True)
    branch = utils_files.ref_or_default(node_addon, request.args)

    file_service = fileservice.GitlabFileService(node_addon)
    try:
        file_service.delete(path, branch)
    except FileServiceError:
        raise HTTPError(http.BAD_REQUEST)

    node_logger = gitlab_utils.GitlabNodeLogger(
        node, auth=auth, path=path,
        branch=branch,
    )
    node_logger.log(NodeLog.FILE_REMOVED)


@must_be_contributor_or_public
@must_have_addon('gitlab', 'node')
def gitlab_get_rendered_file(**kwargs):
    """

    """
    node_settings = kwargs['node_addon']
    path = gitlab_utils.kwargs_to_path(kwargs, required=True)

    sha = (
        request.args.get('sha')
        or utils_files.get_default_file_sha(node_settings, path)
    )

    cache_file = get_cache_file(path, sha)
    return get_cache_content(node_settings, cache_file)


@must_be_contributor_or_public
@must_have_addon('gitlab', 'node')
def gitlab_osffiles_url(project, node=None, fid=None, vid=None, **kwargs):
    """Redirect pre-GitLab URLs to current URLs. Raises 404 if version is
    specified but not found in routing table.

    """
    node = node or project

    if vid is None:
        return redirect(
            node.web_url_for(
                'gitlab_download_file',
                path=fid
            )
        )

    fid_clean = fid.replace('.', '_')
    route_record = route_collection.find_one({'_id': node._id}) or {}
    route_data = route_record.get('routes', {})
    file_versions = route_data.get(fid_clean, {})
    # Note: Must stringify keys for MongoDB
    try:
        version_key = str(vid)
        return redirect(
            node.web_url_for(
                'gitlab_download_file',
                path=fid,
                branch='master',
                sha=file_versions[version_key],
            )
        )
    except KeyError:
        logger.warn('No route found for file {0}:{1}'.format(fid, vid))
        raise HTTPError(http.NOT_FOUND)
