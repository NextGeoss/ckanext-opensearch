# -*- coding: utf-8 -*-
"""Module adding collection search, or searching via Solr grouping."""

import logging
import json

import pysolr
from paste.deploy.converters import asbool
from paste.util.multidict import MultiDict
import six

from ckan.common import config
from ckan.lib.search.common import make_connection, SearchError,\
    SearchQueryError
import ckan.logic as logic
from ckan.logic import ValidationError
import ckan.lib.plugins as lib_plugins
from ckan.lib.search.query import VALID_SOLR_PARAMETERS, SearchQuery,\
    solr_literal
from ckan.lib.navl.dictization_functions import validate as _validate
from ckan.logic import check_access as _check_access
from ckan import plugins
import ckan.authz as authz

from .config import GROUP_FIELD

VALID_SOLR_PARAMETERS.add('group')
VALID_SOLR_PARAMETERS.add('group.field')
VALID_SOLR_PARAMETERS.add('group.limit')
VALID_SOLR_PARAMETERS.add('group.ngroups')
VALID_SOLR_PARAMETERS.add('group.facet')

QUERY_FIELDS = "name^4 title^4 tags^2 groups^2 text"

log = logging.getLogger(__name__)

_open_licenses = None


def collection_search(context, data_dict):
    """
    Search for groups of packages satisfying a given search criteria.

    Refer to package_search's documentation for more information. Grouping
    Solr results isn't supported by CKAN, so the code below makes several
    changes and omits some things that aren't necessary for our OpenSearch
    results.
    """
    # sometimes context['schema'] is None
    schema = (context.get('schema') or
              logic.schema.default_package_search_schema())
    data_dict, errors = _validate(data_dict, schema, context)
    # put the extras back into the data_dict so that the search can
    # report needless parameters
    data_dict.update(data_dict.get('__extras', {}))
    data_dict.pop('__extras', None)
    if errors:
        raise ValidationError(errors)

    user = context.get('user')

    _check_access('package_search', context, data_dict)

    # Move ext_ params to extras and remove them from the root of the search
    # params, so they don't cause and error
    data_dict['extras'] = data_dict.get('extras', {})
    for key in [key for key in data_dict.keys() if key.startswith('ext_')]:
        data_dict['extras'][key] = data_dict.pop(key)

    # check if some extension needs to modify the search params
    for item in plugins.PluginImplementations(plugins.IPackageController):
        data_dict = item.before_search(data_dict)

    # the extension may have decided that it is not necessary to perform
    # the query
    abort = data_dict.get('abort_search', False)

    if data_dict.get('sort') in (None, 'rank'):
        data_dict['sort'] = 'score desc, metadata_modified desc'

    results = []
    if not abort:
        if asbool(data_dict.get('use_default_schema')):
            data_source = 'data_dict'
        else:
            data_source = 'validated_data_dict'
        data_dict.pop('use_default_schema', None)

        result_fl = data_dict.get('fl')
        if not result_fl:
            data_dict['fl'] = 'id {0}'.format(data_source)
        else:
            data_dict['fl'] = ' '.join(result_fl)

        # Remove before these hit solr FIXME: whitelist instead
        include_private = asbool(data_dict.pop('include_private', False))
        include_drafts = asbool(data_dict.pop('include_drafts', False))
        data_dict.setdefault('fq', '')
        if not include_private:
            data_dict['fq'] = '+capacity:public ' + data_dict['fq']
        if include_drafts:
            data_dict['fq'] += ' +state:(active OR draft)'

        # Pop these ones as Solr does not need them
        data_dict.pop('extras', None)

        # enforce permission filter based on user
        if context.get('ignore_auth') or (user and authz.is_sysadmin(user)):
            labels = None
        else:
            labels = (lib_plugins.get_permission_labels()
                      .get_user_dataset_labels(context['auth_user_obj']))

        # Here's where we diverge...

        data_dict['facet.field'] = ['tags']

        data_dict['group'] = 'true'
        data_dict['group.field'] = GROUP_FIELD
        data_dict['group.limit'] = '1'
        data_dict['group.ngroups'] = 'true'
        data_dict['group.facet'] = 'false'
        query = CollectionSearchQuery()
        results = query.run(data_dict, permission_labels=labels)

        results_count = results['count']
        results_list = process_grouped_results(results['results'])

    search_results = {
        'count': results_count,
        'results': results_list,
    }

    return search_results


def process_grouped_results(results):
    """Convert grouped results into dictionaries that we can work with."""
    processed_results = []

    # This is a hack to ensure that we have something for the atom:published
    # and atom:updated elements for the collection results. Each collection
    # should have its own published and updated timestamp and they should
    # either reflect the when the collection was first published on the source
    # site or on the data hub and when the collection was last updated (e.g,
    # date of the last change to any product in the collection). It's not clear
    # which values we should use and we don't have access to that info in the
    # current version, hence the hack for now.
    published = '2018-01-16T00:00:00Z'
    updated = '2018-01-16T12:35:22Z'

    for i in results:
        dataset_json = i['doclist']['docs'][0]['validated_data_dict']
        dataset_dict = json.loads(dataset_json)
        dataset_dict['extras'] = convert_string_extras(dataset_dict['extras'])
        processed_results.append(
            {'collection_name': get_from_extras(dataset_dict,
                                                'collection_name',
                                                dataset_dict['title']),
             'collection_count': i['doclist']['numFound'],
             'collection_id': get_from_extras(dataset_dict, 'collection_id',
                                              dataset_dict['title']),
             'collection_description': dataset_dict['notes'],
             'collection_title': get_from_extras(dataset_dict,
                                                 'collection_name',
                                                 dataset_dict['title']),
             'collection_published': published,
             'collection_updated': updated,
             'is_collection': True}
        )

    return processed_results


def get_from_extras(data_dict, key, alt_value):
    """Return the value of an extra or the alt_value if it doesn't exist."""
    extras = data_dict.get('extras')

    for extra in extras:
        if extra['key'] == key:
            return extra['value']

    return alt_value


class CollectionSearchQuery(SearchQuery):
    """Create a Solr search query for collection/grouped search."""

    def get_all_entity_ids(self, max_results=1000):
        """Return a list of the IDs of all indexed packages."""
        query = "*:*"
        fq = "+site_id:\"%s\" " % config.get('ckan.site_id')
        fq += "+state:active "

        conn = make_connection()
        data = conn.search(query, fq=fq, rows=max_results, fields='id')
        return [r.get('id') for r in data.docs]

    def get_index(self, reference):
        """Check this method: it may not be necessary."""
        query = {
            'rows': 1,
            'q': 'name:"%s" OR id:"%s"' % (reference, reference),
            'wt': 'json',
            'fq': 'site_id:"%s"' % config.get('ckan.site_id')}

        conn = make_connection(decode_dates=False)
        log.debug('Package query: %r' % query)
        try:
            solr_response = conn.search(**query)
        except pysolr.SolrError, e:
            raise SearchError('SOLR returned an error running query: %r Error: %r' %  # noqa: E501
                              (query, e))

        if solr_response.hits == 0:
            raise SearchError('Dataset not found in the search index: %s' % reference)  # noqa: E501
        else:
            return solr_response.docs[0]

    def run(self, query, permission_labels=None, **kwargs):
        """
        Perform a dataset search using the given query.

        :param query: dictionary with keys like: q, fq, sort, rows, facet
        :type query: dict
        :param permission_labels: filter results to those that include at
            least one of these labels. None to not filter (return everything)
        :type permission_labels: list of unicode strings; or None

        :returns: dictionary with keys results and count

        May raise SearchQueryError or SearchError.
        """
        assert isinstance(query, (dict, MultiDict))
        # check that query keys are valid
        if not set(query.keys()) <= VALID_SOLR_PARAMETERS:
            invalid_params = [s for s in set(query.keys()) - VALID_SOLR_PARAMETERS]  # noqa: E501
            raise SearchQueryError("Invalid search parameters: %s" % invalid_params)  # noqa: E501

        # default query is to return all documents
        q = query.get('q')
        if not q or q == '""' or q == "''":
            query['q'] = "*:*"

        # number of results
        rows_to_return = min(1000, int(query.get('rows', 10)))
        if rows_to_return > 0:
            # #1683 Work around problem of last result being out of order
            #       in SOLR 1.4
            rows_to_query = rows_to_return + 1
        else:
            rows_to_query = rows_to_return
        query['rows'] = rows_to_query

        fq = []
        if 'fq' in query:
            fq.append(query['fq'])
        fq.extend(query.get('fq_list', []))

        # show only results from this CKAN instance
        fq.append('+site_id:%s' % solr_literal(config.get('ckan.site_id')))

        # filter for package status
        if '+state:' not in query.get('fq', ''):
            fq.append('+state:active')

        # only return things we should be able to see
        if permission_labels is not None:
            fq.append('+permission_labels:(%s)' % ' OR '.join(
                solr_literal(p) for p in permission_labels))
        query['fq'] = fq

        # faceting
        query['facet'] = query.get('facet', 'true')
        query['facet.limit'] = query.get('facet.limit', config.get('search.facets.limit', '50'))  # noqa: E501
        query['facet.mincount'] = query.get('facet.mincount', 1)

        # return the package ID and search scores
        query['fl'] = query.get('fl', 'name')

        # return results as json encoded string
        query['wt'] = query.get('wt', 'json')

        # If the query has a colon in it then consider it a fielded search
        # and do use dismax.
        def_type = query.get('defType', 'dismax')
        if ':' not in query['q'] or def_type == 'edismax':
            query['defType'] = def_type
            query['tie'] = query.get('tie', '0.1')
            # this minimum match is explained
            # http://wiki.apache.org/solr/DisMaxQParserPlugin#mm_.28Minimum_.27Should.27_Match.29
            query['mm'] = query.get('mm', '2<-1 5<80%')
            query['qf'] = query.get('qf', QUERY_FIELDS)

        conn = make_connection(decode_dates=False)
        log.debug('Package query: %r' % query)
        try:
            solr_response = conn.search(**query)
        except pysolr.SolrError, e:
            # Error with the sort parameter.  You see slightly different
            # error messages depending on whether the SOLR JSON comes back
            # or Jetty gets in the way converting it to HTML - not sure why
            #
            if e.args and isinstance(e.args[0], str):
                if "Can't determine a Sort Order" in e.args[0] or \
                        "Can't determine Sort Order" in e.args[0] or \
                        'Unknown sort order' in e.args[0]:
                    raise SearchQueryError('Invalid "sort" parameter')
            raise SearchError('SOLR returned an error running query: %r Error: %r' %  # noqa: E501
                              (query, e))

        self.count = solr_response.grouped[GROUP_FIELD]['ngroups']
        self.results = solr_response.grouped[GROUP_FIELD]['groups']

        # #1683 Filter out the last row that is sometimes out of order
        self.results = self.results[:rows_to_return]

        # get any extras and add to 'extras' dict
        for result in self.results:
            extra_keys = filter(lambda x: x.startswith('extras_'), result.keys())  # noqa: E501
            extras = {}
            for extra_key in extra_keys:
                value = result.pop(extra_key)
                extras[extra_key[len('extras_'):]] = value
            if extra_keys:
                result['extras'] = extras

        # if just fetching the id or name, return a list instead of a dict
        if query.get('fl') in ['id', 'name']:
            self.results = [r.get(query.get('fl')) for r in self.results]

        # get facets and convert facets list to a dict
        self.facets = solr_response.facets.get('facet_fields', {})
        for field, values in six.iteritems(self.facets):
            self.facets[field] = dict(zip(values[0::2], values[1::2]))

        return {'results': self.results, 'count': self.count}


def convert_string_extras(extras_list):
    """Convert extras stored as a string back into a normal extras list."""
    try:
        extras = ast.literal_eval(extras_list[0]["value"])
        assert type(extras) == list
        return extras
    except:
        return extras_list
