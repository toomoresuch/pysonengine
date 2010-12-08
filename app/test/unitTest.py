# -*- coding: utf-8 -*-

from tipfy import RequestHandler, Response, Rule, Tipfy, default_config
from apps.hello_world.handlers import HelloWorldHandler

import gae_test_base
import unittest


class TestCase(gae_test_base.GAETestBase):

    # USE_PRODUCTION_STUBS = True
    # USE_REMOTE_STUBS = True

    CLEANUP_USED_KIND = True

    def setUp(self):
        app = Tipfy(rules=[Rule('/', endpoint='home',
                    handler=HelloWorldHandler)])
        self.client = app.get_test_client()
        gae_test_base.APP_ID = default_config['app_id']

    def tearDown(self):
        pass

    def test(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'Hello, World!')


if __name__ == '__main__':
    unittest.main()

