# -*- coding: utf-8 -*-
import ckan.plugins as plugins
from ckan.common import config


class OpensearchPlugin(plugins.SingletonPlugin):
    """Plugin enabling an OpenSearch interface."""
    plugins.implements(plugins.IRoutes, inherit=True)

    # IRoutes
    def before_map(self, map):
        """Add the OpenSearch endpoints to the map."""
        map.connect('create_description_document', '/opensearch/description',
            controller='ckanext.opensearch.controller:OpenSearchController',
            action='create_description_document', search_type='dataset')

        map.connect('process_query', '/opensearch',
            controller='ckanext.opensearch.controller:OpenSearchController',
            action='process_query', search_type='dataset')

        # Optional support for two-step (collection->dataset) search
        if config.get('ckanext.opensearch.enable_collections') == 'true':

            map.connect('create_description_document',
                '/opensearch/collections/description',
                controller='ckanext.opensearch.controller:OpenSearchController',
                action='create_description_document', search_type='collection')

            map.connect('process_query', '/opensearch/collections',
                controller='ckanext.opensearch.controller:OpenSearchController',
                action='process_query', search_type='collection')

        return map
