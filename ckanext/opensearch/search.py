# -*- coding: utf-8 -*-
"""
Contains functions for executing OpenSearch queries and returning Atom results.
"""

from collections import OrderedDict
from datetime import datetime
import math
import re

from webob.multidict import MultiDict, UnicodeMultiDict

from ckan.lib.base import abort, render
import ckan.logic as logic

from .config import COLLECTIONS, NAMESPACES, PARAMETERS, SHORT_NAME, SITE_URL
import converters
from plugin import OpenSearchError
import validators
from ckanext.opensearch import helpers


def make_results_feed(search_type, params, request_url, context):
    """Process the query and return the results feed."""
    abort_if_collection_id_invalid(params)
    abort_if_collections_not_configured(search_type)

    param_dict = make_param_dict(params, search_type)

    validate_params(param_dict, PARAMETERS[search_type])

    results_dict = process_query(search_type, param_dict, request_url, context)

    return make_atom_feed(results_dict, search_type)


def abort_if_collection_id_invalid(params):
    """
    Abort if the collection_id is invalid. Every search has specific parameters
    that are permitted or available. If a user tries to search
    in a collection that doesn't exist, we have no way of looking up the
    valid parameters.
    """
    collection_id = params.get("productType")

    if collection_id:
        try:
            PARAMETERS[collection_id]
        except KeyError:
            abort(400, "Invalid collection_id ({})".format(collection_id))


def abort_if_collections_not_configured(search_type):
    """
    Abort if no collections are configured but a user is trying to perform a
    collection search.
    """
    if search_type == "collection" and not COLLECTIONS:
        abort(400, "Collection search is unavailable.")


def validate_params(submitted_params, expected_params):
    """Validate each submitted parameter and raise an exception if one is invalid."""
    try:
        param_counts = {}
        for param_name, _ in submitted_params.items():
            if param_name not in param_counts:
                param_counts[param_name] = 1
            else:
                param_counts[param_name] += 1

        for param_name, param_value in submitted_params.items():
            param_config = expected_params[param_name]
            display_name = "{}:{}".format(
                param_config["namespace"], param_config["os_name"]
            )
            min_occurances = param_config.get("minimum", 0)
            max_occurances = param_config.get("maximum", "*")
            value_min_inclusive = param_config.get("min_inclusive", None)
            value_max_exclusive = param_config.get("max_exclusive", None)
            additional_validators = param_config.get("validators", [])

            # Base validators for all parameters
            validators.valid_occurances(
                param_counts[param_name], min_occurances, max_occurances, display_name
            )
            validators.valid_value_min_max(
                param_value, value_min_inclusive, value_max_exclusive, display_name
            )

            # Additional validators from the parameter config
            for validator in additional_validators:
                getattr(validators, validator)(param_value, display_name)

    except OpenSearchError as e:
        abort(400, str(e))


def process_query(search_type, param_dict, request_url, context):
    """
    Process the search query. Underneath, we're still executing a standard
    CKAN search. We're just using a different validation flow and doing
    something different with the results.
    """
    # Translate the query parameters into a CKAN data_dict so we
    # can query the DB.
    data_dict = translate_os_query(param_dict, search_type)
    start = data_dict['start_index']
    del data_dict['start_index']
    print data_dict

    results_dict = search(data_dict, search_type, context)

    results_dict["items_per_page"] = data_dict["rows"]

    # Get next page, previous page and index of first element on page.
    current_page = int(param_dict.get("page") or 1)
    total_results = results_dict["count"]
    requested_rows = results_dict["items_per_page"]
    expected_results = requested_rows * current_page

    if expected_results >= total_results:
        next_page = None
    else:
        next_page = current_page + 1

    if current_page == 1:
        prev_page = None
    else:
        prev_page = current_page - 1

    last_page = int(math.ceil(total_results / float(requested_rows)))
    if last_page == 0:
        last_page = 1

    results_dict["namespaces"] = {
        "xmlns:{0}".format(key): value for key, value in NAMESPACES.items()
    }
    results_dict["feed_title"] = "{} OpenSearch Search Results".format(SHORT_NAME)
    results_dict["feed_subtitle"] = "{} results for your search".format(total_results)
    results_dict["feed_generator_attrs"] = {
        "version": "0.1",
        "uri": request_url.replace("&", "&amp;"),
    }
    results_dict["feed_generator_content"] = "{} search results".format(SHORT_NAME)
    results_dict["feed_updated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    results_dict["start_index"] = start
    results_dict["query_attrs"] = make_query_dict(param_dict, search_type)
    results_dict["feed_box"] = make_feed_box(results_dict)
    results_dict["site_url"] = SITE_URL
    results_dict["search_url"] = "{}/opensearch/description.xml".format(SITE_URL)
    results_dict["self_url"] = request_url
    results_dict["base_url"] = make_base_url(request_url)
    results_dict["first_url"] = make_nav_url(request_url, 1)
    results_dict["next_url"] = make_nav_url(request_url, next_page)
    results_dict["prev_url"] = make_nav_url(request_url, prev_page)
    results_dict["last_url"] = make_nav_url(request_url, last_page)

    return results_dict


def make_param_dict(params, search_type):
    """
    Get the query parameters and remove 'amp' if it has snuck in.
    Strip any parameters that aren't valid as per CEOS-BP-009B.
    Exclude empty parameters.
    """
    param_dict = UnicodeMultiDict(MultiDict(), encoding="utf-8")

    for param, value in params.items():
        if param != "amp" and param in PARAMETERS.get(search_type, {}) and value:
            param_dict.add(param, value)

    return param_dict


def translate_os_query(param_dict, search_type):
    """
    Translate the OpenSearch query parameters based on a template.

    The parameters will already have been validated.
    """
    # convert params and build data dictionary
    data_dict = {}
    if param_dict.get("q") != "":
        data_dict["q"] = param_dict.get("q")
    data_dict["rows"] = set_rows(param_dict.get("rows"))
    data_dict["start_index"] = set_search_index(param_dict.get("start_index"))
    data_dict["start"] = set_start(data_dict["rows"], data_dict["start_index"], param_dict.get("page"))
    #data_dict["start"] = set_start(data_dict["rows"], param_dict.get("page"))
    data_dict["ext_bbox"] = param_dict.get("bbox")
    # data_dict["collection_id"] = param_dict.get("productType")

    # del param_dict["productType"]

    # if param_dict.get('geom'):
    #     param_dict['geom'] = param_dict['spatail_geom']
    #     del param_dict['geom']


    # if param_dict.get('orbit_direction'):
    #     param_dict['orbitDirection'] = param_dict['orbit_direction']
    #     del param_dict['orbit_direction']

    # if param_dict.get('polarisation'):
    #     param_dict['TransmitterReceiverPolarisation'] = param_dict['polarisation']
    #     del param_dict['polarisation']

    data_dict["fq"] = add_filters(param_dict, search_type)

    return data_dict


def set_rows(rows_param):
    if not rows_param:
        return 20
    else:
        return int(rows_param)


def set_search_index(rows_param):
    if not rows_param:
        return 1
    else:
        return int(rows_param)


def set_start(rows, start_index, page_param):
    if not page_param:
        page = 0
    else:
        page = int(page_param) - 1

    if start_index > 1:
        return start_index
    else:
        return rows * page


def add_filters(param_dict, search_type):
    """
    Some parameters map directly to filter queries; we can just append them.
    """
    filters = ""

    for (param, value) in param_dict.items():
        # TODO: the params to skip should be defined elsewhere.
        skip = {"q", "rows", "page", "ext_bbox", "start_index", "bbox"}
        extra_params = {"swath", "orbit_direction", "polarisation", "product_type",
                "cloud_coverage", "family_name"}

        if param not in skip:
            for converter in PARAMETERS[search_type][param].get("converters", []):
                value = getattr(converters, converter)(value)
            names = helpers.get_extra_names()
            if param in names:
                param = names[param]
            if param == 'productType':
                param = 'collection_id'

            filters += " %s:%s" % (param, value)

        # if param in extra_params:
        #     os_name = PARAMETERS[search_type][param]["os_name"]
        #     filters += " %s:%s" % (os_name, value)

    return filters + " +dataset_type:dataset"


def search(data_dict, search_type, context):
    # Query the DB.
    if search_type == "collection":
        data_dict["facet.field"] = ["collection_id"]

    print data_dict

    results_dict = logic.get_action("package_search")(context, data_dict)

    if search_type == "collection":
        return collection_results_dict(results_dict)
    else:
        return results_dict_with_accessible_extras(results_dict)


def collection_results_dict(results_dict):
    """Return a new results_dict with just the collection information."""
    collection_results = []

    # We don't have published/updated information for collections right now,
    # so we have to fake it.
    published = "2018-01-16T00:00:00Z"
    updated = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    collections = results_dict["facets"].get("collection_id", {})

    for _id, count in collections.items():
        collection_results.append(
            {
                "id": _id,
                "count": count,
                "description": COLLECTIONS[_id]["description"],
                "name": COLLECTIONS[_id]["name"],
                "published": published,
                "updated": updated,
            }
        )

    return {"results": collection_results, "count": len(collections)}


def results_dict_with_accessible_extras(results_dict):
    """Get the extras from their list and make them normal key/value pairs."""
    for entry in results_dict["results"]:
        extras = {extra["key"]: extra["value"] for extra in entry.pop("extras", [])}
        entry.update(extras)

    return results_dict


def make_query_dict(param_dict, search_type):
    """
    Make a dict of params and values for Query element in the response.

    The formatting is is different from the query/parameter dictionary that
    CKAN already provides, so we need to do a bit of work first to rename
    them and combine parameters that occur more than once into a single
    string.
    """
    query_dict = OrderedDict()

    # XML attributes are unique per element, so parameters that occur more
    # than once in a query must be combined into a space-delimited string.
    for (param, value) in param_dict.items():
        os_name = PARAMETERS[search_type][param]["os_name"]
        namespace = PARAMETERS[search_type][param]["namespace"]
        if namespace == "opensearch":
            os_param = os_name
        else:
            os_param = "{}:{}".format(namespace, os_name)
        if os_param not in query_dict:
            query_dict[os_param] = value
        else:
            query_dict[os_param] += " {}".format(value)

    query_dict["role"] = "request"

    return query_dict


def make_feed_box(results_dict):
    """Return the content of the GeoRSS box element for the feed."""
    bbox_param = "{http://a9.com/-/opensearch/extensions/geo/1.0/}box"
    bbox = results_dict["query_attrs"].get(bbox_param)
    if bbox:
        return bbox.replace(",", " ")
    else:
        return "-180.0 -90.0 180.0 90.0"


def make_nav_url(query_url, page):
    """Create a navigation URL (next, prev, last, etc.)."""
    if not page:
        return None
    else:
        if "page=" not in query_url:
            nav_url = "{0}?page={1}".format(query_url, page)
        else:
            halves = re.compile(r"page=\d*").split(query_url)
            if len(halves) == 1:
                nav_url = "{0}?page={1}".format(halves[0], page)
            else:
                nav_url = "{0}page={1}{2}".format(halves[0], page, halves[1])

        return nav_url


def make_atom_feed(results_dict, search_type):
    """Convert the modified search results dictionary into Atom XML."""
    if search_type == "collection":
        template = "collection_results"
    else:
        template = "search_results"

    return render("opensearch/{}.xml".format(template), extra_vars=results_dict)


def make_base_url(query_url):
    import re
    if 'start_index' in query_url:
        query_url = re.sub("&start_index=.*", "", query_url)

    return query_url
