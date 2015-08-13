# -*- coding: utf-8 -*-

import re

from flask import request

from framework.auth.decorators import collect_auth
from framework.auth.core import get_user
from framework.auth.signals import user_confirmed

from website import mails
from website.project.decorators import (
    must_be_valid_project,
    must_have_permission,
    must_not_be_registration,
    must_be_contributor
)
from website.project.mailing_list import (
    create_list,
    delete_list,
    update_subscription
)
from website.util.permissions import ADMIN
from website.models import Node


###############################################################################
# Internal Calls
###############################################################################


@must_be_valid_project
@must_have_permission(ADMIN)
@must_not_be_registration
def enable_discussions(node, **kwargs):
    create_list(title=node.title, **node.mailing_params)
    node.mailing_enabled = True
    node.save()


@must_be_valid_project
@must_have_permission(ADMIN)
@must_not_be_registration
def disable_discussions(node, **kwargs):
    delete_list(node._id)
    node.mailing_enabled = False
    node.save()


@must_be_valid_project
@collect_auth
@must_be_contributor
@must_not_be_registration
def set_subscription(node, auth, **kwargs):
    subscription = request.json.get('discussionsSub')
    subscribed = True if subscription == 'subscribed' else False
    user = auth.user

    update_subscription(node._id, user.email, subscribed)

    if subscribed and user in node.mailing_unsubs:
        node.mailing_unsubs.remove(user)
    elif not subscribed and user not in node.mailing_unsubs:
        node.mailing_unsubs.append(user)

    node.save()


###############################################################################
# Signalled Functions
###############################################################################


@user_confirmed.connect
def resubscribe_on_confirm(user):
    for node in user.node__contributed:
        node.mailing_unsubs.remove(user)
        update_subscription(node._id, user.email, True)


###############################################################################
# MailGun Calls
###############################################################################


def find_email(long_email):
    email = re.search(r'<\S*>$', long_email).group(0)[1:-1]
    return email


def route_message(**kwargs):
    message = request.form
    target = message['To']
    if ' ' in target:
        target = find_email(target)
    node_id = re.search(r'[a-z0-9]*@', target).group(0)[:-1]
    sender_email = message['From']
    # allow for both "{email}" syntax and "{name} <{email}>" syntax
    if ' ' in sender_email:
        sender_email = find_email(sender_email)

    sender = get_user(email=sender_email)
    if sender:
        sender = sender if sender.is_active else None
    node = Node.load(node_id)

    user_is_admin = 'admin' in node.get_permissions(sender)\
        if sender and node else False

    mail_params = {
        'to_addr': sender_email,
        'mail': mails.DISCUSSIONS_EMAIL_REJECTED,
        'target_address': target,
        'user': sender,
        'node_type': node.project_or_component if node else '',
        'node_url': node.absolute_url if node else '',
        'is_admin': user_is_admin
    }

    if not sender:
        reason = 'no_user'
    elif not node:
        reason = 'node_dne'
    elif node.is_deleted:
        reason = 'node_deleted'
    elif sender not in node.contributors:
        reason = 'no_access' if node.is_public else 'private_no_access'
    elif not node.mailing_enabled:
        reason = 'discussions_disabled'
    else:
        reason = ''

    if reason:
        mails.send_mail(reason=reason, **mail_params)

    # Any logging code should go here, since by now we know the email was sent
