import functools
import waffle

from flask import request

from framework.auth.core import _get_current_user
from website.ember_osf_web.views import use_ember_app


def ember_flag_is_active(flag_name):
    """
    Decorator for checking whether ember flag is active.  If so, proxy to ember
    app, otherwise, load old view.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            # Waffle does not enjoy NoneTypes as user values.
            mock_user = type('Mock User', (object,), {'is_authenticated': False})()
            request.user = _get_current_user() or mock_user

            if waffle.flag_is_active(request, flag_name):
                return use_ember_app()
            else:
                return func(*args, **kwargs)
        return wrapped
    return decorator
