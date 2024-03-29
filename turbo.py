from aiohttp import web


class Turbo:

    def requested_frame(self, request: web.Request):
        """Returns the target frame the client expects, or ``None``."""
        return request.headers.get("Turbo-Frame")

    def can_stream(self, request: web.Request):
        """Returns ``True`` if the client accepts turbo stream responses."""
        stream_mimetype = "text/vnd.turbo-stream.html"
        return stream_mimetype in request.headers.get("Accept", "")

    def _make_stream(self, action, content, target):
        stream = f'<turbo-stream action="{action}" target="{target}">'
        if content:
            stream += f"<template>{content}</template>"
        stream += "</turbo-stream>"
        return stream

    def append(self, content, target):
        """Create an append stream.

        :param content: the HTML content to include in the stream.
        :param target: the target ID for this change.
        """
        return self._make_stream("append", content, target)

    def prepend(self, content, target):
        """Create a prepend stream.

        :param content: the HTML content to include in the stream.
        :param target: the target ID for this change.
        """
        return self._make_stream("prepend", content, target)

    def replace(self, content, target):
        """Create a replace stream.

        :param content: the HTML content to include in the stream.
        :param target: the target ID for this change.
        """
        return self._make_stream("replace", content, target)

    def update(self, content, target):
        """Create an update stream.

        :param content: the HTML content to include in the stream.
        :param target: the target ID for this change.
        """
        return self._make_stream("update", content, target)

    def remove(self, target):
        """Create a remove stream.

        :param target: the target ID for this change.
        """
        return self._make_stream("remove", "", target)

    def after(self, content, target):
        """Create an after stream.

        :param content: the HTML content to include in the stream.
        :param target: the target ID for this change.
        """
        return self._make_stream("after", content, target)

    def before(self, content, target):
        """Create an before stream.

        :param content: the HTML content to include in the stream.
        :param target: the target ID for this change.
        """
        return self._make_stream("before", content, target)

    def stream(self, stream):
        """Create a turbo stream response.

        :param stream: one or a list of streamed responses generated by the
                       ``append()``, ``prepend()``, ``replace()``, ``update()``
                       and ``remove()`` methods.
        """
        return web.Response(
            body="".join(stream), content_type="text/vnd.turbo-stream.html"
        )
