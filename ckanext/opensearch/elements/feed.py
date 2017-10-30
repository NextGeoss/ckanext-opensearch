import uuid
import re
from datetime import datetime
# -*- coding: utf-8 -*-
from ckan.common import config, g, request

from . import OSElement
from .entry import Entry


class Feed(OSElement):
    """Define the Atom feed element for OpenSearch responses."""

    def __init__(self, results_dict):
        children = [
            (FeedTitle, None),
            (FeedLink, None),
            (FeedUpdated, None),
            (FeedAuthor, None),
            (FeedID, None),
            (TotalResults, results_dict),
            (StartIndex, results_dict),
            (ItemsPerPage, results_dict),
            (Query, results_dict),
            (GeoRSSBox, results_dict),
            (SelfLink, None),
            (NextLink, results_dict),
            (PrevLink, results_dict),
            (Entries, results_dict)
        ]
        OSElement.__init__(self, 'atom', 'feed', children=children)


class FeedTitle(OSElement):
    """Define the Atom feed title element."""

    def __init__(self):
        site_title = g.site_title or 'CKAN'
        feed_title = '{} OpenSearch Search Results'.format(site_title)
        OSElement.__init__(self, 'atom', 'title', content=feed_title)


class FeedLink(OSElement):
    """Define the URL used for accessing the OpenSearch service itself."""

    def __init__(self):
        url = '{}/opensearch/description'.format(g.site_url)
        link = {
            'href': url
        }
        OSElement.__init__(self, 'atom', 'link', attr=link)


class FeedUpdated(OSElement):
    """Define the element describing when the feed was las updated."""

    def __init__(self):
        updated = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        OSElement.__init__(self, 'atom', 'updated', content=updated)


class FeedAuthor(OSElement):
    """Define the Atom element holding the feed author details."""

    def __init__(self):
        children = [
            (FeedAuthorName, None)
        ]
        OSElement.__init__(self, 'atom', 'author', children=children)


class FeedAuthorName(OSElement):
    """Define the Atom element describing the name of the feed author."""

    def __init__(self):
        name = config.get('ckanext.opensearch.author',
            'No author information available')
        OSElement.__init__(self, 'atom', 'name', content=name)


class FeedID(OSElement):
    """Define the Atom element describing the ID of the feed."""

    def __init__(self):
        feed_id = 'urn:uuid' + str(uuid.uuid5(uuid.NAMESPACE_URL, request.url))
        OSElement.__init__(self, 'atom', 'id', content=feed_id)


class TotalResults(OSElement):
    """Define the OpenSearch element decribing the total results for the search."""
    def __init__(self, results_dict):
        total_results = str(results_dict['count'])
        OSElement.__init__(self, 'opensearch', 'totalResults', content=total_results)


class StartIndex(OSElement):
    """
    Define the OpenSearch element describing the start index for the current
    page of results.
    """

    def __init__(self, results_dict):
        start_index = str(results_dict['start_index'])
        OSElement.__init__(self, 'opensearch', 'startIndex', content=start_index)


class ItemsPerPage(OSElement):
    """
    Define the OpenSearch element describing the default number of items
    per page.
    """

    def __init__(self, results_dict):
        items_per_page = str(results_dict['items_per_page'])
        OSElement.__init__(self, 'opensearch', 'itemsPerPage',
            content=items_per_page)


class Query(OSElement):
    """Define the OpenSearch element describing the query itself."""

    def __init__(self, results_dict):
        query = results_dict['query']
        OSElement.__init__(self, 'opensearch', 'Query', content=query)


class SelfLink(OSElement):
    """
    Define the OpenSearch element describing the link to duplicate
    the search. URL comes from request.url
    """

    def __init__(self):
        link = {
            'href': request.url, 
            'title': 'self', 
            'rel': 'self',
            'type': 'application/atom+xml'
        }
        OSElement.__init__(self, 'atom', 'link', attr=link)


class NavLink(object):
    """Define the skeleton of an Atom next/previous link."""

    def get_link(self, page, rel):
        """
        Return a dictionary describing the link for next/previous page
        or an empty dictionary if there is no next/previous page.
        """
        attr = {
            'title': rel,
            'rel': rel,
            'type': 'application/atom+xml'
        }
        if page:
            page = str(page)
            current_url = request.url
            if 'page=' not in current_url:
                link_url = current_url + '&page=' + page
            else:
                halves = re.compile('page=\d*').split(current_url)
                if len(halves) == 1:
                    link_url = halves[0] + '&page=' + page
                else:
                    link_url = halves[0] + 'page=' + page + halves[1]
            attr['href'] = link_url
        else:
            attr['href'] = ''
        return attr


class NextLink(OSElement, NavLink):
    """
    Define the Atom element describing the link to the next page of 
    search results.
    """

    def __init__(self, results_dict):
        attr = NavLink.get_link(self, results_dict['next_page'], 'next')
        OSElement.__init__(self, 'atom', 'link', attr=attr)


class PrevLink(OSElement, NavLink):
    """
    Define the Atom element describing the link to the previous page of
    search results.
    """

    def __init__(self, results_dict):
        attr = NavLink.get_link(self, results_dict['prev_page'], 'prev')
        OSElement.__init__(self, 'atom', 'link', attr=attr)


class GeoRSSBox(OSElement):
    """
    Define the GeoRSS element describing the bounding box containing all the
    search results in the feed.

    CKAN's bounding box is a comma-delimted string, but georss and other
    formats expect space-delimeted strings.
    """

    def __init__(self, results_dict):
        bbox_param = '{http://a9.com/-/opensearch/extensions/geo/1.0/}box'
        bbox = results_dict['query'].get(bbox_param)
        if bbox:
            georss_box = bbox.replace(',', ' ')
        else:
            georss_box = None
        # If there was no bounding box in the query, then the resulting
        # element will be empty.
        OSElement.__init__(self, 'georss', 'box', content=georss_box)


class Entries(OSElement):
    """ Define the Atom entries element containing all the search results."""

    def __init__(self, results_dict):
        children = [
            (Entry, results_dict['results'])
        ]
        OSElement.__init__(self, 'atom', 'entries', children=children)