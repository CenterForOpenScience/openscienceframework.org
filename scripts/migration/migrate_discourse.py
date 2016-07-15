import os
import sys
import shutil
import tempfile
import json
import logging

from framework import discourse
from website import models
from website.app import init_app
from modularodm import Q

import pdb

logger = logging.getLogger(__name__)

def serialize_users(file_out):
    users = models.User.find()
    for user in users:
        if user.username == None:
            continue
        data = {}
        data['object_type'] = 'user'
        data['id'] = int(user._id, 36)
        data['email'] = user.username
        data['username'] = user._id
        data['name'] = user.fullname
        data['avatar_url'] = user.profile_image_url()

        logger.info('Serializing user %s' % user.fullname)
        json.dump(data, file_out)

def serialize_projects(file_out):
    projects = models.Node.find()
    for project in projects:
        data = {}
        data['object_type'] = 'project'
        data['id'] = int(project._id, 36)
        data['guid'] = project._id
        data['is_public'] = project.is_public
        contributors = [int(user._id, 36) for user in project.contributors if user.username]
        data['contributors'] = contributors

        logger.info('Serializing project %s' % project.label)
        json.dump(data, file_out)


def serialize_comments(file_out):
    comments = models.Comment.find().sort('date_created')
    for comment in comments:
        if comment.target == comment.root_target:
            # First create the topic itself
            data = {}
            data['object_type'] = 'post'
            data['post_type'] = 'topic'
            data['id'] = int(comment.node.guid_id, 36)
            data['type'] = comment.page
            data['date_created'] = comment.date_created.isoformat()
            data['title'] = comment.node.label
            data['content'] = discourse.make_topic_content(comment.node)
            data['parent_guids'] = discourse.get_parent_guids(comment.node)
            data['topic_guid'] = comment.node.guid_id

            logger.info('Serializing topic %s' % comment.node.label)
            json.dump(data, file_out)

        data = {}
        data['object_type'] = 'post'
        data['post_type'] = 'comment'
        data['id'] = comment._id
        data['user'] = int(comment.user._id, 36)
        data['content'] = comment.content
        data['date_created'] = comment.date_created.isoformat()
        if comment.target == comment.root_target:
            data['reply_to'] = int(comment.node.guid_id, 36)
        else:
            data['reply_to'] = comment.target._id

        logger.info('Serializing comment %s' % comment._id)
        json.dump(data, file_out)

def main():
    if len(sys.argv) != 2:
        sys.exit('Usage: %s [output_file | --dry]' % sys.arv[0])

    dry_run = False
    if '--dry' in sys.argv:
        dry_run = True
        out_file = sys.stdout
        logger.warn('Dry_run mode')
    else:
        out_file = open(sys.argv[1], 'w')

    init_app(set_backends=True, routes=False)

    serialize_users(out_file)
    serialize_projects(out_file)
    serialize_comments(out_file)

    if dry_run:
        print('')

if __name__ == '__main__':
    main()
