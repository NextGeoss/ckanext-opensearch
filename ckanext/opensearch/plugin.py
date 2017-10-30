# -*- coding: utf-8 -*-
import ckan.plugins as plugins


class OpensearchPlugin(plugins.SingletonPlugin):
    """Plugin enabling an OpenSearch interface."""
    plugins.implements(plugins.IRoutes, inherit=True)

    # IRoutes
    def before_map(self, map):
        """Add the OpenSearch endpoints to the map."""
        map.connect('create_description_document', '/opensearch/description',
            controller='ckanext.opensearch.controller:OpenSearchController',
            action='create_description_document')

        map.connect('process_query', '/opensearch',
            controller='ckanext.opensearch.controller:OpenSearchController',
            action='process_query')

        return map
