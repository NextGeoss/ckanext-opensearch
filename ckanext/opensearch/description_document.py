# -*- coding: utf-8 -*-
"""Contains functions for building description documents."""

from collections import OrderedDict

from ckan.lib.base import abort, render

from .config import PARAMETERS, NAMESPACES, SHORT_NAME, SITE_URL


def make_description_document(params, request_url):
    """Return description document as XML."""
    document_type = get_document_type_or_abort(params)

    osdd_dict = {}
    osdd_dict["namespaces"] = {
        "xmlns:{0}".format(key): value for key, value in NAMESPACES.items()
    }
    osdd_dict["short_name"] = SHORT_NAME
    osdd_dict["description"] = make_osdd_description(document_type)
    osdd_dict["tags"] = make_osdd_tags()
    osdd_dict["syndication"] = make_syndication()
    osdd_dict["self_url"] = request_url
    osdd_dict["search_rel"] = make_search_rel(document_type)
    osdd_dict["search_url"] = make_search_template(document_type)
    osdd_dict["parameters"] = make_parameters(document_type)

    return render("opensearch/description_document.xml", extra_vars=osdd_dict)


def get_document_type_or_abort(params):
    """Return the type of description document or abort if it's invalid."""
    document_type = params.get("osdd")

    try:
        PARAMETERS[document_type]
    except KeyError:
        abort(400, "Invalid osdd name (osdd={})".format(document_type))

    return document_type


def make_osdd_description(document_type):
    """Create a description of the OSDD for it description element."""
    if document_type == "collection":
        description = "Search collections of products."
    elif document_type == "dataset":
        description = "Search all datasets."
    else:
        description = "Search products in the {} collection.".format(document_type)

    return description


def make_osdd_tags():
    """Return a string of tags for the OSDD's tags element."""
    default = "open data CKAN opendata"
    # TODO: Add a way to set custom tags in the settings
    custom = None

    return custom or default


def make_syndication():
    """Return the content of the OSDD's syndication element."""
    default = "open"
    # TODO: Add a way to set custom tags in the settings
    custom = None
    return custom or default


def make_search_rel(document_type):
    """Return the value of the rel attribute of search link element."""
    if document_type == "collection":
        return "collection"
    else:
        return "results"


def make_search_template(document_type):
    """Create the OpenSearch template based on the various parameters."""
    terms = []
    if document_type != "collection":
        terms.append("collection_id={}".format(document_type))
    for param, details in PARAMETERS[document_type].items():
        name = param
        value = details["os_name"]
        # Add namespace and required flag to value if necessary
        namespace = details.get("namespace", "opensearch")
        value = namespace + ":" + value
        required = details.get("minimum")
        if not required:
            value = value + "?"
        term = name + "={" + value + "}"
        terms.append(term)
    terms = "&".join(terms)

    search_template = "{}/opensearch/search.atom?{}".format(SITE_URL, terms)
    return search_template


def make_parameters(document_type):
    """Convert parameters settings into a usable format for making XML."""
    param_dicts = []

    for param, details in PARAMETERS[document_type].items():
        attrs = OrderedDict()
        attrs["name"] = param
        attrs["value"] = "{%s:%s}" % (details["namespace"], details["os_name"])
        attrs["title"] = details.get("title")
        attrs["minimum"] = details.get("minimum")
        attrs["maximum"] = details.get("maximum")
        attrs["minInclusive"] = details.get("min_inclusive")
        attrs["maxExclusive"] = details.get("max_exclusive")

        options = details.get("options")

        param_dicts.append({"attrs": attrs, "options": options})

    return param_dicts
