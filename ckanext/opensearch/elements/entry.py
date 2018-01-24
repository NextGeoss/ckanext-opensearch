# -*- coding: utf-8 -*-
"""Contains classes for the entries in an OpenSearch feed."""
from ckan.lib import helpers as h
from ckan.common import request

from . import OSElement
from .earth_observation import EarthObservation


class Entry(OSElement):
    """Define an OpenSearch Entry element."""

    def __init__(self, entry_dict):
        if entry_dict.get('is_collection', False):
            children = [
                (CollectionTitle, entry_dict),
                (CollectionID, entry_dict),
                (CollectionIdentifier, entry_dict),
                (CollectionPublished, entry_dict),
                (CollectionUpdated, entry_dict),
                (CollectionDescription, entry_dict),
                (CollectionDescribedBy, entry_dict),
                (CollectionOSDD, entry_dict),
                (CollectionVia, entry_dict),
            ]
        else:
            extras_dict = dict()
            if 'extras' in entry_dict:
                for extra in entry_dict['extras']:
                    extras_dict[extra['key']] = extra['value']
            entry_dict['extras'] = extras_dict

            children = [
                (EntryTitle, entry_dict),
                (EntryID, entry_dict),
                (EntryIdentifier, entry_dict),
                (EntryPublisher, entry_dict),
                (EntryPublished, entry_dict),
                (EntryUpdated, entry_dict),
                (EntrySummary, entry_dict),
                (EntryDCDate, entry_dict),
                (EntryRights, entry_dict),
                (DatasetLink, entry_dict),
                (EntryCategory, entry_dict['tags']),
                (ResourceLink, entry_dict['resources']),
            ]
        OSElement.__init__(self, 'atom', 'entry', children=children)


class CollectionTitle(OSElement):
    """Define a collection element title."""

    def __init__(self, data_dict):
        title = data_dict['collection_title']
        OSElement.__init__(self, 'atom', 'title', content=title)


class CollectionID(OSElement):
    """Define a collection entry's Atom ID element."""

    def __init__(self, data_dict):
        identifier = data_dict['collection_id']
        OSElement.__init__(self, 'atom', 'id', content=identifier)


class CollectionIdentifier(OSElement):
    """Define the Dubin Core identifier element of an OpenSearch entry."""

    def __init__(self, data_dict):
        identifier = data_dict['collection_id']
        OSElement.__init__(self, 'dc', 'identifier', content=identifier)


class CollectionPublished(OSElement):
    """Define an atom:published element for a collection result."""

    def __init__(self, data_dict):
        content = data_dict['collection_published']
        OSElement.__init__(self, 'atom', 'published', content=content)


class CollectionUpdated(OSElement):
    """Define an atom:updated element for a collection result."""

    def __init__(self, data_dict):
        content = data_dict['collection_updated']
        OSElement.__init__(self, 'atom', 'updated', content=content)


class CollectionDescription(OSElement):
    """Define a collection element title."""

    def __init__(self, data_dict):
        title = data_dict.get('collection_description', 'No description')
        OSElement.__init__(self, 'atom', 'summary', content=title)


class CollectionCount(OSElement):
    """Define an element containing the count of a collection."""

    def __init__(self, data_dict):
        count = str(data_dict.get('collection_count', 0))
        OSElement.__init__(self, 'atom', 'count', content=count)


class CollectionDescribedBy(OSElement):
    """URL pointing to a description of the collection."""
    # We can include pages on the Data Hub with info about the collections and
    # point there instead of to the original pages in the future.

    def __init__(self, data_dict):
        collection_name = data_dict['collection_name']
        if 'urn:ogc:def:EOP:VITO' in collection_name:
            url = 'http://www.vito-eodata.be/collections/srv/eng/main.home?uuid=' + collection_name
        elif 'Sentinel' in collection_name:
            url = 'https://sentinels.copernicus.eu/web/sentinel'
        else:
            url = 'http://example.com'

        link = {
            'href': url,
            'rel': 'describedBy',
            'type': 'text/html'
        }
        OSElement.__init__(self, 'atom', 'link', attr=link)

class CollectionOSDD(OSElement):
    """
    Define an element containing a link to the OpenSearch description
    document for a given collection.
    """

    def __init__(self, data_dict):
        base_url = request.url.split('opensearch')[0] + 'opensearch/description.xml?osdd='
        url = base_url + data_dict['collection_id']
        attr = {'rel': 'search',
                'type': 'application/opensearchdescription+xml',
                'href': url}
        OSElement.__init__(self, 'atom', 'link', attr=attr)


class CollectionVia(OSElement):
    """URL pointing to a metadata representation of the collection at the source."""
    # We can include pages on the Data Hub with info about the collections and
    # point there instead of to the original pages in the future.

    def __init__(self, data_dict):
        collection_name = data_dict['collection_name']
        if 'urn:ogc:def:EOP:VITO' in collection_name:
            url = 'http://www.vito-eodata.be/collections/srv/eng/xml_iso19139?uuid=' + collection_name
            content_type = 'application/vnd.iso.19139+xml'
        elif 'Sentinel' in collection_name:
            url = 'https://sentinels.copernicus.eu/web/sentinel'
            content_type = 'text/html'
        else:
            url = 'http://example.com'
            content_type = 'text/html'

        link = {
            'href': url,
            'rel': 'via',
            'type': content_type
        }
        OSElement.__init__(self, 'atom', 'link', attr=link)


class EntryTitle(OSElement):
    """Define the title element of an OpenSearch entry."""

    def __init__(self, data_dict):
        title = data_dict.get('title', 'Untitled')
        OSElement.__init__(self, 'atom', 'title', content=title)


class EntryID(OSElement):
    """
    Define the ID element of an OpenSearch entry.

    Here we define the ID as the URL  of the dataset created using the
    CKAN ID of the dataset.
    """

    def __init__(self, data_dict):
        # Prefer creating links with the ID vs. the name because
        # the ID won't change.
        entry_id = h.url_for(controller='package',
                             action='read',
                             id=data_dict['id'], qualified=True)
        OSElement.__init__(self, 'atom', 'id', content=entry_id)


class EntryIdentifier(OSElement):
    """Define the Dubin Core identifier element of an OpenSearch entry."""

    def __init__(self, data_dict):
        identifier = data_dict['id']
        OSElement.__init__(self, 'dc', 'identifier', content=identifier)


class EntryAuthor(OSElement):
    """Define the author element of an OpenSearch entry."""

    def __init__(self, entry_dict):
        children = [
            (EntryAuthorName, entry_dict)
        ]
        OSElement.__init__(self, 'atom', 'author', children=children)


class EntryAuthorName(OSElement):
    """
    Define the author name element of an OpenSearch entry.

    Only use the CKAN author if the CKAN organization is not available.
    """

    def __init__(self, data_dict):
        try:
            author = data_dict['organization'].get('title')
        except (AttributeError, KeyError):
            author = data_dict.get('author')
        OSElement.__init__(self, 'atom', 'name', content=author)


class EntryAuthorEmail(OSElement):
    """Define the author email element of an OpenSearch entry."""

    def __init__(self, data_dict):
        email = data_dict.get('author_email')
        OSElement.__init__(self, 'atom', 'email', content=email)


class EntryPublisher(OSElement):
    """
    Define the publisher element of the dataset in the OpenSearch entry.

    The publisher will usually be the organization associated with the dataset.
    """

    def __init__(self, data_dict):
        try:
            publisher = data_dict['organization'].get('title')
        except (AttributeError, KeyError):
            publisher = data_dict.get('author', 'No publisher info available')
        OSElement.__init__(self, 'dc', 'publisher', content=publisher)


class EntryUpdated(OSElement):
    """Describe when the entry (dataset) was last updated."""

    def __init__(self, data_dict):
        updated = data_dict['metadata_modified'] + 'Z'
        OSElement.__init__(self, 'atom', 'updated', content=updated)


class EntryPublished(OSElement):
    """Describe when the entry (dataset) was first published."""

    def __init__(self, data_dict):
        published = data_dict['metadata_created'] + 'Z'
        OSElement.__init__(self, 'atom', 'published', content=published)


class EntryRights(OSElement):
    """Define the rights element of the OpenSearch entry."""

    def __init__(self, data_dict):
        license = data_dict.get('license_title',
                                'No license information available')
        OSElement.__init__(self, 'atom', 'rights', content=license)


class DatasetLink(OSElement):
    """
    URL for the dataset on CKAN.
    """

    def __init__(self, data_dict):
        # Prefer creating links with the ID vs. the name because
        # the ID won't change.
        url = h.url_for(controller='package',
                        action='read', id=data_dict['id'], qualified=True)
        link = {
            'href': url,
            'rel': 'describedBy',
            'type': 'text/html'
        }
        OSElement.__init__(self, 'atom', 'link', attr=link)


class EntrySummary(OSElement):
    """
    Define the element containing the summary of the entry.

    The dataset description is used for the summary.
    """

    def __init__(self, data_dict):
        summary = data_dict.get('notes', 'No summary available.')
        OSElement.__init__(self, 'atom', 'summary', content=summary)


class EntryDCDate(OSElement):
    """Define a DC date element representing the timespan of the result."""

    def __init__(self, data_dict):
        start = data_dict['extras'].get('StartTime', '')
        end = data_dict['extras'].get('StopTime', '')
        date_range = '{}/{}'.format(start, end)
        OSElement.__init__(self, 'dc', 'date', content=date_range)


class AtomContent(OSElement):
    """
    Define the Atom contnet element for an entry.
    """

    def __init__(self, data_dict):
        content = data_dict.get('notes', 'No summary available.')
        OSElement.__init__(self, 'atom', 'content', content=content)


class EntryCategory(OSElement):
    """
    Define an Atom element describing a feed entry.

    In this case, each category is a CKAN tag.
    There can be more than one category element in an entry.
    """

    def __init__(self, tag_dict):
        attr = {'term': tag_dict['name']}
        OSElement.__init__(self, 'atom', 'category', attr=attr)


class ResourceLink(OSElement):
    """
    Define an Atom element describing a link to a datset's resource.

    There can be more than one resource link in an entry.
    """

    def __init__(self, resource_dict):
        # TODO: create a MIME-type mapper
        mime_type = 'application/octect-stream'
        if resource_dict.get('name', None) != 'Thumbnail Link':
            link = {
                'href': resource_dict['url'],
                'title': resource_dict.get('name', 'Untitled'),
                'rel': 'enclosure',
                'type': mime_type
            }
        else:
            link = {
                'href': resource_dict['url'],
                'title': 'Quicklook image',
                'rel': 'icon',
                'type': mime_type
            }
        OSElement.__init__(self, 'atom', 'link', attr=link)


class ThumbnailLink(OSElement):
    """Define an Atom element linking to the quicklook/thumbnail for a dataset."""

    def __init__(self, entry_dict):
        thumbnail = OSElement._get_from_extras(self, entry_dict, ['thumbnail'])
        if thumbnail:
            link = {
                'href': thumbnail,
                'title': 'Quicklook image',
                'rel': 'icon'
            }
        else:
            link = {}
        OSElement.__init__(self, 'atom', 'link', attr=link)


class EntryGEORSSPolygon(OSElement):
    """Define a GEORSS polygon element based on an entry's spatial value."""

    def __init__(self, entry_dict):
        spatial = entry_dict['extras'].get('spatial', None)
        if spatial:
            coordinates = spatial['coordinates'][0]
            coord_list = []
            for i in coordinates:
                coord_list.append(str(i[0]))
                coord_list.append(str(i[1]))
            coord_str = ' '.join(coord_list)
        else:
            coord_str = ''
        OSElement.__init__(self, 'georss', 'polygon', content=coord_str)
