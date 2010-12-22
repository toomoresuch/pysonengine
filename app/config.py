# -*- coding: utf-8 -*-

"""
    config
    ~~~~~~

    Configuration settings.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE for more details.
"""

config = {}

# Configurations for the 'tipfy' module.
# Enable debugger. It will be loaded only in development.
# Enable the Hello, World! app example.

config['tipfy'] = {'middleware': ['tipfy.ext.debugger.DebuggerMiddleware'],
                   'apps_installed': ['apps.hello_world', 'apps.api']}

from tipfy.ext.acl import Acl

# Basic ACL idea.
# name: create=POST, read=GET, update=POST/PUT, delete=DELETE
# ACL level (combination of area and user) and
# scan order (from strict to loose) are as follows.
# 1. area = docType:docId, user: email logged in = private(as JsonEngine)
# 2. area = docType:docId, user: *
# 3. area = docType,       user: email logged in
# 4. area = docType,       user: *
# --------------------------------------------------- by member's RESTful
# 5. area = *,             user: email logged in
# 6. area = *,             user: *  = protected(as JsonEngine)
# 7. area = *  = public(as JsonEngine),
#                comment out 'login: required' in app.yaml
# --------------------------------------------------- by superUser's RESTful
# 8. SuperUser
# --------------------------------------------------- by GAE console

Acl.roles_map = {
    'default': [('*', '*', False)],
    'reader': [('member', 'read', True)],
    'editor': [('member', 'create', True), ('member', 'read', True), ('member',
               'update', True)],
    'admin': [('member', 'create', True), ('member', 'read', True), ('member',
              'update', True), ('member', 'delete', True)],
    'superUser': [('*', '*', True)],
    }


