# -*- coding: utf-8 -*-

"""
    handlers
    ~~~~~~~~

    api.

    :copyright: 2010 by toomore_such project.
    :license: MIT, see LICENSE for more details.
"""

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


class CreateHandler(BaseHandler):

    def post(self, doc_type):
        doc = self.request.args.get('_doc')

        try:
            doc_values = self._json_to_obj(doc)
        except NotFound:
            return Response(status=404)

        try:
            doc_id = doc_values['_docId']
        except KeyError:
            doc_id = None

        if doc_id and PEDoc.get_by_key_name(doc_id):
            return Response(status=404)

        try:
            result = PEDoc.create_and_get_by_dict(doc_id, doc_type, doc_values)
        except InternalServerError:
            return Response(status=500)

        return render_escaped_json_response(result)


class UpdateHandler(BaseHandler):

    def post(self, doc_type, doc_id):
        doc = self.request.args.get('_doc')

        try:
            doc_values = self._json_to_obj(doc)
        except NotFound:
            return Response(status=404)

        if PEDoc.get_by_key_name(doc_id) is None:
            return Response(status=404)

        try:
            result = PEDoc.update_and_get_by_dict(doc_id, doc_type, doc_values)
        except InternalServerError:
            return Response(status=500)
        except ConflictError:
            return Response(status=409)

        return render_escaped_json_response(result)

    def put(self, doc_type, doc_id):
        return self.post(doc_type, doc_id)


class DeleteHandler(BaseHandler):

    pass


    # def get(self, doc_type):
    #     doc = self.request.args.get('_doc')

    #     try:
    #         doc_values = self._json_to_obj(doc)
    #     except NotFound:
    #         return Response(status=404)

    #     return render_escaped_json_response(doc)


