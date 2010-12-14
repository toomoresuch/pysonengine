# -*- coding: utf-8 -*-

from simplejson.encoder import JSONEncoder
from tipfy import Response
from werkzeug.exceptions import HTTPException


class JSONEncoderForHTMLEscape(JSONEncoder):

    """An encoder that produces JSON safe to embed in HTML.

    To embed JSON content in, say, a script tag on a web page, the
    characters &, < and > should be escaped. They cannot be escaped
    with the usual entities (e.g. &amp;) because they are not expanded
    within <script> tags.
    """

    def encode(self, o):

        # Override JSONEncoder.encode because it has hacks for
        # performance that make things more complicated.

        chunks = self.iterencode(o, True)
        if self.ensure_ascii:
            return ''.join(chunks)
        else:
            return u''.join(chunks)

    def iterencode(self, o, _one_shot=False):
        chunks = super(JSONEncoderForHTMLEscape, self).iterencode(o, _one_shot)
        for chunk in chunks:
            chunk = chunk.replace('&', '&amp;')
            chunk = chunk.replace('<', '&lt;')
            chunk = chunk.replace('>', '&gt;')
            yield chunk


def render_escaped_json_response(*args, **kwargs):
    """Renders a JSON response.

    :param args:
        Arguments to be passed to simplejson.dumps().
    :param kwargs:
        Keyword arguments to be passed to simplejson.dumps().
    :return:
        A :class:`Response` object with a JSON string in the body and
        mimetype set to ``application/json``.
    """

    return Response(JSONEncoderForHTMLEscape().encode(*args, **kwargs),
                    mimetype='application/json')


class ConflictError(HTTPException):

    code = 409



