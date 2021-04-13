# -*- coding: utf-8 -*-
"""Asynchronous task queue module."""
from celery import Celery
from celery.utils.log import get_task_logger
from osf.utils.requests import requests_retry_session

from raven import Client
from raven.contrib.celery import register_signal

from website.settings import SENTRY_DSN, VERSION, CeleryConfig, IA_ARCHIVE_ENABLED, OSF_PIGEON_URL

app = Celery()
app.config_from_object(CeleryConfig)

if SENTRY_DSN:
    client = Client(SENTRY_DSN, release=VERSION, tags={'App': 'celery'})
    register_signal(client)

if CeleryConfig.broker_use_ssl:
    app.setup_security()

@app.task
def error_handler(task_id, task_name):
    """logs detailed message about tasks that raise exceptions

    :param task_id: TaskID of the failed task
    :param task_name: name of task that failed
    """
    # get the current logger
    logger = get_task_logger(__name__)
    # query the broker for the AsyncResult
    result = app.AsyncResult(task_id)
    excep = result.get(propagate=False)
    # log detailed error mesage in error log
    logger.error('#####FAILURE LOG BEGIN#####\n'
                r'Task {0} raised exception: {0}\n\{0}\n'
                '#####FAILURE LOG STOP#####'.format(task_name, excep, result.traceback))


@app.task(max_retries=5, default_retry_delay=60)
def send_to_pigeon(node_id):
    requests_retry_session().post(f'{OSF_PIGEON_URL}archive/{node_id}')
