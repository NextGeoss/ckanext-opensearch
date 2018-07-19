# -*- coding: utf-8 -*-
"""
Contains functions for executing OpenSearch queries and returning Atom results.
"""

from collections import OrderedDict
from datetime import datetime
import math
import re

from webob.multidict import (MultiDict,
                             UnicodeMultiDict)

from ckan.lib.base import (abort,
                           render)
import ckan.logic as logic

from .collection_search import collection_search
from .config import (NAMESPACES,
                     PARAMETERS,
                     TEMPORAL_START,
                     TEMPORAL_END,
                     SHORT_NAME,
                     SITE_URL)
from .validator import QueryValidator

from ckan.common import config
import ast


def translate_os_query(param_dict):
    """
    Translate the OpenSearch query parameters based on a template.

    The parameters will already have been validated.
    """
    # convert params and build data dictionary
    data_dict = dict()

    data_dict['q'] = param_dict.get('q', '')

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
    for (param, value) in param_dict.items():
        skip = ['q', 'page', 'sort', 'begin', 'end', 'rows',
                'date_modified']
        if param not in skip and len(value) and not param.startswith('_'):
            if not param.startswith('ext_'):
                fq += ' %s:"%s"' % (param, value)

    # Temporal search across a start time field and an end time field
    if TEMPORAL_START and TEMPORAL_END:
        # Get time range
        begin = param_dict.get('begin')
        end = param_dict.get('end')

        # If begin or end are empty (e.g., "begin="), get will return an
        # empty string rather than the alternate value,
        # so we need this second step.
        if begin or end:
            if not begin:
                begin = '*'
            if not end:
                end = 'NOW'

            time_range = '[{} TO {}]'.format(begin, end)
            fq += ' {}:{}'.format(TEMPORAL_START, time_range)
            fq += ' {}:{}'.format(TEMPORAL_END, time_range)

    # Temporal search across metadata_modified
    date_modified = param_dict.get('date_modified')
    # Format: [YYYY-MM-DDTHH:MM:SS,YYYY-MM-DDTHH:MM:SS]
    if date_modified:
        begin = '{}Z'.format(date_modified[1:20])
        end = '{}Z'.format(date_modified[21:-1])
        time_range = '[{} TO {}]'.format(begin, end)
        fq += ' {}:{}'.format('metadata_modified', time_range)

    # Add geometry spatial filter (only works with Solr spatial field)
    geometry = param_dict.get('ext_geometry', None)
    if geometry:
        # Validate the polygon
        geometry_filter = ' +spatial_geom:"Intersects({})"'.format(geometry)  # noqa: E501
        fq += geometry_filter

    # Add any additional facets that are necessary behind the scenes
    fq += ' +dataset_type:dataset'  # Only search datasets; no harvesters

    data_dict['fq'] = fq

    data_dict['ext_bbox'] = param_dict.get('ext_bbox')

    # Define the sorting method here, in case we want to change it vs.
    # the CKAN defaults
    data_dict['sort'] = 'score desc, metadata_modified desc'
    return data_dict


def make_query_dict(param_dict, search_type):
    """
    Make a dict of parames and values for Query element in the response.

    The formatting is is different from the query/parameter dictionary that
    CKAN already provides, so we need to do a bit of work first to rename
    them and combine parameters that occur more than once into a single
    string.
    """
    query_dict = OrderedDict()

    # XML attributes are unique per element, so parameters that occur more
    # than once in a query must be combined into a space-delimited string.
    for (param, value) in param_dict.items():
        if param != 'collection_id':
            os_name = PARAMETERS[search_type][param]['os_name']
            namespace = PARAMETERS[search_type][param]['namespace']
            if namespace == 'opensearch':
                os_param = os_name
            else:
                os_param = '{}:{}'.format(namespace, os_name)
            if os_param not in query_dict:
                query_dict[os_param] = value
            else:
                query_dict[os_param] += ' {}'.format(value)

    query_dict['role'] = 'request'

    return query_dict


def process_query(search_type, params, request_url, context):
    """
    Process the search query.

    It may be possible to hook into CKAN's standard search method
    using the `before_search` and `after_search` interfaces,
    but it appears that those hooks are only intended for modifying
    the query and results as part of the normal search process,
    (i.e., via the website or the API) rather than creating a new
    search process. Underneath, we're still executing a standard
    CKAN search. We're just using a different validation flow and
    doing something different with the results.
    """
    # Get the query parameters and remove 'amp' if it has snuck in.
    # Strip any parameters that aren't valid as per CEOS-BP-009B.
    param_dict = UnicodeMultiDict(MultiDict(), encoding='utf-8')
    query_url = request_url.split('?')[0] + '?'
    if search_type not in {'collection', 'dataset', 'record'}:
        c_name = '%20'.join(search_type.split(' '))  # TODO: This shouldn't be necessary anymore  # noqa: E501
        query_url += '{}={}'.format('collection_id', c_name)
    for param, value in params.items():
        if param != 'amp' and param in PARAMETERS[search_type]:
            param_dict.add(param, value)
            if query_url[-1] != '?':
                query_url += '&'
            query_url += '{}={}'.format(param, value)

    if search_type not in {'collection', 'dataset', 'record'}:
        param_dict['collection_id'] = search_type

    # Work in progress: use client_id for usage metrics
    # The client_id parameter is _not_ a search parameter,
    # so don't treat it as one.
    param_dict.pop('client_id', None)

    # Validate the query and abort if there are errors.
    validator = QueryValidator(param_dict, PARAMETERS[search_type])
    if validator.errors:
        error_report = '</br>'.join(validator.errors)
        return abort(400, error_report)

    # Translate the query parameters into a CKAN data_dict so we
    # can query the DB.
    data_dict = translate_os_query(param_dict)

    # Query the DB.
    if search_type == 'collection':
        results_dict = results_dict = collection_search(context,
                                                        data_dict)
    else:
        results_dict = logic.get_action('package_search')(context,
                                                          data_dict)
    # We'll need to refactor this. we don't want to rely on the request
    # global when creating the feed, so we're adding this info here.
    results_dict['request_url'] = request_url
    results_dict['params'] = params
    for result in results_dict['results']:
        result['request_url'] = request_url
        result['params'] = params

    results_dict['items_per_page'] = data_dict['rows']

    # Get next page, previous page and index of first element on page.
    current_page = int(param_dict.get('page') or 1)
    total_results = results_dict['count']
    requested_rows = results_dict['items_per_page']
    expected_results = requested_rows * current_page

    if expected_results >= total_results:
        next_page = None
    else:
        next_page = current_page + 1
    results_dict['next_page'] = next_page

    if current_page == 1:
        prev_page = None
    else:
        prev_page = current_page - 1
    results_dict['prev_page'] = prev_page

    last_page = int(math.ceil(total_results / float(requested_rows)))

    results_dict['namespaces'] = {'xmlns:{0}'.format(key): value
                                  for key, value
                                  in NAMESPACES.items()}
    results_dict['feed_title'] = ('{} OpenSearch Search Results'
                                  .format(SHORT_NAME))
    results_dict['feed_subtitle'] = ('{} results for your search'
                                     .format(total_results))
    results_dict['feed_id'] = request_url
    results_dict['feed_generator_attrs'] = {'version': '0.1',
                                            'uri': request_url.replace('&', '&amp;')}  # noqa: E501
    results_dict['feed_generator_content'] = ('{} search results'
                                              .format(SHORT_NAME))
    results_dict['feed_updated'] = (datetime.utcnow()
                                    .strftime('%Y-%m-%dT%H:%M:%SZ'))
    results_dict['start_index'] = expected_results - requested_rows + 1
    results_dict['query_attrs'] = make_query_dict(param_dict, search_type)
    results_dict['feed_box'] = make_feed_box(results_dict)
    results_dict['search_url'] = ('{}/opensearch/description.xml'
                                  .format(SITE_URL))
    results_dict['self_url'] = query_url
    results_dict['first_url'] = make_nav_url(query_url, 1)
    results_dict['next_url'] = make_nav_url(query_url, next_page)
    results_dict['prev_url'] = make_nav_url(query_url, prev_page)
    results_dict['last_url'] = make_nav_url(query_url, last_page)

    for result in results_dict['results']:
        result['extras'] = new_extras(result['extras'])

    return results_dict


def make_feed_box(results_dict):
    """Return the content of the GeoRSS box element for the feed."""
    bbox_param = '{http://a9.com/-/opensearch/extensions/geo/1.0/}box'
    bbox = results_dict['query_attrs'].get(bbox_param)
    if bbox:
        return bbox.replace(',', ' ')
    else:
        return '-180.0 -90.0 180.0 90.0'


def make_nav_url(query_url, page):
    """Create a navigation URL (next, prev, last, etc.)."""
    if 'page=' not in query_url:
        nav_url = '{0}&page={1}'.format(query_url, page)
    else:
        halves = re.compile('page=\d*').split(query_url)
        if len(halves) == 1:
            nav_url = '{0}&page={1}'.format(halves[0], page)
        else:
            nav_url = '{0}page={1}{2}'.format(halves[0], page, halves[1])

    return nav_url


def make_atom_feed(results_dict, search_type):
    """Convert the modified search results dictionary into Atom XML."""
    if search_type == 'collection':
        template = 'collection_results'
    else:
        template = 'search_results'

    return render('opensearch/{}.xml'.format(template),
                  extra_vars=results_dict)


def make_results_feed(search_type, params, request_url, context):
    """Process the query and return the results feed."""
    results_dict = process_query(search_type, params, request_url, context)

    return make_atom_feed(results_dict, search_type)


def new_extras(package_extras, auto_clean=False, subs=None, exclude=None):
    """Necessary because we're storing them as a string."""

    # If exclude is not supplied use values defined in the config
    if not exclude:
        exclude = config.get('package_hide_extras', [])
    output = []
    for extra in sorted(package_extras, key=lambda x: x['key']):
        if extra.get('state') == 'deleted':
            continue
        extras_tmp = ast.literal_eval(extra['value'])

        for ext in extras_tmp:
            k, v = ext['key'], ext['value']
            if k in exclude:
                continue
            if subs and k in subs:
                k = subs[k]
            elif auto_clean:
                k = k.replace('_', ' ').replace('-', ' ').title()
            if isinstance(v, (list, tuple)):
                v = ", ".join(map(unicode, v))
            output.append((k, v))
    return output
