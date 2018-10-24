# -*- coding: utf-8 -*-
import json

from ckan.lib.helpers import get_pkg_dict_extra

from .config import SITE_URL


def make_collection_via(entry):
    """URL pointing to the source's metadata about the collection."""
    # We can include pages on the Data Hub with info about the collections and
    # point there instead of to the original pages in the future.
    collection_id = entry.get("collection_id") or entry.get("id")
    if 'urn:ogc:def:EOP:VITO' in collection_id:
        url = 'http://www.vito-eodata.be/collections/srv/eng/xml_iso19139?uuid={}'.format(collection_id)  # noqa: E501
        content_type = 'application/vnd.iso.19139+xml'
    elif 'SENTINEL' in collection_id:
        url = 'https://sentinels.copernicus.eu/web/sentinel'
        content_type = 'text/html'
    else:
        url = 'http://example.com'
        content_type = 'text/html'

    return {'href': url, 'type': content_type, 'rel': 'via'}


def make_entry_polygon(entry):
    """Define a GEORSS polygon element based on an entry's spatial value."""
    spatial = get_pkg_dict_extra(entry, 'spatial', '')
    if spatial:
        spatial = json.loads(spatial)
        coordinates = spatial['coordinates'][0]
        coord_list = []
        for i in coordinates:
            coord_list.append(str(i[0]))
            coord_list.append(str(i[1]))
        coord_str = ' '.join(coord_list)
    else:
        coord_str = ''

    return coord_str


def make_entry_resource(resource):
    """
    Define an Atom element describing a link to a datset's resource.

    There can be more than one resource link in an entry.
    """
    default = 'application/octet-stream'
    mime_type = resource.get('mimetype') or default
    name = resource.get('name', 'Untitled')
    if name.startswith('Metadata Download'):
        link = {
            'href': resource['url'],
            'title': name,
            'rel': 'via',
            'type': mime_type
        }
    elif name.startswith('Thumbnail Download'):
        link = {
            'href': resource['url'],
            'title': 'Quicklook image',
            'rel': 'icon',
            'type': mime_type
        }
    else:
        link = {
            'href': resource['url'],
            'title': name,
            'rel': 'enclosure',
            'type': mime_type,
            'length': str(resource.get('size', ''))
        }

    return link
