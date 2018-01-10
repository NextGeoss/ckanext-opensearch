# -*- coding: utf-8 -*-
"""This module contains the OpenSearch plugin."""

import ckan.plugins as plugins
from ckan.common import config


class OpensearchPlugin(plugins.SingletonPlugin):
    """Plugin enabling an OpenSearch interface."""

    plugins.implements(plugins.IRoutes, inherit=True)

    # IRoutes
    def before_map(self, map):
        """Add the OpenSearch endpoints to the map."""
        controller = 'ckanext.opensearch.controller:OpenSearchController'

        map.connect('create_description_document', '/opensearch/description',
                    controller=controller,
                    action='create_description_document')

        map.connect('process_query', '/opensearch',
                    controller=controller, action='process_query',
                    search_type='dataset')

        # Optional support for two-step (collection->dataset) search
        if config.get('ckanext.opensearch.enable_collections') == 'true':

            map.connect('create_description_document',
                        '/opensearch/collections/description',
                        controller=controller,
                        action='create_description_document',
                        search_type='collection')

            map.connect('process_query', '/opensearch/collections',
                        controller=controller, action='process_query',
                        search_type='collection')

        return map
