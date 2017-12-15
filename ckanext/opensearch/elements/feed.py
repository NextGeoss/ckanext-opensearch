# -*- coding: utf-8 -*-
"""Contains classes describing Atom feed elements."""

import uuid
import re
from datetime import datetime

from ckan.common import config, g, request

from . import OSElement
from .entry import Entry
from ckanext.opensearch.config import SHORT_NAME
from ckanext.opensearch.config import SITE_URL


class Feed(OSElement):
    """Define the Atom feed element for OpenSearch responses."""

    def __init__(self, results_dict):
        children = [
            (FeedTitle, None),
            (FeedSubtitle, results_dict),
            (FeedID, None),
            (AtomGenerator, None),
            (FeedAuthor, None),
            (FeedUpdated, None),
            (TotalResults, results_dict),
            (StartIndex, results_dict),
            (ItemsPerPage, results_dict),
            (Query, results_dict),
            (GeoRSSBox, results_dict),
            (AtomSearch, None),
            (SelfLink, None),
            (FirstLink, None),
            (NextLink, results_dict),
            (PrevLink, results_dict),
            (LastLink, results_dict),
            (Entry, results_dict['results'])
        ]
        OSElement.__init__(self, 'atom', 'feed', children=children)


class FeedTitle(OSElement):
    """Define the Atom feed title element."""

    def __init__(self):
        feed_title = '{} OpenSearch Search Results'.format(SHORT_NAME)
        OSElement.__init__(self, 'atom', 'title', content=feed_title)


class FeedSubtitle(OSElement):
    """Define the Atom feed subtitle element."""

    def __init__(self, results_dict):
        total_results = str(results_dict['count'])
        subtitle = '{} results for your search'.format(total_results)
        OSElement.__init__(self, 'atom', 'subtitle', content=subtitle)


class AtomGenerator(OSElement):
    """Define the Atom generator element."""

    def __init__(self):
        attr = {'version': '0.1', 'uri': request.url}
        content = "{} search results".format(SHORT_NAME)
        OSElement.__init__(self, 'atom', 'generator', attr=attr,
                           content=content)


class AtomSearch(OSElement):
    """Define an Atom link for the OpenSearch description document."""

    def __init__(self):
        attr = {'title': 'Description document', 'rel': 'search',
                'type': 'application/opensearchdescription+xml',
                'href': '{}/opensearch/description'.format(SITE_URL)}
        OSElement.__init__(self, 'atom', 'link', attr=attr)


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
        feed_id = request.url
        OSElement.__init__(self, 'atom', 'id', content=feed_id)


class TotalResults(OSElement):
    """Define the OpenSearch element decribing the total results count."""

    def __init__(self, results_dict):
        total_results = str(results_dict['count'])
        OSElement.__init__(self, 'opensearch', 'totalResults',
                           content=total_results)


class StartIndex(OSElement):
    """Describe the start index for the current page of results."""

    def __init__(self, results_dict):
        start_index = str(results_dict['start_index'])
        OSElement.__init__(self, 'opensearch', 'startIndex',
                           content=start_index)


class ItemsPerPage(OSElement):
    """Describe the default number of items per page."""

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
    """Describe the link that will duplicate the search."""

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
    """Describe the link to the next page of search results."""

    def __init__(self, results_dict):
        attr = NavLink.get_link(self, results_dict['next_page'], 'next')
        OSElement.__init__(self, 'atom', 'link', attr=attr)


class PrevLink(OSElement, NavLink):
    """Describe the link to the previous page of search results."""

    def __init__(self, results_dict):
        attr = NavLink.get_link(self, results_dict['prev_page'], 'prev')
        OSElement.__init__(self, 'atom', 'link', attr=attr)


class FirstLink(OSElement, NavLink):
    """Create a link to the first page of search results."""

    def __init__(self):
        attr = NavLink.get_link(self, 1, 'first')
        OSElement.__init__(self, 'atom', 'link', attr=attr)


class LastLink(OSElement, NavLink):
    """Create a link to the last page of search results."""

    def __init__(self, results_dict):
        attr = NavLink.get_link(self, results_dict['last_page'], 'last')
        OSElement.__init__(self, 'atom', 'link', attr=attr)


class GeoRSSBox(OSElement):
    """
    Describe the the bounding box containing all the search results.

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
    """Define the Atom entries element containing all the search results."""

    def __init__(self, results_dict):
        children = [
            (Entry, results_dict['results'])
        ]
        OSElement.__init__(self, 'atom', 'entries', children=children)
