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
    SEED_FOR_UP_B = '{"boolean": [false, true]%s}'
    SEED_FOR_UP_D = '{"double": 3e-1%s}'
    SEED_FOR_UP_S = '{"string": "Fuga"%s}'

    DAT = urllib.quote(SEED % '')
    DAT_WITH_DOC_ID = urllib.quote(SEED % DOC_ID)

    DAT_FOR_UP_B = urllib.quote(SEED_FOR_UP_B % '')
    DAT_FOR_UP_D = urllib.quote(SEED_FOR_UP_D % '')
    DAT_FOR_UP_S = urllib.quote(SEED_FOR_UP_S % '')
    DAT_FOR_UP_B_WITH_DOC_ID = urllib.quote(SEED_FOR_UP_B % DOC_ID)
    DAT_FOR_UP_D_WITH_DOC_ID = urllib.quote(SEED_FOR_UP_D % DOC_ID)
    DAT_FOR_UP_S_WITH_DOC_ID = urllib.quote(SEED_FOR_UP_S % DOC_ID)

    CLIENT = Tipfy(rules=[Rule('/_api/<doc_type>/<doc_id>',
                   endpoint='api/doctype/docid',
                   handler='apps.api.handlers.RestfulHandler'),
                   Rule('/_api/<doc_type>', endpoint='api/doctype',
                   handler='apps.api.handlers.CreateHandler'
                   )]).get_test_client()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    # ---------------------------------------- #
    # ---------------------------------------- #

    def _assert_create(self, response):

        # status code の確認

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

    # ---------------------------------------- #

    def test_success_post_a_new_entity_by_json(self):

        # entity 数を POST の前後で確認して保存の有無

        self.assertEqual(PEDoc.all().count(), 0)
        response = self.CLIENT.post('/_api/myDoc?_doc=%s' % self.DAT)
        self.assertEqual(PEDoc.all().count(), 1)
        self._assert_create(response)

        # with _docId.

        response_with_doc_id = self.CLIENT.post('/_api/myDoc?_doc=%s'
                % self.DAT_WITH_DOC_ID)
        self._assert_create(response_with_doc_id)

        # response に含まれるデータにおいて、_docId のみ確認

        doc_id = json.loads(response_with_doc_id.data)['_docId']
        self.assertEqual(doc_id, '1234567890abcdefghijklmnopqrstuv')

        # update syntax

        update_syntax_response = \
            self.CLIENT.post('/_api/myDoc/vutsrqponmlkjihgfedcba0987654321?_doc=%s'
                              % self.DAT)
        self._assert_create(update_syntax_response)

        # response に含まれるデータにおいて、_docId のみ確認

        doc_id_up = json.loads(update_syntax_response.data)['_docId']
        self.assertEqual(doc_id_up, 'vutsrqponmlkjihgfedcba0987654321')

    # ---------------------------------------- #
    # ---------------------------------------- #

    # def test_post_without_docId_by_update_style_and_json(self):
    #     response = self.CLIENT.post('/_api/myDoc/?_doc=%s' % self.DAT)
    #     pass

    def _assert_update(
        self,
        first_response,
        second_response,
        key,
        value,
        ):

        # status code の確認

        self.assertEqual(second_response.status_code, 200)

        # データに変更が無いもの

        obj = json.loads(first_response.data)
        updated_obj = json.loads(second_response.data)
        updated_model = PEDoc.get_by_key_name(updated_obj['_docId'])

        self.assertEqual(updated_obj['_createdAt'], obj['_createdAt'])
        self.assertEqual(updated_obj['_docId'], obj['_docId'])
        self.assertEqual(updated_obj['docType'], 'myDoc')

        self.assertEqual(updated_model.createdBy.email(),
                         gae_test_base.LOGGED_IN_USER)
        self.assertEqual(updated_model.updatedBy.email(),
                         gae_test_base.LOGGED_IN_USER)
        self.assertEqual(updated_model.schemaVersion, 1)
        self.assertEqual(updated_model.version, 1)

        # データに変更が有るもの

        self.assertTrue(updated_obj['_updatedAt'] > obj['_updatedAt'])
        self.assertEqual(updated_obj[key], value)

    # ---------------------------------------- #

    def test_success_post_and_put_a_existed_entity_by_json(self):

        # データを新規保存

        response = self.CLIENT.post('/_api/myDoc?_doc=%s'
                                    % self.DAT_WITH_DOC_ID)

        # データを更新 create syntax

        create_syntax_response = self.CLIENT.post('/_api/myDoc?_doc=%s'
                % self.DAT_FOR_UP_B_WITH_DOC_ID)
        self._assert_update(response, create_syntax_response, 'boolean',
                            [False, True])

        # データを更新 update syntax

        update_syntax_response = \
            self.CLIENT.post('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_doc=%s'
                              % self.DAT_FOR_UP_D)
        self._assert_update(response, update_syntax_response, 'double', 0.3)

        # データを更新 put

        put_response = \
            self.CLIENT.put('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_doc=%s'
                             % self.DAT_FOR_UP_S)
        self._assert_update(response, put_response, 'string', 'Fuga')

    # ---------------------------------------- #
    # ---------------------------------------- #

    def test_success_delete_a_existed_entity_by_json(self):

        # データを新規保存 & 削除

        self.CLIENT.post('/_api/myDoc?_doc=%s' % self.DAT_WITH_DOC_ID)
        response = \
            self.CLIENT.put('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_method=delete'
                            )

        # status code の確認 & データの削除を確認

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PEDoc.get_by_key_name('1234567890abcdefghijklmnopqrstuv'
                         ), None)

        # データを新規保存 & 削除

        self.CLIENT.post('/_api/myDoc?_doc=%s' % self.DAT_WITH_DOC_ID)
        response = \
            self.CLIENT.delete('/_api/myDoc/1234567890abcdefghijklmnopqrstuv')

        # status code の確認 & データの削除を確認

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PEDoc.get_by_key_name('1234567890abcdefghijklmnopqrstuv'
                         ), None)

    # ---------------------------------------- #
    # ---------------------------------------- #

    def test_get_status_code_403(self):
        pass

    # ---------------------------------------- #
    # ---------------------------------------- #

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

        # 新規 entity を PUT した場合

        response = \
            self.CLIENT.put('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_doc=%s'
                             % self.DAT)
        self.assertEqual(response.status_code, 404)

        # 新規 entity を DELETE した場合

        response = \
            self.CLIENT.delete('/_api/myDoc/1234567890abcdefghijklmnopqrstuv')
        self.assertEqual(response.status_code, 404)

    # ---------------------------------------- #
    # ---------------------------------------- #

    def test_get_status_code_409(self):

        # データを新規保存 & データを割り込み更新

        response = self.CLIENT.post('/_api/myDoc?_doc=%s'
                                    % self.DAT_WITH_DOC_ID)
        obj = json.loads(response.data)
        interruped_response = \
            self.CLIENT.put('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_doc=%s'
                             % self.DAT_FOR_UP_B)

        # データを更新 by _updatedAt & status code の確認

        dat = '{"string": "Fuga", "_updatedAt": "%s"}' % obj['_updatedAt']
        updated_response = \
            self.CLIENT.put('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_doc=%s'
                             % urllib.quote(dat))
        self.assertEqual(updated_response.status_code, 409)

        # データを更新 by _checkUpdatesAfter & status code の確認

        dat = '{"string": "Fuga", "_checkUpdatesAfter": "%s"}' \
            % obj['_updatedAt']
        updated_response = \
            self.CLIENT.put('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_doc=%s'
                             % urllib.quote(dat))
        self.assertEqual(updated_response.status_code, 409)

        # データを削除 by _updatedAt & status code の確認

        response = \
            self.CLIENT.delete('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_updatedAt=%s'
                                % obj['_updatedAt'])
        self.assertEqual(updated_response.status_code, 409)

        # データを削除 by _checkUpdatesAfter & status code の確認

        response = \
            self.CLIENT.delete('/_api/myDoc/1234567890abcdefghijklmnopqrstuv?_checkUpdatesAfter=%s'
                                % obj['_updatedAt'])
        self.assertEqual(updated_response.status_code, 409)

    # ---------------------------------------- #
    # ---------------------------------------- #

    def test_get_status_code_500(self):
        pass


if __name__ == '__main__':
    unittest.main()

