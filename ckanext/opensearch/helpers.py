# -*- coding: utf-8 -*-
import json
import ast
import ckan.logic as logic

from ckan.lib.helpers import get_pkg_dict_extra

def make_collection_via(entry):
    """URL pointing to the source's metadata about the collection."""
    # We can include pages on the Data Hub with info about the collections and
    # point there instead of to the original pages in the future.
    collection_id = entry.get("collection_id") or entry.get("id")
    if "urn:ogc:def:EOP:VITO" in collection_id:
        url = "http://www.vito-eodata.be/collections/srv/eng/xml_iso19139?uuid={}".format(  # noqa: E501
            collection_id
        )
        content_type = "application/vnd.iso.19139+xml"
    elif "SENTINEL" in collection_id:
        url = "https://sentinels.copernicus.eu/web/sentinel"
        content_type = "text/html"
    else:
        url = "http://example.com"
        content_type = "text/html"

    return {"href": url, "type": content_type, "rel": "via"}


def convert_dataset_extra(dataset_extra_string):
    """Convert the dataset_extra string into indexable extras."""
    extras = ast.literal_eval(dataset_extra_string)

    return [(extra["key"], extra["value"]) for extra in extras]


def string_extras_to_extras_list(pkg_dict):
    """Convert extras saved as a string to a normal extras list."""
    extras = pkg_dict.get("extras")

    if extras and extras[0]["key"] == "dataset_extra":
        pkg_dict["extras"] = ast.literal_eval(extras[0]["value"])

    return pkg_dict


def spatial_type(entry):
    spatial = entry['spatial'] if 'spatial' in entry else None

    if spatial is not None:
        spatial = json.loads(spatial)
        spatial_type = spatial.get('type')

    return spatial_type


def make_entry_polygon(entry):
    """Define a GEORSS polygon element based on an entry's spatial value."""
    #spatial = get_pkg_dict_extra(entry, "noa_expiration_date", "")
    spatial = entry['spatial'] if 'spatial' in entry else None

    if spatial is not None:
        spatial = json.loads(spatial)
        spatial_type = spatial.get('type')

        if spatial_type == 'Polygon':
            coordinates = spatial["coordinates"][0]
            coord_list = []
            for i in coordinates:
                coord_list.append(str(i[0]))
                coord_list.append(str(i[1]))
            coord_str = " ".join(coord_list)

        else:
            coord_str = ""

        return coord_str


def make_entry_point(entry):
    """Define a GEORSS polygon element based on an entry's spatial value."""
    #spatial = get_pkg_dict_extra(entry, "noa_expiration_date", "")
    spatial = entry['spatial'] if 'spatial' in entry else None

    if spatial is not None:
        spatial = json.loads(spatial)
        spatial_type = spatial.get('type')

        if spatial_type == 'Point':
            coordinates = spatial["coordinates"]
            coord_list = []
            for i in coordinates:
                coord_list.append(str(i))
            coord_str = " ".join(coord_list)

        else:
            coord_str = ""

        return coord_str



def make_entry_resource(resource):
    """
    Define an Atom element describing a link to a datset's resource.

    There can be more than one resource link in an entry.
    """
    default = "application/octet-stream"
    mime_type = resource.get("mimetype") or default
    name = resource.get("name", "Untitled")
    if name.startswith("Metadata Download"):
        link = {"href": resource["url"], "title": name, "rel": "via", "type": mime_type}
    elif name.startswith("Thumbnail Download"):
        link = {
            "href": resource["url"],
            "title": "Quicklook image",
            "rel": "icon",
            "type": mime_type,
        }
    else:
        link = {
            "href": resource["url"],
            "title": name,
            "rel": "enclosure",
            "type": mime_type,
            "length": str(resource.get("size", "")),
        }

    return link


def make_noa_entry_resource(package):
    """
    Define an Atom element describing a link to a datset's resource.

    There can be more than one resource link in an entry.
    """
    package_id = package.get('name')
    link = {}
    # get list of NOA resources
    from ckanext.nextgeoss.helpers import get_noa_linker_resources_for_package

    noa_resources = get_noa_linker_resources_for_package(package)

    if len(noa_resources) > 0:
        noa_links = noa_resources.get(package_id or [])

        for resource in noa_links[:-1]:
            default = "application/octet-stream"
            mime_type = default
            name = "NOA Sentinel Linker Service resource"
            link = {"href": resource, "title": name, "rel": "enclosure", "type": mime_type}

    return link


def get_extra_names():
    """
    Return a dictionary of new names for use with the subs parameter of
    h.sorted_extras. We may want to grab these names from the config
    in the future.
    """
    new_names = {
        'swath': 'Swath',
        'orbit_direction': 'OrbitDirection',
        'polarisation': 'TransmitterReceiverPolarisation',
        'product_type': 'ProductType'
    }

    return new_names