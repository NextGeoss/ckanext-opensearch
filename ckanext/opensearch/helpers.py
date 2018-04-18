import json
from datetime import datetime

from .config import (COLLECTIONS,
                     SITE_URL)


def make_attributes(attr_dict):
    """
    Convert a dictionary of attributes into a string for use in XML.

    Example: {'title': 'This is an example', 'rel': 'example'} becomes
    'title="This is an example" rel="example"'
    """

    attr_list = ['{0}="{1}"'.format(key, value)
                 for key, value
                 in attr_dict.items()
                 if value]
    if attr_list:
        return ' '.join(attr_list)
    else:
        return ''


def make_collection_id(self_url, entry):
    """Define a collection entry's Atom ID element."""
    base_url = '{}opensearch/search.atom?collection_id='.format(
        self_url.split('opensearch')[0])

    return base_url + entry['collection_id']


def make_collection_updated():
    """
    Define an atom:updated element for a collection result.

    Hardcoded for now until we decide how to represent collections in the db.
    """
    return datetime.utcnow().strftime('%Y-%m-%dT00:00:00.000Z')


def make_collection_dc_date(entry):
    """Define a DC date element representing the timespan of the result."""
    collection_id = entry['collection_id']
    if collection_id.startswith('SENTINEL1'):
        start = '2014-10-06T00:00:00.000Z'
    elif collection_id.startswith('SENTINEL2'):
        start = '2015-06-27T00:00:00.000Z'
    elif collection_id.startswith('SENTINEL3'):
        start = '2016-02-29T00:00:00.000Z'
    else:
        start = ''
    end = datetime.utcnow().strftime('%Y-%m-%dT00:00:00.000Z')

    return '{}/{}'.format(start, end)


def make_collection_box():
    """
    Define a GEORSS box element based on an collection's spatial extent.

    Hardcoded until we get clarification about how to determine or define the
    bounding box of a collection.
    """
    return '-180.0 -90.0 180.0 90.0'


def make_collection_polygon():
    """
    Define a GEORSS polygon element based on an collection's spatial value.

    Hardcoded for now pending clarification.
    """
    return '-180 -90 -180 90 180 90 180 -90 -180 90'


def make_collection_summary(entry):
    """Define a collection's summary text."""
    title = entry.get('collection_title', 'untitled')
    count = entry.get('collection_count', 0)
    return '{} matching products found in the {} collection.'.format(count,
                                                                     title)


def make_collection_content(entry):
    """Define the Atom content element for an entry."""

    return entry.get('collection_description', 'No description available.')


def make_search_element_attrs(params, query_url):
    """
    Make the attributes for the element describing how to access the
    description document related to a given search.
    """
    osdd = params.get('collection_id')
    if osdd in COLLECTIONS:
        title = '{} description document'.format(osdd)
        href = ('{}/opensearch/description.xml?osdd={}'
                .format(SITE_URL, osdd))
    elif 'view_record' in query_url:
        title = 'Record view description document'
        href = ('{}/opensearch/description.xml?osdd={}'
                .format(SITE_URL, 'record'))
    elif 'collection_search' in query_url:
        title = 'Collection description document'
        href = '{}/opensearch/description.xml?osdd=collection'.format(SITE_URL)
    else:
        title = 'Dataset search description document'
        href = '{}/opensearch/description.xml?osdd=dataset'.format(SITE_URL)
    attrs = {'title': title, 'rel': 'search',
             'type': 'application/opensearchdescription+xml',
             'href': href}

    return attrs


def make_collection_search_url(entry):
    """Create the collection search URL for a given dataset."""
    return ('{}/opensearch/description.xml?osdd={}'
            .format(SITE_URL, entry['collection_id']))


def make_collection_via(entry):
    """URL pointing to the source's metadata about the collection."""
    # We can include pages on the Data Hub with info about the collections and
    # point there instead of to the original pages in the future.
    collection_id = entry['collection_id']
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


def make_entry_atom_id(entry):
    """
    Define the ID element of an OpenSearch entry.

    Here we define the ID as the URL of the dataset created using the
    CKAN ID of the dataset.
    """
    # As requested by Pedro for use with the VITO application
    atom_id = '{}/opensearch/view_record.atom?&identifier={}'.format(
        SITE_URL, get_from_extras(entry, 'identifier'))

    return atom_id


def make_entry_dc_identifier(entry):
    """Define the dc:identifier element of an OpenSearch entry."""
    # As requested by Pedro for use with the VITO application
    return get_from_extras(entry, 'identifier')


def make_entry_dc_date(entry):
    """Define a DC date element representing the timespan of the result."""
    start = get_from_extras(entry, 'StartTime')
    end = get_from_extras(entry, 'StopTime')
    if start == end:
        date = start
    else:
        date = '{}/{}'.format(start, end)

    return date


def make_entry_polygon(entry):
    """Define a GEORSS polygon element based on an entry's spatial value."""
    spatial = get_from_extras(entry, 'spatial')
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


def make_entry_summary(entry):
    """
    Define the element containing the summary of the entry.

    The dataset description is used for the summary.
    """
    return entry.get('notes', 'No summary available.')


def make_entry_self_url(entry):
    """Define an atom self link for each entry."""
    # As requested by Pedro for use with the VITO application
    collection = get_from_extras(entry, 'collection_id')
    identifier = get_from_extras(entry, 'identifier')
    url = '{}/opensearch/search.atom?collection_id={}&identifier={}'.format(
        SITE_URL, collection, identifier)

    return url


def make_entry_collection_url(entry):
    """
    Define an Atom link with rel="up" for a product's collection.

    For now, products can only belong to one collection and the collection
    link will always be displayed.
    """
    collection = get_from_extras(entry, 'collection_id')
    if collection:
        return '{}?collection_id={}'.format(SITE_URL, collection)
    else:
        return None


def make_entry_publisher(entry):
    """
    Define the publisher element of the dataset in the OpenSearch entry.

    The publisher will usually be the organization associated with the dataset.
    """
    try:
        publisher = entry['organization'].get('title')
        assert publisher
    except (AttributeError, KeyError, AssertionError):
        publisher = entry.get('author', 'No publisher info available')

    return publisher


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


def get_from_extras(data_dict, term):
    """Get the value of an extra."""
    extras = data_dict.get('extras', [])

    for extra in extras:
        if extra['key'] == term:
            return extra['value']

    return ''


def filter_options(param):
    """Remove the options from a param dict."""
    return {key: value for key, value in param.items() if key != 'options'}
