# -*- coding: utf-8 -*-

"""
    handlers
    ~~~~~~~~

    Hello, World!: the simplest tipfy app.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE for more details.
"""

from google.appengine.api.users import create_logout_url, get_current_user
from tipfy import RequestHandler, Response
from tipfy.ext.jinja2 import render_response


class HelloWorldHandler(RequestHandler):

    def get(self):
        """Simply returns a Response object with an enigmatic salutation."""

        logout = create_logout_url('/')
        current_user = get_current_user()
        return Response('<p><a href="%s">Logout!</a></p><p>%s</p>' % (logout,
                        current_user))


class PrettyHelloWorldHandler(RequestHandler):

    def get(self):
        """Simply returns a rendered template with an enigmatic salutation."""

        return render_response('hello_world.html', message='Hello, World!')



