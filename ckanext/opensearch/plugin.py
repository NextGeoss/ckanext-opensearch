# -*- coding: utf-8 -*-
"""This module contains the OpenSearch plugin."""

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.opensearch import helpers


class OpensearchPlugin(plugins.SingletonPlugin):
    """Plugin enabling an OpenSearch interface."""

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")

    # ITemplateHelpers

    def get_helpers(self):
        return {
            "os_make_collection_via": helpers.make_collection_via,
            "os_make_entry_polygon": helpers.make_entry_polygon,
            "os_make_entry_point": helpers.make_entry_point,
            "os_make_entry_resource": helpers.make_entry_resource,
            "os_make_noa_entry_resource": helpers.make_noa_entry_resource,
            'get_extra_names': helpers.get_extra_names,
            "os_spatial_type": helpers.spatial_type,
        }

    # IRoutes
    def before_map(self, map):
        """Add the OpenSearch endpoints to the map."""
        controller = "ckanext.opensearch.controller:OpenSearchController"

        map.connect(
            "return_description_document",
            "/opensearch/description.xml",
            controller=controller,
            action="return_description_document",
        )

        map.connect(
            "process_query",
            "/opensearch/search.atom",
            controller=controller,
            action="return_search_results",
            search_type="dataset",
        )

        map.connect(
            "process_query",
            "/opensearch/collection_search.atom",
            controller=controller,
            action="return_search_results",
            search_type="collection",
        )

        return map


class OpenSearchError(Exception):
    """Used for OpenSearch-related errors, like invalid parameters in queries."""
    pass
