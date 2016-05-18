import functools
import hashlib
import logging
import threading
import os

import binascii
from collections import OrderedDict

import gevent

from website import settings

_local = threading.local()
logger = logging.getLogger(__name__)

def postcommit_queue():
    if not hasattr(_local, 'postcommit_queue'):
        _local.postcommit_queue = OrderedDict()
    return _local.postcommit_queue

def postcommit_before_request():
    _local.postcommit_queue = OrderedDict()

def postcommit_after_request(response, base_status_error_code=500):
    if response.status_code >= base_status_error_code:
        _local.postcommit_queue = OrderedDict()
        return response
    try:
        if postcommit_queue():
            threads = [gevent.spawn(func) for func in postcommit_queue().values()]
            gevent.joinall(threads)

    except AttributeError:
        if not settings.DEBUG_MODE:
            logger.error('Post commit task queue not initialized')
    return response

def enqueue_postcommit_task(fn, args, kwargs, once_per_request=True):
    # make a hash of the pertinent data
    raw = [fn.__name__, fn.__module__, args, kwargs]
    m = hashlib.md5()
    m.update('-'.join([x.__repr__() for x in raw]))
    key = m.hexdigest()

    if not once_per_request:
        # we want to run it once for every occurrence, add a random string
        key = '{}:{}'.format(key, binascii.hexlify(os.urandom(8)))
    postcommit_queue().update({key: functools.partial(fn, *args, **kwargs)})


handlers = {
    'before_request': postcommit_before_request,
    'after_request': postcommit_after_request,
}


def run_postcommit(once_per_request=True):
    '''
    Delays function execution until after the request's transaction has been committed.
    !!!Tasks enqueued using this decorator **WILL NOT** run if the return status code is >= 500!!!
    :return:
    '''
    def wrapper(func):
        # if we're local dev or running unit tests, run without queueing
        if settings.DEBUG_MODE:
            return func
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            enqueue_postcommit_task(func, args, kwargs, once_per_request=once_per_request)
        return wrapped
    return wrapper
