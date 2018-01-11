import logging
import json

from ckan.common import config
import pysolr
from paste.deploy.converters import asbool
from paste.util.multidict import MultiDict
import six

from ckan.lib.search.common import make_connection, SearchError, SearchQueryError
import ckan.logic as logic
import ckan.model as model
import ckan.lib.plugins as lib_plugins

import ckan.lib.helpers as h
from ckan.common import OrderedDict, _

from ckan.lib.search.query import VALID_SOLR_PARAMETERS, SearchQuery, solr_literal
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
    '''
    Searches for packages satisfying a given search criteria.

    This action accepts solr search query parameters (details below), and
    returns a dictionary of results, including dictized datasets that match
    the search criteria, a search count and also facet information.

    **Solr Parameters:**

    For more in depth treatment of each paramter, please read the `Solr
    Documentation <http://wiki.apache.org/solr/CommonQueryParameters>`_.

    This action accepts a *subset* of solr's search query parameters:


    :param q: the solr query.  Optional.  Default: ``"*:*"``
    :type q: string
    :param fq: any filter queries to apply.  Note: ``+site_id:{ckan_site_id}``
        is added to this string prior to the query being executed.
    :type fq: string
    :param sort: sorting of the search results.  Optional.  Default:
        ``'relevance asc, metadata_modified desc'``.  As per the solr
        documentation, this is a comma-separated string of field names and
        sort-orderings.
    :type sort: string
    :param rows: the number of matching rows to return. There is a hard limit
        of 1000 datasets per query.
    :type rows: int
    :param start: the offset in the complete result for where the set of
        returned datasets should begin.
    :type start: int
    :param facet: whether to enable faceted results.  Default: ``True``.
    :type facet: string
    :param facet.mincount: the minimum counts for facet fields should be
        included in the results.
    :type facet.mincount: int
    :param facet.limit: the maximum number of values the facet fields return.
        A negative value means unlimited. This can be set instance-wide with
        the :ref:`search.facets.limit` config option. Default is 50.
    :type facet.limit: int
    :param facet.field: the fields to facet upon.  Default empty.  If empty,
        then the returned facet information is empty.
    :type facet.field: list of strings
    :param include_drafts: if ``True``, draft datasets will be included in the
        results. A user will only be returned their own draft datasets, and a
        sysadmin will be returned all draft datasets. Optional, the default is
        ``False``.
    :type include_drafts: boolean
    :param include_private: if ``True``, private datasets will be included in
        the results. Only private datasets from the user's organizations will
        be returned and sysadmins will be returned all private datasets.
        Optional, the default is ``False``.
    :param use_default_schema: use default package schema instead of
        a custom schema defined with an IDatasetForm plugin (default: False)
    :type use_default_schema: bool


    The following advanced Solr parameters are supported as well. Note that
    some of these are only available on particular Solr versions. See Solr's
    `dismax`_ and `edismax`_ documentation for further details on them:

    ``qf``, ``wt``, ``bf``, ``boost``, ``tie``, ``defType``, ``mm``


    .. _dismax: http://wiki.apache.org/solr/DisMaxQParserPlugin
    .. _edismax: http://wiki.apache.org/solr/ExtendedDisMax


    **Examples:**

    ``q=flood`` datasets containing the word `flood`, `floods` or `flooding`
    ``fq=tags:economy`` datasets with the tag `economy`
    ``facet.field=["tags"] facet.limit=10 rows=0`` top 10 tags

    **Results:**

    The result of this action is a dict with the following keys:

    :rtype: A dictionary with the following keys
    :param count: the number of results found.  Note, this is the total number
        of results found, not the total number of results returned (which is
        affected by limit and row parameters used in the input).
    :type count: int
    :param results: ordered list of datasets matching the query, where the
        ordering defined by the sort parameter used in the query.
    :type results: list of dictized datasets.
    :param facets: DEPRECATED.  Aggregated information about facet counts.
    :type facets: DEPRECATED dict
    :param search_facets: aggregated information about facet counts.  The outer
        dict is keyed by the facet field name (as used in the search query).
        Each entry of the outer dict is itself a dict, with a "title" key, and
        an "items" key.  The "items" key's value is a list of dicts, each with
        "count", "display_name" and "name" entries.  The display_name is a
        form of the name that can be used in titles.
    :type search_facets: nested dict of dicts.

    An example result: ::

     {'count': 2,
      'results': [ { <snip> }, { <snip> }],
      'search_facets': {u'tags': {'items': [{'count': 1,
                                             'display_name': u'tolstoy',
                                             'name': u'tolstoy'},
                                            {'count': 2,
                                             'display_name': u'russian',
                                             'name': u'russian'}
                                           ]
                                 }
                       }
     }

    **Limitations:**

    The full solr query language is not exposed, including.

    fl
        The parameter that controls which fields are returned in the solr
        query.
        fl can be  None or a list of result fields, such as ['id', 'extras_custom_field'].
        if fl = None, datasets are returned as a list of full dictionary.
    '''
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

    model = context['model']
    session = context['session']
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
        extras = data_dict.pop('extras', None)

        # enforce permission filter based on user
        if context.get('ignore_auth') or (user and authz.is_sysadmin(user)):
            labels = None
        else:
            labels = lib_plugins.get_permission_labels(
                ).get_user_dataset_labels(context['auth_user_obj'])

        # Here's where we diverge...

        facets = OrderedDict()

        facets = {
            'tags': _('Tags'),
            'res_format': _('Formats'),
            #'license_id': _('Licenses'),
            }

        #for facet in h.facets():
        #    if facet in default_facet_titles:
        #        facets[facet] = default_facet_titles[facet]
        #    else:
        #        facets[facet] = facet
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

#        # Add them back so extensions can use them on after_search
#        data_dict['extras'] = extras
#
#        if result_fl:
#            for package in query.results:
#                if package.get('extras'):
#                    package.update(package['extras'] )
#                    package.pop('extras')
#                results.append(package)
#        else:
#            for package in query.results:
#                # get the package object
#                package_dict = package.get(data_source)
#                ## use data in search index if there
#                if package_dict:
#                    # the package_dict still needs translating when being viewed
#                    package_dict = json.loads(package_dict)
#                    if context.get('for_view'):
#                        for item in plugins.PluginImplementations(
#                                plugins.IPackageController):
#                            package_dict = item.before_view(package_dict)
#                    results.append(package_dict)
#                else:
#                    log.error('No package_dict is coming from solr for package '
#                              'id %s', package['id'])
#
#        count = query.count
#        facets = query.facets
#    else:
#        count = 0
#        facets = {}
#        results = []
#
    search_results = {
        'count': results_count,
        #'facets': facets,
        'results': results_list,
        #'sort': data_dict['sort']
    }
#
#    # create a lookup table of group name to title for all the groups and
#    # organizations in the current search's facets.
#    group_names = []
#    for field_name in ('groups', 'organization'):
#        group_names.extend(facets.get(field_name, {}).keys())
#
#    groups = (session.query(model.Group.name, model.Group.title)
#                    .filter(model.Group.name.in_(group_names))
#                    .all()
#              if group_names else [])
#    group_titles_by_name = dict(groups)
#
#    # Transform facets into a more useful data structure.
#    restructured_facets = {}
#    for key, value in facets.items():
#        restructured_facets[key] = {
#            'title': key,
#            'items': []
#        }
#        for key_, value_ in value.items():
#            new_facet_dict = {}
#            new_facet_dict['name'] = key_
#            if key in ('groups', 'organization'):
#                display_name = group_titles_by_name.get(key_, key_)
#                display_name = display_name if display_name and display_name.strip() else key_
#                new_facet_dict['display_name'] = display_name
#            elif key == 'license_id':
#                license = model.Package.get_license_register().get(key_)
#                if license:
#                    new_facet_dict['display_name'] = license.title
#                else:
#                    new_facet_dict['display_name'] = key_
#            else:
#                new_facet_dict['display_name'] = key_
#            new_facet_dict['count'] = value_
#            restructured_facets[key]['items'].append(new_facet_dict)
#    search_results['search_facets'] = restructured_facets
#
#    # check if some extension needs to modify the search results
#    for item in plugins.PluginImplementations(plugins.IPackageController):
#        search_results = item.after_search(search_results, data_dict)
#
#    # After extensions have had a chance to modify the facets, sort them by
#    # display name.
#    for facet in search_results['search_facets']:
#        search_results['search_facets'][facet]['items'] = sorted(
#            search_results['search_facets'][facet]['items'],
#            key=lambda facet: facet['display_name'], reverse=True)
#
    return search_results


def process_grouped_results(results):
    processed_results = []
    for i in results:
        dataset_json = i['doclist']['docs'][0]['validated_data_dict']
        dataset_dict = json.loads(dataset_json)
        processed_results.append(
            {
             'collection_name': dataset_dict.get('collection_name') or dataset_dict['title'],
             'collection_count': i['doclist']['numFound'],
             'collection_id': dataset_dict['id'],
             'collection_description': dataset_dict['notes'],
             'is_collection': True
            }
        )

    return processed_results


class CollectionSearchQuery(SearchQuery):
    def get_all_entity_ids(self, max_results=1000):
        """
        Return a list of the IDs of all indexed packages.
        """
        query = "*:*"
        fq = "+site_id:\"%s\" " % config.get('ckan.site_id')
        fq += "+state:active "

        conn = make_connection()
        data = conn.search(query, fq=fq, rows=max_results, fields='id')
        return [r.get('id') for r in data.docs]

    def get_index(self,reference):
        query = {
            'rows': 1,
            'q': 'name:"%s" OR id:"%s"' % (reference,reference),
            'wt': 'json',
            'fq': 'site_id:"%s"' % config.get('ckan.site_id')}

        conn = make_connection(decode_dates=False)
        log.debug('Package query: %r' % query)
        try:
            solr_response = conn.search(**query)
        except pysolr.SolrError, e:
            raise SearchError('SOLR returned an error running query: %r Error: %r' %
                              (query, e))

        if solr_response.hits == 0:
            raise SearchError('Dataset not found in the search index: %s' % reference)
        else:
            return solr_response.docs[0]


    def run(self, query, permission_labels=None, **kwargs):
        '''
        Performs a dataset search using the given query.

        :param query: dictionary with keys like: q, fq, sort, rows, facet
        :type query: dict
        :param permission_labels: filter results to those that include at
            least one of these labels. None to not filter (return everything)
        :type permission_labels: list of unicode strings; or None

        :returns: dictionary with keys results and count

        May raise SearchQueryError or SearchError.
        '''
        assert isinstance(query, (dict, MultiDict))
        # check that query keys are valid
        if not set(query.keys()) <= VALID_SOLR_PARAMETERS:
            invalid_params = [s for s in set(query.keys()) - VALID_SOLR_PARAMETERS]
            raise SearchQueryError("Invalid search parameters: %s" % invalid_params)

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
        if not '+state:' in query.get('fq', ''):
            fq.append('+state:active')

        # only return things we should be able to see
        if permission_labels is not None:
            fq.append('+permission_labels:(%s)' % ' OR '.join(
                solr_literal(p) for p in permission_labels))
        query['fq'] = fq

        # faceting
        query['facet'] = query.get('facet', 'true')
        query['facet.limit'] = query.get('facet.limit', config.get('search.facets.limit', '50'))
        query['facet.mincount'] = query.get('facet.mincount', 1)

        # return the package ID and search scores
        query['fl'] = query.get('fl', 'name')

        # return results as json encoded string
        query['wt'] = query.get('wt', 'json')

        # If the query has a colon in it then consider it a fielded search and do use dismax.
        defType = query.get('defType', 'dismax')
        if ':' not in query['q'] or defType == 'edismax':
            query['defType'] = defType
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
            raise SearchError('SOLR returned an error running query: %r Error: %r' %
                              (query, e))

        self.count = solr_response.grouped['title']['ngroups'] # ['matches'] gives the total number of datasets
        self.results = solr_response.grouped['title']['groups']

        # #1683 Filter out the last row that is sometimes out of order
        self.results = self.results[:rows_to_return]

        # get any extras and add to 'extras' dict
        for result in self.results:
            extra_keys = filter(lambda x: x.startswith('extras_'), result.keys())
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
        print dir(solr_response)
        print solr_response.facets
        self.facets = solr_response.facets.get('facet_fields', {})
        for field, values in six.iteritems(self.facets):
            self.facets[field] = dict(zip(values[0::2], values[1::2]))

        return {'results': self.results, 'count': self.count}