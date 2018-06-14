# -*- coding: utf-8 -*-
"""Contains the OpenSearch controller and methods for transforming queries."""

import logging

from ckan.lib.base import (abort,
                           BaseController)
from ckan.common import (_,
                         c,
                         config,
                         request,
                         response)
import ckan.logic as logic
import ckan.model as model

from .description_document import make_description_document
from .search import make_results_feed


log = logging.getLogger(__name__)


class OpenSearchController(BaseController):
    """Controller for OpenSearch queries."""

    def check_auth_context(self):
        try:
            context = {'model': model, 'user': c.user,
                       'auth_user_obj': c.userobj}
            if not config.get('testing'):
                logic.check_access('site_read', context)
        except logic.NotAuthorized:
            abort(403, _('Not authorized to see this page'))

        if not c.userobj.about == "true":
            abort(403, _('Not authorized to see this page'))

        return context

    def return_description_document(self):
        """Return a description document based on the query."""
        self.check_auth_context()

        request_url = request.url
        params = request.params

        description_document = make_description_document(params, request_url)
        content_type = 'application/opensearchdescription+xml'

        return self._finish(200, description_document, content_type)

    def return_search_results(self, search_type):
        """Execute a search and return the results as an Atom feed."""
        context = self.check_auth_context()

        request_url = request.url
        params = request.params

        search_type = params.get('collection_id', search_type)

        results_feed = make_results_feed(search_type, params, request_url,
                                         context)
        content_type = 'application/atom+xml'

        return self._finish(200, results_feed, content_type)

    def _finish(self, status_int, response_data, content_type):
        """Prepare the response once the controller method has finished."""
        response.charset = 'UTF-8'
        response.status_int = status_int
        response.headers['Content-Type'] = content_type + '; charset=UTF-8'

        return response_data
