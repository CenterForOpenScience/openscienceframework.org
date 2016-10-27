from .common import DiscourseException, request

import requests
import logging
import framework.logging # importing this configures the logger
from website import settings

logger = logging.getLogger(__name__)

file_category = None
wiki_category = None
project_category = None

def _get_or_create_category(category_name, color):
    match = [c['id'] for c in _categories if c['slug'].lower() == category_name.lower()]
    if len(match) > 0:
        return match[0]
    return create_category(category_name, color)

def get_categories():
    result = request('get', '/categories.json')
    return result['category_list']['categories']

def create_category(category_name, color):
    data = {}
    data['name'] = category_name
    data['slug'] = category_name.lower()
    data['color'] = color
    data['text_color'] = 'FFFFFF'
    data['allow_badges'] = 'true'
    #data['permissions[everyone]'] = '2'
    return request('post', '/categories', data)['category']['id']


def load_basic_categories():
    try:
        _categories = get_categories()

        file_category = _get_or_create_category('Files', settings.DISCOURSE_CATEGORY_COLORS[0])
        wiki_category = _get_or_create_category('Wikis', settings.DISCOURSE_CATEGORY_COLORS[1])
        project_category = _get_or_create_category('Projects', settings.DISCOURSE_CATEGORY_COLORS[2])
    except (DiscourseException, requests.exceptions.ConnectionError):
        logger.exception('Discourse is either not running, or is malfunctioning. For correct Discourse functionality, please configure Discourse and make sure it is running.')

load_basic_categories()
