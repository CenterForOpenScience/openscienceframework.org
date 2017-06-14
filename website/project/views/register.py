# -*- coding: utf-8 -*-
import httplib as http
import itertools

from flask import request
from modularodm import Q
from modularodm.exceptions import NoResultsFound

from framework import status
from framework.exceptions import HTTPError
from framework.flask import redirect  # VOL-aware redirect

from framework.auth.decorators import must_be_signed

from website.archiver import ARCHIVER_SUCCESS, ARCHIVER_FAILURE

from website import settings
from website.exceptions import NodeStateError
from website.project.decorators import (
    must_be_valid_project, must_be_contributor_or_public,
    must_have_permission,
    must_not_be_registration, must_be_registration,
)
from website.identifiers.utils import get_or_create_identifiers, build_ezid_metadata
from osf.models import Identifier, MetaSchema, NodeLog
from website.project.utils import serialize_node
from website.util.permissions import ADMIN
from website import language
from website.project import signals as project_signals
from website.project.metadata.schemas import _id_to_name
from website import util
from website.project.metadata.utils import serialize_meta_schema
from website.project.model import has_anonymous_link
from website.archiver.decorators import fail_archive_on_error

from website.identifiers.client import EzidClient

from .node import _view_project

@must_be_valid_project
@must_be_contributor_or_public
def node_register_page(auth, node, **kwargs):
    """Display the registration metadata for a registration.

    :return: serialized Node
    """

    if node.is_registration:
        return serialize_node(node, auth)
    else:
        status.push_status_message(
            'You have been redirected to the project\'s registrations page. From here you can initiate a new Draft Registration to complete the registration process',
            trust=False)
        return redirect(node.web_url_for('node_registrations', view='draft'))

@must_be_valid_project
@must_have_permission(ADMIN)
def node_registration_retraction_redirect(auth, node, **kwargs):
    return redirect(node.web_url_for('node_registration_retraction_get', _guid=True))

@must_be_valid_project
@must_have_permission(ADMIN)
def node_registration_retraction_get(auth, node, **kwargs):
    """Prepares node object for registration retraction page.

    :return: serialized Node to be retracted
    :raises: 400: BAD_REQUEST if registration already pending retraction
    """

    if not node.is_registration:
        raise HTTPError(http.BAD_REQUEST, data={
            'message_short': 'Invalid Request',
            'message_long': 'Withdrawal of non-registrations is not permitted.'
        })
    if node.is_pending_retraction:
        raise HTTPError(http.BAD_REQUEST, data={
            'message_short': 'Invalid Request',
            'message_long': 'This registration is already pending withdrawal.'
        })

    return serialize_node(node, auth, primary=True)

@must_be_valid_project
@must_have_permission(ADMIN)
def node_registration_retraction_post(auth, node, **kwargs):
    """Handles retraction of public registrations

    :param auth: Authentication object for User
    :return: Redirect URL for successful POST
    """
    if node.is_pending_retraction:
        raise HTTPError(http.BAD_REQUEST, data={
            'message_short': 'Invalid Request',
            'message_long': 'This registration is already pending withdrawal'
        })
    if not node.is_registration:
        raise HTTPError(http.BAD_REQUEST, data={
            'message_short': 'Invalid Request',
            'message_long': 'Withdrawal of non-registrations is not permitted.'
        })

    if node.root_id != node.id:
        raise HTTPError(http.BAD_REQUEST, data={
            'message_short': 'Invalid Request',
            'message_long': 'Withdrawal of non-parent registrations is not permitted.'
        })

    data = request.get_json()
    try:
        node.retract_registration(auth.user, data.get('justification', None))
        node.save()
        node.retraction.ask(node.get_active_contributors_recursive(unique_users=True))
    except NodeStateError as err:
        raise HTTPError(http.FORBIDDEN, data=dict(message_long=err.message))

    return {'redirectUrl': node.web_url_for('view_project')}

@must_be_valid_project
@must_be_contributor_or_public
def node_register_template_page(auth, node, metaschema_id, **kwargs):
    if node.is_registration and bool(node.registered_schema):
        try:
            meta_schema = MetaSchema.find_one(
                Q('_id', 'eq', metaschema_id)
            )
        except NoResultsFound:
            # backwards compatability for old urls, lookup by name
            try:
                meta_schema = MetaSchema.find(
                    Q('name', 'eq', _id_to_name(metaschema_id))
                ).order_by('-schema_version').first()
            except IndexError:
                raise HTTPError(http.NOT_FOUND, data={
                    'message_short': 'Invalid schema name',
                    'message_long': 'No registration schema with that name could be found.'
                })
        if not node.registered_schema.filter(id=meta_schema.id).exists():
            raise HTTPError(http.BAD_REQUEST, data={
                'message_short': 'Invalid schema',
                'message_long': 'This registration has no registration supplment with that name.'
            })

        ret = _view_project(node, auth, primary=True)
        my_meta = serialize_meta_schema(meta_schema)
        if has_anonymous_link(node, auth):
            for indx, schema_page in enumerate(my_meta['schema']['pages']):
                for idx, schema_question in enumerate(schema_page['questions']):
                    if schema_question['title'] in settings.ANONYMIZED_TITLES:
                        del my_meta['schema']['pages'][indx]['questions'][idx]
        ret['node']['registered_schema'] = serialize_meta_schema(meta_schema)
        return ret
    else:
        status.push_status_message(
            'You have been redirected to the project\'s registrations page. From here you can initiate a new Draft Registration to complete the registration process',
            trust=False
        )
        return redirect(node.web_url_for('node_registrations', view=kwargs.get('template')))

@must_be_valid_project  # returns project
@must_have_permission(ADMIN)
@must_not_be_registration
def project_before_register(auth, node, **kwargs):
    """Returns prompt informing user that addons, if any, won't be registered."""
    # TODO: Avoid generating HTML code in Python; all HTML should be in display layer
    messages = {
        'full': {
            'addons': set(),
            'message': 'The content and version history of <strong>{0}</strong> will be copied to the registration.',
        },
        'partial': {
            'addons': set(),
            'message': 'The current version of the content in <strong>{0}</strong> will be copied to the registration, but version history will be lost.'
        },
        'none': {
            'addons': set(),
            'message': 'The contents of <strong>{0}</strong> cannot be registered at this time,  and will not be included as part of this registration.',
        },
    }
    errors = {}

    addon_set = [n.get_addons() for n in itertools.chain([node], node.get_descendants_recursive(primary_only=True))]
    for addon in itertools.chain(*addon_set):
        if not addon.complete:
            continue
        archive_errors = getattr(addon, 'archive_errors', None)
        error = None
        if archive_errors:
            error = archive_errors()
            if error:
                errors[addon.config.short_name] = error
                continue
        name = addon.config.short_name
        if name in settings.ADDONS_ARCHIVABLE:
            messages[settings.ADDONS_ARCHIVABLE[name]]['addons'].add(addon.config.full_name)
        else:
            messages['none']['addons'].add(addon.config.full_name)
    error_messages = errors.values()

    prompts = [
        m['message'].format(util.conjunct(m['addons']))
        for m in messages.values() if m['addons']
    ]

    if node.has_pointers_recursive:
        prompts.append(
            language.BEFORE_REGISTER_HAS_POINTERS.format(
                category=node.project_or_component
            )
        )

    return {
        'prompts': prompts,
        'errors': error_messages
    }


def osf_admin_change_status_identifier(node, status):
    if node.get_identifier_value('doi') and node.get_identifier_value('ark'):
        doi, metadata = build_ezid_metadata(node)
        client = EzidClient(settings.EZID_USERNAME, settings.EZID_PASSWORD)
        client.change_status_identifier(status, doi, metadata)


@must_be_valid_project
@must_be_contributor_or_public
def node_identifiers_get(node, **kwargs):
    """Retrieve identifiers for a node. Node must be a public registration.
    """
    if not node.is_public:
        raise HTTPError(http.BAD_REQUEST)
    return {
        'doi': node.get_identifier_value('doi'),
        'ark': node.get_identifier_value('ark'),
    }


@must_be_valid_project
@must_have_permission(ADMIN)
def node_identifiers_post(auth, node, **kwargs):
    """Create identifier pair for a node. Node must be a public registration.
    """
    if not node.is_public or node.is_retracted:
        raise HTTPError(http.BAD_REQUEST)
    if node.get_identifier('doi') or node.get_identifier('ark'):
        raise HTTPError(http.BAD_REQUEST)
    try:
        identifiers = get_or_create_identifiers(node)
    except HTTPError:
        raise HTTPError(http.BAD_REQUEST)
    for category, value in identifiers.iteritems():
        node.set_identifier_value(category, value)
    node.add_log(
        NodeLog.EXTERNAL_IDS_ADDED,
        params={
            'parent_node': node.parent_id,
            'node': node._id,
            'identifiers': identifiers,
        },
        auth=auth,
    )
    return identifiers, http.CREATED


def get_referent_by_identifier(category, value):
    """Look up identifier by `category` and `value` and redirect to its referent
    if found.
    """
    try:
        identifier = Identifier.find_one(
            Q('category', 'eq', category) &
            Q('value', 'eq', value)
        )
    except NoResultsFound:
        raise HTTPError(http.NOT_FOUND)
    if identifier.referent.url:
        return redirect(identifier.referent.url)
    raise HTTPError(http.NOT_FOUND)

@fail_archive_on_error
@must_be_signed
@must_be_registration
def registration_callbacks(node, payload, *args, **kwargs):
    errors = payload.get('errors')
    src_provider = payload['source']['provider']
    if errors:
        node.archive_job.update_target(
            src_provider,
            ARCHIVER_FAILURE,
            errors=errors,
        )
    else:
        # Dataverse requires two seperate targets, one
        # for draft files and one for published files
        if src_provider == 'dataverse':
            src_provider += '-' + (payload['destination']['name'].split(' ')[-1].lstrip('(').rstrip(')').strip())
        node.archive_job.update_target(
            src_provider,
            ARCHIVER_SUCCESS,
        )
    project_signals.archive_callback.send(node)
