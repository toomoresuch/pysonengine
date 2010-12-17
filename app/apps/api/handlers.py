# -*- coding: utf-8 -*-

"""
    handlers
    ~~~~~~~~

    api.

    :copyright: 2010 by toomore_such project.
    :license: MIT, see LICENSE for more details.
"""

import logging
import simplejson as json

from google.appengine.ext import db
from tipfy import RequestHandler, Response, render_json_response
from werkzeug.exceptions import InternalServerError, NotFound

from apps.api.models import PEDoc
from my_utils import render_escaped_json_response, ConflictError


class BaseHandler(RequestHandler):

    def _json_to_obj(self, doc):
        try:
            doc_values = json.loads(doc)
        except (TypeError, json.decoder.JSONDecodeError):
            self.abort(404)

        return doc_values

    def _get_doc_values(self, request):
        if self.request.is_xhr:
            doc_values = self.request.values.to_dict()
        else:
            try:
                doc = self.request.values.to_dict()['_doc']
                try:
                    doc_values = self._json_to_obj(doc)
                except NotFound:
                    self.abort(404)
            except AttributeError:
                self.abort(404)

        return doc_values

    def _get_doc_values_and_id(self, request):
        doc_values = self._get_doc_values(request)

        try:
            doc_id = doc_values['_docId']
        except KeyError:
            doc_id = None

        return (doc_values, doc_id)

    def _after(
        self,
        doc_id,
        doc_type,
        doc_values,
        ):

        if doc_id and PEDoc.get_by_key_name(doc_id):
            try:
                result = PEDoc.update_and_get_by_dict(doc_id, doc_type,
                        doc_values)
            except ConflictError:
                return Response(status=409)
            except InternalServerError:
                return Response(status=500)
        else:
            try:
                result = PEDoc.create_and_get_by_dict(doc_id, doc_type,
                        doc_values)
            except InternalServerError:
                return Response(status=500)

        return render_escaped_json_response(result)


class ByDocTypeHandler(BaseHandler):

    def post(self, doc_type):
        try:
            (doc_values, doc_id) = self._get_doc_values_and_id(self.request)
        except NotFound:
            return Response(status=404)

        return self._after(doc_id, doc_type, doc_values)

    def put(self, doc_type):
        try:
            (doc_values, doc_id) = self._get_doc_values_and_id(self.request)
        except NotFound:
            return Response(status=404)

        if doc_id and PEDoc.get_by_key_name(doc_id) is None:
            return Response(status=404)

        return self._after(doc_id, doc_type, doc_values)

    def get(self, doc_type):
        models = PEDoc.gql('WHERE docType = :1', doc_type)

        try:
            result = {doc_type: [PEDoc.convert_dict(i) for i in models]}
        except AttributeError:
            result = {}

        return render_escaped_json_response(result)


class ByDocIdHandler(BaseHandler):

    def post(self, doc_type, doc_id):
        if self.request.args.get('_method') == 'delete':
            return self.delete(doc_type, doc_id)

        try:
            doc_values = self._get_doc_values(self.request)
        except NotFound:
            return Response(status=404)

        return self._after(doc_id, doc_type, doc_values)

    def put(self, doc_type, doc_id):
        if PEDoc.get_by_key_name(doc_id) is None:
            return Response(status=404)

        try:
            doc_values = self._get_doc_values(self.request)
        except NotFound:
            return Response(status=404)

        return self._after(doc_id, doc_type, doc_values)

    def delete(self, doc_type, doc_id):
        updated_at = self.request.args.get('_checkUpdatesAfter')
        if updated_at is None:
            updated_at = self.request.args.get('_updatedAt')

        try:
            result = PEDoc.delete_in_txn(doc_id, updated_at)
        except NotFound:
            return Response(status=404)
        except ConflictError:
            return Response(status=409)
        except InternalServerError:
            return Response(status=500)

        return Response(status=200)

    def get(self, doc_type, doc_id):
        model = PEDoc.get_by_key_name(doc_id)

        try:
            result = PEDoc.convert_dict(model)
        except AttributeError:
            return Response(status=404)

        return render_escaped_json_response(result)



