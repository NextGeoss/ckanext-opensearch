# -*- coding: utf-8 -*-
"""This module contains the OpenSearch plugin."""

import os
import six

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.common import config

from ckanext.opensearch import helpers


class OpensearchPlugin(plugins.SingletonPlugin):
    """Plugin enabling an OpenSearch interface."""

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'os_make_collection_id': helpers.make_collection_id,
            'os_make_collection_updated': helpers.make_collection_updated,
            'os_make_collection_dc_date': helpers.make_collection_dc_date,
            'os_make_collection_box': helpers.make_collection_box,
            'os_make_collection_polygon': helpers.make_collection_polygon,
            'os_make_collection_summary': helpers.make_collection_summary,
            'os_make_collection_content': helpers.make_collection_content,
            'os_make_collection_via': helpers.make_collection_via,
            'os_make_search_element_attrs': helpers.make_search_element_attrs,
            'os_make_entry_atom_id': helpers.make_entry_atom_id,
            'os_make_entry_dc_date': helpers.make_entry_dc_date,
            'os_make_entry_polygon': helpers.make_entry_polygon,
            'os_make_entry_summary': helpers.make_entry_summary,
            'os_make_entry_self_url': helpers.make_entry_self_url,
            'os_make_entry_collection_url': helpers.make_entry_collection_url,
            'os_make_entry_publisher': helpers.make_entry_publisher,
            'os_make_entry_resource': helpers.make_entry_resource,
            'os_filter_options': helpers.filter_options,
            'os_make_entry_dc_identifier': helpers.make_entry_dc_identifier,
            'os_make_collection_search_url': helpers.make_collection_search_url
        }

    # IRoutes
    def before_map(self, map):
        """Add the OpenSearch endpoints to the map."""
        controller = 'ckanext.opensearch.controller:OpenSearchController'

        map.connect('return_description_document',
                    '/opensearch/description.xml',
                    controller=controller,
                    action='return_description_document')

        map.connect('process_query', '/opensearch/search.atom',
                    controller=controller, action='return_search_results',
                    search_type='dataset')

        # Optional support for two-step (collection->dataset) search
        if six.text_type(os.environ.get('CKANEXT__OPENSEARCH__ENABLE_COLLECTIONS', config.get('ckanext.opensearch.enable_collections', ''))).strip() == "true":

            map.connect('create_description_document',
                        '/opensearch/collections/description.xml',
                        controller=controller,
                        action='create_description_document',
                        search_type='collection')

            map.connect('process_query', '/opensearch/collection_search.atom',
                        controller=controller, action='return_search_results',
                        search_type='collection')

        return map
