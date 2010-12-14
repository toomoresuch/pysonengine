# -*- coding: utf-8 -*-

"""
    urls
    ~~~~

    URL definitions.

    :copyright: 2010 by toomore_such project.
    :license: MIT, see LICENSE for more details.
"""

from tipfy import Rule

UPDATE = Rule('/_api/<doc_type>/<doc_id>', endpoint='api/doctype/docid',
              handler='apps.api.handlers.UpdateHandler')
CREATE = Rule('/_api/<doc_type>', endpoint='api/doctype',
              handler='apps.api.handlers.CreateHandler')


def get_rules(app):
    """Returns a list of URL rules for the Hello, World! application.

    :param app:
        The WSGI application instance.
    :return:
        A list of class:`tipfy.Rule` instances.
    """

    rules = [UPDATE, CREATE]

    return rules



