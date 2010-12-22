# -*- coding: utf-8 -*-

"""
    urls
    ~~~~

    URL definitions.

    :copyright: 2010 by toomore_such project.
    :license: MIT, see LICENSE for more details.
"""

from tipfy import Rule

ACL_FOR_DOCTYPE = Rule('/_api/acl/<doc_type>', endpoint='api/acl/doctype',
                       handler='apps.api.handlers.ACLforDocTypeHandler')

DOC_BY_DOCID = Rule('/_api/<doc_type>/<doc_id>', endpoint='api/doctype/docid',
                    handler='apps.api.handlers.DocByDocIdHandler')
DOC_BY_DOCTYPE = Rule('/_api/<doc_type>', endpoint='api/doctype',
                      handler='apps.api.handlers.DocByDocTypeHandler')


def get_rules(app):
    """Returns a list of URL rules for the Hello, World! application.

    :param app:
        The WSGI application instance.
    :return:
        A list of class:`tipfy.Rule` instances.
    """

    rules = [ACL_FOR_DOCTYPE, DOC_BY_DOCID, DOC_BY_DOCTYPE]

    return rules



