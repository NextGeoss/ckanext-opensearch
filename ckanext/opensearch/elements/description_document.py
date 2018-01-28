# -*- coding: utf-8 -*-
"""Contains the elements for an OpenSearch description document."""

from collections import OrderedDict

from ckan.common import request

from ckanext.opensearch.config import PARAMETERS
from ckanext.opensearch.config import SITE_URL
from ckanext.opensearch.config import NAMESPACES
from ckanext.opensearch.config import SHORT_NAME
from . import OSElement


class DescriptionDocument(OSElement):
    """Define the OpenSearch description document element."""

    def __init__(self, description_type):
        children = [
            (DescShortName, None),
            (DescDescription, description_type),
            (DescTags, None),
            (DescSyndication, None),
            (SelfURL, None),
            (SearchURL, description_type),
            (QueryExample, description_type)
        ]
        attr = {'{http://commons.esipfed.org/ns/discovery/1.2/}version': '1.2'}

        OSElement.__init__(self, 'opensearch', 'OpenSearchDescription',
                           attr=attr, children=children)


class DescShortName(OSElement):
    """Define the OpenSearch description document short name element."""

    def __init__(self):
        OSElement.__init__(self, 'opensearch', 'ShortName', content=SHORT_NAME)


class DescDescription(OSElement):
    """Define the OpenSearch description document description here."""

    def __init__(self, description_type):
        if description_type == 'collection':
            description = 'Search collections of products.'
        else:
            description = ('Search products in the {} collection.'
                           .format(description_type))
        OSElement.__init__(self, 'opensearch', 'Description',
                           content=description)


class DescTags(OSElement):
    """Define the OpenSearch tags element."""

    def __init__(self):
        default = 'open data CKAN opendata'
        # TODO: Add a way to set custom tags in the settings, probably
        # using `h.config.get()`.
        custom = None
        tags = custom or default + ' CEOS-OS-BP-V1.1'
        OSElement.__init__(self, 'opensearch', 'Tags', content=tags)


class DescSyndication(OSElement):
    """Define the OpenSearch syndication rights element."""

    def __init__(self):
        default = 'open'
        # TODO: Add a way to set custom tags in the settings, probably
        # using `h.config.get()`.
        custom = None
        rights = custom or default
        OSElement.__init__(self, 'opensearch', 'SyndicationRight',
                           content=rights)


class SelfURL(OSElement):
    """Describe the OS element containing the link the description document."""

    def __init__(self):
        attr = {'rel': 'self', 'type': 'application/opensearchdescription+xml',
                'template': request.url}
        OSElement.__init__(self, 'opensearch', 'Url', attr=attr)


class SearchURL(OSElement):
    """Describe the OpenSearch search template."""

    def __init__(self, description_type):
        if description_type == 'collection':
            rel = 'collection'
        else:
            rel = 'results'
        attr = {'pageOffset': '1',
                'indexOffset': '1',
                'rel': rel,
                'type': 'application/atom+xml',
                'template': self._create_search_template(description_type)}
        param_dicts = self._create_param_dicts(description_type)
        children = [
            (Parameter, param_dicts)
        ]
        OSElement.__init__(self, 'opensearch', 'Url', attr=attr,
                           children=children)

    def _create_search_template(self, description_type):
        """Create the OpenSearch template based on the various parameters."""
        terms = []
        if description_type is not 'collection':
            terms.append('collection={}'.format(description_type))
        for param, details in PARAMETERS[description_type].items():
            name = param
            value = details['os_name']
            # Add namespace and required flag to value if necessary
            namespace = details.get('namespace', 'opensearch')
            value = namespace + ':' + value
            required = details.get('minimum')
            if not required:
                value = value + '?'
            term = name + '={' + value + '}'
            terms.append(term)
        terms = '&'.join(terms)

        search_template = '{}/opensearch/search.atom?{}'.format(SITE_URL,
                                                                terms)

        return search_template

    def _create_param_dicts(self, description_type):
        """Convert parameters settings into a usable format for making XML."""
        print 'calling param dicts'
        param_dicts = []

        for param, details in PARAMETERS[description_type].items():

            # Create a dictionary of the parameter attributes
            param_dict = OrderedDict()
            param_dict['name'] = param
            param_dict['value'] = '{%s:%s}' % (details['namespace'],
                                               details['os_name'])
            param_dict['title'] = details.get('title')
            param_dict['minimum'] = details.get('minimum')
            param_dict['maximum'] = details.get('maximum')
            param_dict['minInclusive'] = details.get('min_inclusive')
            param_dict['maxExclusive'] = details.get('max_exclusive')
            # The options will be handled separately
            param_dict['options'] = details.get('options')
            param_dicts.append(param_dict)

        return param_dicts


class Parameter(OSElement):
    """Define an OpenSearch Parameter parameter element."""

    def __init__(self, param_dict):
        self.minimum = param_dict['minimum']
        self.maximum = param_dict['maximum']
        self.min_inclusive = param_dict['minInclusive']
        self.max_exclusive = param_dict['maxExclusive']
        options = param_dict.pop('options')
        params = self._filter_params(param_dict)
        children = []
        if params.get('name') == 'q':
            children.append((SearchProfile, None))
        print children
        if options:
            children.append((Option, options))
        OSElement.__init__(self, 'param', 'Parameter', attr=params,
                           children=children)

    def _filter_params(self, param_dict):
        # Remove out any empty attributes and make sure they're strings
        for i in param_dict:
            if param_dict[i] is None:
                param_dict.pop(i)
            else:
                param_dict[i] = str(param_dict[i])

        return param_dict


class SearchProfile(OSElement):
    """Define an Atom element describing the profile for free text search."""

    def __init__(self):
        link = OrderedDict()
        link['title'] = 'This parameter follows the Lucene free text search implementations'  # noqa: E501
        link['rel'] = 'profile'
        link['href'] = 'http://lucene.apache.org/core/2_9_4/queryparsersyntax.html'  # noqa: E501
        OSElement.__init__(self, 'atom', 'link', attr=link)


class Option(OSElement):
    """Define an OpenSearch Parameter option element."""

    def __init__(self, option_dict):
        OSElement.__init__(self, 'param', 'Option', attr=option_dict)


class QueryExample(OSElement):
    """Define an OpenSearch Query example to enable test searches."""

    def __init__(self, description_type):
        example_query = self._create_example_query(description_type)
        OSElement.__init__(self, 'opensearch', 'Query', attr=example_query)

    def _create_example_query(self, description_type):
        """Create an example query element based on the parameters."""
        examples = OrderedDict()

        examples['role'] = 'example'

        for param, details in PARAMETERS[description_type].items():
            example_value = details['example']
            if example_value is not None:
                if details['namespace'] != 'opensearch':
                    namespace_url = NAMESPACES[details['namespace']]
                    parameter = '{%s}%s' % (namespace_url, details['os_name'])
                else:
                    parameter = details['os_name']
                examples[parameter] = str(example_value)

        return examples
