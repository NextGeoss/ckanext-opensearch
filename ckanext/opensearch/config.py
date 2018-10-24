# -*- coding: utf-8 -*-
"""This module processes configuration files and creates constants."""

import toml
import os
import inspect
from collections import OrderedDict
import logging
import six

from ckan.common import config

log = logging.getLogger(__name__)


def load_config_file(file_path):
    """
    Given a path like "ckanext.opensearch:namespaces.toml"
    find the second part relative to the import path of the first
    """
    module_name, file_name = file_path.split(':', 1)
    module = __import__(module_name, fromlist=[''])
    file_path = os.path.join(os.path.dirname(inspect.getfile(module)),
                             file_name)

    return open(file_path)


def load_settings(settings_name):
    """
    Load the TOML file containing the named settings specified in the
    INI file.
    """
    config_name = 'ckanext.opensearch.' + settings_name
    default_location = 'ckanext.opensearch.defaults:{}.toml'.\
        format(settings_name)
    location = config.get(config_name, default_location)
    file = load_config_file(location)

    return toml.load(file, _dict=OrderedDict)


def get_site_url():
    """Return the URL of the site for constructing template URLs."""
    return six.text_type(os.environ.get(
        'CKAN_SITE_URL', config.get('ckan.site_url', ''))).strip()


def get_site_title():
    """Return the name of the site."""
    return six.text_type(os.environ.get(
        'CKAN__SITE_TITLE', config.get(
            'ckan.site_title', 'CKAN Portal'))).strip()


def get_temporal_start_field():
    """Return the database field to use for the start of temporal searches."""
    return six.text_type(os.environ.get(
        'CKANEXT__OPENSEARCH__TEMPORAL_START', config.get(
            'ckanext.opensearch.temporal_start', ''))).strip()


def get_temporal_end_field():
    """Return the database field to use for the end of temporal searches."""
    return six.text_type(os.environ.get(
        'CKANEXT__OPENSEARCH__TEMPORAL_END', config.get(
            'ckanext.opensearch.temporal_end', ''))).strip()


def get_short_name():
    """
    Return the short name of the portal/service.

    The short name must not be longer than 16 characters.
    """
    # TODO: Validate length of short name.
    return six.text_type(os.environ.get(
        'CKANEXT__OPENSEARCH__SHORT_NAME', config.get(
            'ckanext.opensearch.short_name', 'CKAN Portal'))).strip()


# Constants
try:
    COLLECTIONS = load_settings("collections_list")
except IOError:
    log.debug("No OpenSearch collections are configured.")
    COLLECTIONS = {}

PARAMETERS = {}
PARAMETERS['dataset'] = load_settings('dataset_parameters')
if COLLECTIONS:
    PARAMETERS['collection'] = load_settings('collection_parameters')
for _id, details in COLLECTIONS.items():
    PARAMETERS[_id] = dict(PARAMETERS["dataset"])
    extended_parameters = details.get("parameters_file")
    if extended_parameters:
        PARAMETERS[_id].update(load_settings(extended_parameters))

NAMESPACES = load_settings('namespaces')

SITE_URL = get_site_url()
SITE_TITLE = get_site_title()
TEMPORAL_START = get_temporal_start_field()
TEMPORAL_END = get_temporal_end_field()
SHORT_NAME = get_short_name()
