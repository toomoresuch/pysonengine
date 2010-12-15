# -*- coding: utf-8 -*-

"""
    models
    ~~~~~~~~

    PEDoc.

    :copyright: 2010 by toomore_such project.
    :license: MIT, see LICENSE for more details.
"""

import random
import string

from google.appengine.ext import db
from tipfy.ext.db import JsonProperty, retry_on_timeout
from werkzeug.exceptions import abort

from my_utils import ConflictError


class PEDoc(db.Model):

    REMOVE_KEYS_FROM_DOC_VALUES = ('_docId', '_createdAt', '_updatedAt',
                                   'docType', '_checkUpdatesAfter')

    # not jsonize, and auto.

    createdBy = db.UserProperty(auto_current_user_add=True)
    updatedBy = db.UserProperty(auto_current_user=True)
    schemaVersion = db.IntegerProperty(default=1)
    version = db.IntegerProperty(default=1)

    # auto.

    createdAt = db.DateTimeProperty(auto_now_add=True)
    updatedAt = db.DateTimeProperty(auto_now=True)

    # no auto.

    docType = db.StringProperty(required=True)
    docValues = JsonProperty()

    #

    @classmethod
    def _generate_uuid(cls, n):
        alphabets = string.digits + string.letters
        seed = [random.choice(alphabets) for i in range(n)]
        return ''.join(seed)

    @classmethod
    def _get_or_generate_key_name(cls, doc_values):
        try:
            key_name = doc_values['_docId']  # if _docId is existed,
        except KeyError:
            key_name = cls._generate_uuid(32)
        return key_name

    @classmethod
    def _remove_keys_from_doc_values(cls, doc_values, touple):
        for i in touple:
            try:
                doc_values.pop(i)
            except KeyError:
                pass
        return doc_values

    @classmethod
    def _update_model(cls, model, doc_values):
        model.docValues.update(doc_values)
        model.put()

    @classmethod
    def _convert_dict(cls, model):
        base = {
            '_docId': model.key().name(),
            '_createdAt': model.createdAt.isoformat(),
            '_updatedAt': model.updatedAt.isoformat(),
            'docType': model.docType,
            }
        model.docValues.update(base)
        return model.docValues

    @classmethod
    def create_and_get_by_dict(
        cls,
        key_name,
        doc_type,
        doc_values,
        ):

        # _docId = key_name で一意を判断する。
        # ただし、万が一、同一 key_name が発生しないよう、get_by_key_name でチェック

        if key_name is None:
            key_name = cls._get_or_generate_key_name(doc_values)

        doc = cls._remove_keys_from_doc_values(doc_values,
                cls.REMOVE_KEYS_FROM_DOC_VALUES)

        try:
            cls.get_or_insert(key_name=key_name, docType=doc_type,
                              docValues=doc)  # create.
        except db.TransactionFailedError:
            abort(500)

        model = cls.get_by_key_name(key_name)
        return cls._convert_dict(model)

    @classmethod
    def _is_updated(cls, key_name, doc_values):
        try:
            updated_at = doc_values['_updatedAt']
        except KeyError:
            try:
                updated_at = doc_values['_checkUpdatesAfter']
            except KeyError:
                updated_at = None

        model = cls.get_by_key_name(key_name)
        return updated_at and model.updatedAt.isoformat() > updated_at

    @classmethod
    def update_and_get_by_dict(
        cls,
        key_name,
        doc_type,
        doc_values,
        ):

        if cls._is_updated(key_name, doc_values):
            raise ConflictError()

        model = cls.get_by_key_name(key_name)
        doc = cls._remove_keys_from_doc_values(doc_values,
                cls.REMOVE_KEYS_FROM_DOC_VALUES)

        try:
            db.run_in_transaction(cls._update_model, model, doc)  # update.
        except db.TransactionFailedError:
            abort(500)

        model = cls.get_by_key_name(key_name)
        return cls._convert_dict(model)

    @classmethod
    def delete_in_txn(cls, key_name, updated_at):
        if cls._is_updated(key_name, {'_updatedAt': updated_at}):
            raise ConflictError()

        model = PEDoc.get_by_key_name(key_name)
        try:
            db.run_in_transaction(model.delete)  # delete.
        except db.TransactionFailedError:
            abort(500)
        except (AttributeError, db.NotSavedError):
            abort(404)



