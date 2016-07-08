from website import settings
import requests
from simplejson.scanner import JSONDecodeError

log_requests = False

class DiscourseException(Exception):
    def __init__(self, message, result):
        super(DiscourseException, self).__init__(message)
        self.result = result

def request(method, path, data={}, user_name=None):
    params = {}
    params['api_key'] = settings.DISCOURSE_API_KEY
    params['api_username'] = user_name if user_name else settings.DISCOURSE_API_ADMIN_USER

    url = requests.compat.urljoin(settings.DISCOURSE_SERVER_URL, path)
    result = getattr(requests, method)(url, data=data, params=params)

    if log_requests:
        print(method + ' \t' + result.url + ' with ' + str(data))

    if result.status_code < 200 or result.status_code > 299:
        raise DiscourseException('Discourse server responded to ' + method + ' request ' + result.url + ' with '
                                 + ' post data ' + str(data) + ' with result code '
                                 + str(result.status_code) + ': ' + result.text[:500],
                                 result)

    try:
        return result.json()
    except JSONDecodeError:
        return None
