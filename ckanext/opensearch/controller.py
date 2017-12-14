# -*- coding: utf-8 -*-
"""Contains the OpenSearch controller and methods for transforming queries."""

import importlib
from collections import OrderedDict
import logging

from lxml import etree
from webob.multidict import MultiDict, UnicodeMultiDict

from ckan.lib.base import abort, BaseController
from ckan.common import _, c, request, response
import ckan.logic as logic
import ckan.model as model

from .config import ELEMENTS, NAMESPACES, PARAMETERS, TEMPORAL_START,\
    TEMPORAL_END
from .xml_maker import make_xml
from .validator import QueryValidator
from .collection_search import collection_search

# Load the custom elements or the default elements if no custome elements
# are specified.
path_to_feed = '{}.feed'.format(ELEMENTS)
feed = importlib.import_module(path_to_feed)
Feed = feed.Feed

path_to_description_document = '{}.description_document'.format(ELEMENTS)
description_document = importlib.import_module(path_to_description_document)
DescriptionDocument = description_document.DescriptionDocument

log = logging.getLogger(__name__)


class OpenSearchController(BaseController):
    """Controller for OpenSearch queries."""

    def create_description_document(self, search_type):
        """Create the OpenSearch description document."""
        frame = [DescriptionDocument(search_type).element]
        ns_root = 'opensearch'
        content_type = 'application/opensearchdescription+xml'

        return self.prepare_response(frame, ns_root, content_type)

    def translate_os_query(self, param_dict):
        """
        Translate the OpenSearch query parameters based on a template.

        The parameters will already have been validated.
        """
        # convert params and build data dictionary
        data_dict = dict()

        data_dict['q'] = param_dict.get('q')

        rows = param_dict.get('rows')
        if not rows:
            data_dict['rows'] = 20
        else:
            data_dict['rows'] = int(rows)

        page = param_dict.get('page')
        if not page:
            page = 0
        else:
            page = int(page) - 1

        # Set the Solr start index
        data_dict['start'] = page * data_dict['rows']

        fq = ''
        for (param, value) in request.params.items():
            if param not in ['q', 'page', 'sort', 'begin', 'end'] \
                and len(value) and not param.startswith('_'):  # noqa: E125
                if not param.startswith('ext_'):
                    fq += ' %s:"%s"' % (param, value)

        if TEMPORAL_START and TEMPORAL_END:
            # Get time range
            begin = param_dict.get('begin')
            end = param_dict.get('end')

            # If begin or end are empty (e.g., "begin="), get will return an empty
            # string rather than the alternate value, so we need this second step.
            if begin or end:
                if not begin:
                    begin = '*'
                if not end:
                    end = 'NOW'

                time_range = '[{} TO {}]'.format(begin, end)
                fq += ' {}:{}'.format(TEMPORAL_START, time_range)
                fq += ' {}:{}'.format(TEMPORAL_END, time_range)

        # Add any additional facets that are necessary behind the scenes
        fq += ' +dataset_type:dataset'  # Only search datasets; no harvesters

        data_dict['fq'] = fq

        # Define the sorting method here, in case we want to change it vs.
        # the CKAN defaults
        data_dict['sort'] = 'score desc, metadata_modified desc'

        return data_dict

    def make_query_dict(self, param_dict, search_type):
        """
        Make a dictionary of parameters and values that will be used for
        the OpenSearch Query element in the response. The formatting is
        is different from the query/parameter dictionary that CKAN already
        provides, so we need to do a bit of work first to rename them
        and combine parameters that occur more than once into a single
        string.
        """
        query_dict = OrderedDict()

        query_dict['role'] = 'request'

        # XML attributes are unique per element, so parameters that occur more
        # than once in a query must me combined into a space-delimited string.
        for (param, value) in param_dict.items():
            os_name = PARAMETERS[search_type][param]['os_name']
            if os_name not in query_dict:
                query_dict[os_name] = value
            else:
                query_dict[os_name] += ' {}'.format(value)

        return query_dict

    def process_query(self, search_type):
        """
        It may be possible to hook into CKAN's standard search method
        using the `before_search` and `after_search` interfaces,
        but it appears that those hooks are only intended for modifying
        the query and results as part of the normal search process,
        (i.e., via the website or the API) rather than creating a new
        search process. Underneath, we're still executing a standard
        CKAN search. We're just using a different validation flow and
        doing something different with the results.
        """
        try:
            context = {'model': model, 'user': c.user,
                       'auth_user_obj': c.userobj}
            logic.check_access('site_read', context)
        except logic.NotAuthorized:
            abort(403, _('Not authorized to see this page'))

        # Get the query parameters and remove 'amp' if it has snuck in.
        param_dict = UnicodeMultiDict(MultiDict(), encoding='utf-8')
        for param, value in request.params.items():
            if param != 'amp':
                param_dict.add(param, value)

        # Validate the query and abort if there are errors.
        validator = QueryValidator(param_dict, PARAMETERS[search_type])
        if validator.errors:
            error_report = '</br>'.join(validator.errors)
            return abort(400, error_report)

        # Translate the query parameters into a CKAN data_dict so we
        # can query the DB.
        data_dict = self.translate_os_query(param_dict)

        # Query the DB.
        if search_type == 'dataset':
            results_dict = logic.get_action(
                'package_search')(context, data_dict)
        elif search_type == 'collection':
            results_dict = results_dict = collection_search(context, data_dict)

        results_dict['items_per_page'] = data_dict['rows']

        # Get next page, previous page and index of first element on page.
        current_page = int(param_dict.get('page', 1))
        total_results = results_dict['count']
        requested_rows = results_dict['items_per_page']
        expected_results = requested_rows * current_page

        if expected_results >= total_results:
            next_page = None
        else:
            next_page = current_page + 1
        results_dict['next_page'] = next_page

        if current_page == 1:
            previous_page = None
        else:
            previous_page = current_page - 1
        results_dict['prev_page'] = previous_page

        results_dict['start_index'] = expected_results - requested_rows + 1

        results_dict['query'] = self.make_query_dict(param_dict, search_type)

        return self.return_results(results_dict)

    def return_results(self, results):
        """Generate the XML response for successful search results errors."""
        frame = [Feed(results).element]
        ns_root = 'atom'
        content_type = 'application/atom+xml'

        return self.prepare_response(frame, ns_root, content_type)

    def prepare_response(self, frame, ns_root, content_type):
        """Prepare the response."""
        element_tree = make_xml(frame, NAMESPACES, ns_root)

        response_data = etree.tostring(
            element_tree,
            encoding='UTF-8',
            xml_declaration=True,
            pretty_print=True
        )

        return self._finish(200, response_data, content_type)

    def _finish(self, status_int, response_data, content_type):
        """
        When a controller method has completed, call this method
        to prepare the response.
        """
        response.charset = 'UTF-8'
        response.status_int = status_int
        response.headers['Content-Type'] = content_type + '; charset=UTF-8'

        return response_data
