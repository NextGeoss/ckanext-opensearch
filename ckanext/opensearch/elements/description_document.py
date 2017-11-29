# -*- coding: utf-8 -*-
from collections import OrderedDict

from ckan.common import g

from ckanext.opensearch.config import PARAMETERS
from . import OSElement


class DescriptionDocument(OSElement):
    """Define the OpenSearch description document element."""

    def __init__(self, description_type):
        children = [
            (DescShortName, None),
            (DescDescription, None),
            (DescTags, None),
            (DescSyndication, None),
            (SearchURL, description_type),

        ]
        OSElement.__init__(self, 'opensearch', 'OpenSearchDescription',
            children=children)


class DescShortName(OSElement):
    """Define the OpenSearch description document short name element."""

    def __init__(self):
        site_title = g.site_title or 'CKAN'
        short_name = '{} {}'.format(site_title, 'OpenSearch')
        OSElement.__init__(self, 'opensearch', 'ShortName', content=short_name)


class DescDescription(OSElement):
    """Define the OpenSearch description document description here."""

    def __init__(self):
        name = g.site_title or 'CKAN'
        default = 'OpenSearch gateway for the {} data catalogue'.format(name)
        # TODO: Add a way to set a custom description in the settings, probably
        # using `h.config.get()`.
        custom = None
        description = custom or default
        OSElement.__init__(self, 'opensearch', 'Description',
            content=description)


class DescTags(OSElement):
    """Define the OpenSearch tags element."""

    def __init__(self):
        default = 'open data CKAN opendata'
        # TODO: Add a way to set custom tags in the settings, probably
        # using `h.config.get()`.
        custom = None
        tags = custom or default
        OSElement.__init__(self, 'opensearch', 'Tags', content=tags)


class DescSyndication(OSElement):
    """Define the OpenSearch syndication rights element."""

    def __init__(self):
        default = 'open'
        # TODO: Add a way to set custom tags in the settings, probably
        # using `h.config.get()`.
        custom = None
        rights = custom or default
        OSElement.__init__(self, 'opensearch', 'SyndicationRight', content=rights)


class SearchURL(OSElement):
    """
    Define the OpenSearch element describing the URL template to use for
    searching.
    """

    def __init__(self, description_type):
        print 'hey'
        attr = {
            'type': 'application/atom+xml',
            'template': self.create_search_template(description_type)
        }
        param_dicts = self.create_param_dicts(description_type)
        children = [
            (Parameter, param_dicts)
        ]
        OSElement.__init__(self, 'opensearch', 'Url', attr=attr, children=children)

    def create_search_template(self, description_type):
        """Create the OpenSearch template based on the various parameters."""
        print 'calling search template'
        site = g.site_url
        terms = []
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

        search_template = '{}/opensearch?{}'.format(site, terms)

        return search_template

    def create_param_dicts(self, description_type):
        """Convert parameters settings into a usable format for creating XML."""
        print 'calling param dicts'
        param_dicts = []

        for param, details in PARAMETERS[description_type].items():

            # Create a dictionary of the parameter attributes
            param_dict = OrderedDict()
            param_dict['name'] = param
            param_dict['value'] = '{%s:%s}' % (details['namespace'], details['os_name'])
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
        if options:
            children = [
                (Option, options)
            ]
        else:
            children = None
        OSElement.__init__(self, 'param', 'Parameter', attr=params, children=children)

    def _filter_params(self, param_dict):
        # Remove out any empty attributes and make sure they're strings
        for i in param_dict:
            if param_dict[i] == None:
                param_dict.pop(i)
            else:
                param_dict[i] = str(param_dict[i])

        return param_dict


class Option(OSElement):
    """Define an OpenSearch Parameter option element."""

    def __init__(self, option_dict):
        OSElement.__init__(self, 'param', 'Option', attr=option_dict)
