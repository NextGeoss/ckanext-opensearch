# -*- coding: utf-8 -*-
"""This module processes configuration files and creates constants."""

import json
import os
import inspect
from collections import OrderedDict

from ckan.common import config


def load_config_file(file_path):
    """
    Given a path like "ckanext.opensearch:namespaces.json"
    find the second part relative to the import path of the first
    """
    module_name, file_name = file_path.split(':', 1)
    module = __import__(module_name, fromlist=[''])
    file_path = os.path.join(os.path.dirname(inspect.getfile(module)),
                             file_name)

    return open(file_path)


def load_settings(settings_name):
    """
    Load the JSON file containing the named settings specified in the
    INI file.
    """
    config_name = 'ckanext.opensearch.' + settings_name
    default_location = 'ckanext.opensearch.defaults:{}.json'.\
        format(settings_name)
    location = config.get(config_name, default_location)
    file = load_config_file(location)
    json_data = json.load(file)
    settings = json_data.get(settings_name)

    return settings


def get_parameters(parameter_type):
    """
    Return the list of parameters from the JSON file specified in the settings.

    If the parameters file is missing or invalid, raise an error.
    """
    parameter_settings = load_settings(parameter_type)
    parameters = OrderedDict(
        (i['ckan_name'], {
            'minimum': i.get('minimum', 0),
            'maximum': i.get('maximum', 1),
            'min_inclusive': i.get('min_inclusive', None),
            'max_exclusive': i.get('max_exclusive', None),
            'os_name': i['os_name'],
            'namespace': i['namespace'],
            'options': i.get('options'),
            'example': i.get('example', None)
        }) for i in parameter_settings)

    return parameters


def get_namespaces():
    """
    Return a dictionary of namespaces from the JSON file
    specified in the settings.
    """
    namespace_settings = load_settings('namespaces')
    namespaces = {i['alias']: i['namespace'] for i in namespace_settings}

    return namespaces


def get_elements():
    """
    Return the import path for the elements package.

    This enables us to specify an alterate elements.py package
    so that we can load custom elements when the plugin is loaded."""
    elements_path = config.get('ckanext.opensearch.elements',
                               'ckanext.opensearch.elements')

    return elements_path


def get_site_url():
    """Return the URL of the site for constructing template URLs."""
    return config.get('ckan.site_url', '')


def get_site_title():
    """Return the name of the site."""
    return config.get('ckan.site_title', 'CKAN Portal')


def get_temporal_start_field():
    """Return the database field to use for the start of temporal searches."""
    return config.get('ckanext.opensearch.temporal_start')


def get_temporal_end_field():
    """Return the database field to use for the end of temporal searches."""
    return config.get('ckanext.opensearch.temporal_end')


def get_short_name():
    """
    Return the short name of the portal/service.

    The short name must not be longer than 16 characters.
    """
    # TODO: Validate length of short name.
    return config.get('ckanext.opensearch.short_name', 'CKAN Portal')


def get_collection_params_list():
    """
    Return the list of collections and their parameter files
    from the JSON file specified in the settings.
    """
    collection_params_list = load_settings('collection_params_list')
    return collection_params_list


def get_group_field():
    """Return the name of the field for grouping collection search results."""
    return config.get('ckanext.opensearch.group_on', 'title')


# Constants
PARAMETERS = {}
for param_pair in get_collection_params_list():
    PARAMETERS[param_pair['id']] = get_parameters(param_pair['file'])
#PARAMETERS = {'dataset': get_parameters('dataset_parameters')}
if config.get('ckanext.opensearch.enable_collections') == 'true':
    PARAMETERS['collection'] = get_parameters('collection_parameters')
COLLECTIONS = [i['id'] for i in get_collection_params_list()]
print COLLECTIONS
NAMESPACES = get_namespaces()
ELEMENTS = get_elements()
SITE_URL = get_site_url()
SITE_TITLE = get_site_title()
TEMPORAL_START = get_temporal_start_field()
TEMPORAL_END = get_temporal_end_field()
SHORT_NAME = get_short_name()
GROUP_FIELD = get_group_field()
