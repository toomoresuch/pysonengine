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
from tipfy.ext.acl import Acl, AclRules
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError
from apps.api.models import PEDoc, AclRulesPlus
from my_utils import render_escaped_json_response, ConflictError, \
    required_admin_role


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


class DocHandler(BaseHandler):

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


class DocByDocTypeHandler(DocHandler):

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
            return Response(status=404)

        return render_escaped_json_response(result)


class DocByDocIdHandler(DocHandler):

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


class ACLHandler(BaseHandler):

    def _flatten_doc_values(self, docs):
        doc_values = {}
        for i in docs:
            try:
                doc_values.update(i)
            except ValueError:
                self.abort(404)

        return doc_values

    def _admins(self, acls):
        return frozenset([i.user for i in acls if Acl(i.area,
                         i.user).is_one('admin')])

    def _members(self, doc_values):
        return frozenset([key for key in doc_values.keys() if doc_values[key]
                         != 'admin'])

    def _has_admin(self, doc_values):
        return True in [doc_values[key] == 'admin' for key in doc_values.keys()]

    def _400(self):
        return Response(response='{"error": "No Admin"}', status=400,
                        mimetype='application/json')


class ACLforDocTypeHandler(ACLHandler):

    def post(self, doc_type):
        acls_count = AclRulesPlus.get_by_area(doc_type).count()

        @required_admin_role(doc_type, acls_count)
        def inner():
            try:
                docs = self._get_doc_values(self.request)
                doc_values = self._flatten_doc_values(docs)
            except NotFound:
                return Response(status=404)

            acls = AclRulesPlus.get_by_area(doc_type)
            no_admin = self._has_admin(doc_values) is False
            if acls.count() == 0:
                if no_admin:
                    return self._400()
            else:
                if no_admin and self._members(doc_values) >= self._admins(acls):
                    return self._400()

            for key in doc_values.keys():
                AclRules.insert_or_update(doc_type, key, [doc_values[key]])
            result = {doc_type: AclRulesPlus.get_by_list(doc_type)}

            return render_escaped_json_response(result)
        return inner()

    def put(self, doc_type):

        @required_admin_role(doc_type)
        def inner():
            acls = AclRulesPlus.get_by_area(doc_type)
            if acls.count() == 0:
                return Response(status=404)

            return self.post(doc_type)
        return inner()

    def delete(self, doc_type):
        pass

    def get(self, doc_type):
        return Response(response='{"error": "No Admin"}', status=400,
                        mimetype='application/json')



