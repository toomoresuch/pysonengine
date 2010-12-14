# -*- coding: utf-8 -*-

import datetime
import gae_test_base
import os
import re
import simplejson as json
import unittest
import urllib

from google.appengine.api.users import get_current_user
from tipfy import RequestHandler, Response, Rule, Tipfy, default_config
from werkzeug.exceptions import NotFound

from apps.api.models import PEDoc

gae_test_base.APP_ID = 'ano-devs-an'
gae_test_base.LOGGED_IN_USER = 'test@example.com'  # 'test@gmail.com'


class TestCase(gae_test_base.GAETestBase):

    # USE_PRODUCTION_STUBS = True
    # USE_REMOTE_STUBS = True

    CLEANUP_USED_KIND = True

    # /_api/myDoc?double=2e+1
    # /_api/myDoc?boolean=true&boolean=false <= array
    # /_api/myDoc?string=Hoge
    # self.REGEX_DATE = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}'
    # self.REGEX_DOC_ID = r'myDoc:\w{32}'

    DOC_ID = ', "_docId": "1234567890abcdefghijklmnopqrstuv"'
    SEED = '{"double": 2e+1, "boolean": [true, false], "string": "Hoge"%s}'
    SEED_FOR_UPDATE = '{"double": 3e-1, "boolean": [false, true]%s}'

    DAT = urllib.quote(SEED % '')
    DAT_WITH_DOC_ID = urllib.quote(SEED % DOC_ID)

    DAT_FOR_UPDATE = urllib.quote(SEED_FOR_UPDATE % '')
    DAT_FOR_UPDATE_WITH_DOC_ID = urllib.quote(SEED_FOR_UPDATE % DOC_ID)

    CLIENT = Tipfy(rules=[Rule('/_api/<doc_type>/<doc_id>',
                   endpoint='api/doctype/docid',
                   handler='apps.api.handlers.UpdateHandler'),
                   Rule('/_api/<doc_type>', endpoint='api/doctype',
                   handler='apps.api.handlers.CreateHandler'
                   )]).get_test_client()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    #

    def test_post_a_new_entity_without_docId_by_json(self):

        # entity 数を POST の前後で確認して保存の有無

        self.assertEqual(PEDoc.all().count(), 0)
        response = self.CLIENT.post('/_api/myDoc?_doc=%s' % self.DAT)
        self.assertEqual(PEDoc.all().count(), 1)

        # status code

        self.assertEqual(response.status_code, 200)

        # response に含まれるデータの正誤

        obj = json.loads(response.data)
        model = PEDoc.get_by_key_name(obj['_docId'])

        self.assertEqual(obj['_docId'], model.key().name())
        self.assertEqual(obj['_createdAt'], model.createdAt.isoformat())
        self.assertEqual(obj['_updatedAt'], model.updatedAt.isoformat())
        self.assertEqual(obj['docType'], 'myDoc')

        self.assertEqual(obj['boolean'], [True, False])
        self.assertEqual(obj['double'], 20.0)
        self.assertEqual(obj['string'], 'Hoge')

        # response に含まれないデータの正誤

        self.assertEqual(model.createdBy.email(), gae_test_base.LOGGED_IN_USER)
        self.assertEqual(model.updatedBy.email(), gae_test_base.LOGGED_IN_USER)
        self.assertEqual(model.schemaVersion, 1)
        self.assertEqual(model.version, 1)

    #

    def test_post_a_new_entity_with_docId_by_json(self):
        response = self.CLIENT.post('/_api/myDoc?_doc=%s'
                                    % self.DAT_WITH_DOC_ID)

        # response に含まれるデータにおいて、_docId のみ確認

        docId = json.loads(response.data)['_docId']
        self.assertEqual(docId, '1234567890abcdefghijklmnopqrstuv')

    #

    def test_post_a_existed_entity_with_docId_by_create_style_and_json(self):

        # データを新規作成

        response = self.CLIENT.post('/_api/myDoc?_doc=%s'
                                    % self.DAT_WITH_DOC_ID)

        # データを更新

        updated_response = self.CLIENT.post('/_api/myDoc?_doc=%s'
                % self.DAT_FOR_UPDATE_WITH_DOC_ID)

        # status code の確認

        self.assertEqual(updated_response.status_code, 404)

    # def test_post_without_docId_by_update_style_and_json(self):
    #     response = self.CLIENT.post('/_api/myDoc/?_doc=%s' % self.DAT)

    #

    def test_post_a_existed_entity_with_no_409_by_json(self):

        # データを新規保存

        response = self.CLIENT.post('/_api/myDoc?_doc=%s'
                                    % self.DAT_WITH_DOC_ID)
        obj = json.loads(response.data)

        # データを更新

        updated_response = \
            self.CLIENT.post('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_doc=%s'
                              % self.DAT_FOR_UPDATE)
        updated_obj = json.loads(updated_response.data)
        updated_model = PEDoc.get_by_key_name(updated_obj['_docId'])

        # status code の確認

        self.assertEqual(updated_response.status_code, 200)

        # データに変更が無いもの

        self.assertEqual(updated_obj['_createdAt'], obj['_createdAt'])
        self.assertEqual(updated_obj['_docId'],
                         '1234567890abcdefghijklmnopqrstuv')
        self.assertEqual(updated_obj['docType'], 'myDoc')

        self.assertEqual(updated_model.createdBy.email(),
                         gae_test_base.LOGGED_IN_USER)
        self.assertEqual(updated_model.updatedBy.email(),
                         gae_test_base.LOGGED_IN_USER)
        self.assertEqual(updated_model.schemaVersion, 1)
        self.assertEqual(updated_model.version, 1)

        # データに変更が有るもの

        self.assertTrue(updated_obj['_updatedAt'] > obj['_updatedAt'])
        self.assertEqual(updated_obj['boolean'], [False, True])
        self.assertEqual(updated_obj['double'], 0.3)
        self.assertEqual(updated_obj['string'], 'Hoge')

    #

    def test_put_a_existed_entity_with_no_409_by_json(self):

        # データを新規保存

        response = self.CLIENT.post('/_api/myDoc?_doc=%s'
                                    % self.DAT_WITH_DOC_ID)

        # データを更新

        updated_response = \
            self.CLIENT.put('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_doc=%s'
                             % self.DAT_FOR_UPDATE)

        # status code の確認

        self.assertEqual(updated_response.status_code, 200)

    #

    def test_post_a_new_entity_with_docId_by_update_style_and_json(self):
        response = \
            self.CLIENT.post('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_doc=%s'
                              % self.DAT)

        # status code の確認

        self.assertEqual(response.status_code, 404)

    #

    def test_put_a_new_entity_with_docId_by_json(self):
        response = \
            self.CLIENT.put('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_doc=%s'
                             % self.DAT)

        # status code の確認

        self.assertEqual(response.status_code, 404)

    #

    # def test_get_status_code_403(self):
    #     pass

    #

    def test_get_status_code_404(self):

        # _doc に値が無い場合

        response = self.CLIENT.post('/_api/myDoc?_doc')
        self.assertEqual(response.status_code, 404)
        response = \
            self.CLIENT.put('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_doc')
        self.assertEqual(response.status_code, 404)

        # _doc の値が空の場合

        response = self.CLIENT.post('/_api/myDoc?_doc=')
        self.assertEqual(response.status_code, 404)
        response = \
            self.CLIENT.put('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_doc='
                            )
        self.assertEqual(response.status_code, 404)

    #

    def test_get_status_code_409(self):

        # データを新規保存

        response = self.CLIENT.post('/_api/myDoc?_doc=%s'
                                    % self.DAT_WITH_DOC_ID)
        obj = json.loads(response.data)

        # データを割り込み更新

        interruped_response = \
            self.CLIENT.put('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_doc=%s'
                             % self.DAT_FOR_UPDATE)

        # データを更新 by _updatedAt

        dat = '{"string": "Fuga", "_updatedAt": "%s"}' % obj['_updatedAt']
        updated_response = \
            self.CLIENT.put('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_doc=%s'
                             % urllib.quote(dat))

        # status code の確認

        self.assertEqual(updated_response.status_code, 409)

        # データを更新 by _checkUpdatesAfter

        dat = '{"string": "Fuga", "_checkUpdatesAfter": "%s"}' \
            % obj['_updatedAt']
        updated_response = \
            self.CLIENT.put('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_doc=%s'
                             % urllib.quote(dat))

        # status code の確認

        self.assertEqual(updated_response.status_code, 409)

    def test_get_status_code_500(self):
        pass


if __name__ == '__main__':
    unittest.main()

