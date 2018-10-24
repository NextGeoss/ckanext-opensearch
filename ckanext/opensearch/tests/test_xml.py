# -*- coding: utf-8 -*-
"""Tests for XML documents."""
import json
import pathlib
from io import BytesIO

from lxml import etree
from parameterized import parameterized
import toml

import ckan.tests.helpers as helpers


HERE = pathlib.Path(__file__).parent

APP = helpers._get_test_app()


def get_relaxng(rng):
    """
    Helper function that returns a local RNG file.

    The RNG files are converted from OGC's RNC files.
    """
    with open(str(HERE / 'relaxng' / rng), 'r') as rng_xml:
        relaxng_doc = etree.parse(rng_xml)

    return etree.RelaxNG(relaxng_doc)


def validate_against_rng(xml, rng):
    """
    Helper function that validates XML against an RNG file.

    Returns True or False.

    Prints the last error if validation fails.
    """
    relaxng = get_relaxng(rng)
    result = relaxng.validate(xml)

    if not result:
        print etree.tostring(xml, pretty_print=True)
        print relaxng.error_log

    return result


def get_xml(request_url):
    """
    Return a parsed description document or Atom feed.

    request_url is relative, i.e.: /opensearch/search.atom
    """
    result = APP.get(url=request_url)
    xml = BytesIO(result.body.encode('utf-8'))

    return etree.parse(xml)


def get_collection_ids():
    """Return a list of collection IDs from the config."""
    filepath = str(HERE.parent / "defaults" / "collections_list.toml")
    with open(filepath, "r") as f:
        collection_params_list = toml.load(f)
        return [_id for _id, details in collection_params_list.items()]


def setup_db():
    """Reset the test database and add some test datasets."""
    helpers.reset_db()
    context = {}
    context.setdefault('user', 'test_user')
    context.setdefault('ignore_auth', True)
    with open(str(HERE / 'json' / 'test_user.json'), 'r') as f:
        params = json.load(f)
        params['email'] = 'test@example.com'
        params['password'] = 'testpassword'
    helpers.call_action('user_create', context, **params)
    with open(str(HERE / 'json' / 'test_org.json'), 'r') as f:
        params = json.load(f)
    helpers.call_action('organization_create', context, **params)
    with open(str(HERE / 'json' / 'test_record.json'), 'r') as f:
        params = json.load(f)
    helpers.call_action('package_create', context, **params)


setup_db()

collection_ids = get_collection_ids()
collection_ids.extend(["collection", "dataset"])

description_docs = [(get_xml('/opensearch/description.xml?osdd={}'
                    .format(collection_id)),)
                    for collection_id in collection_ids]


class TestDescriptionDocuments(object):
    """Class for collection OSDD tests."""

    @parameterized(description_docs)
    def test_is_valid_osdd(self, osdd):
        """Check if the OSDD is valid according to OCG's schema."""
        assert validate_against_rng(osdd, 'schemas/osdd.rng')

    @parameterized(description_docs)
    def test_is_valid_osddgeo(self, osdd):
        """
        Check if the OSDD geo elements are valid according to OGC's schema.
        """
        assert validate_against_rng(osdd, 'schemas/osddgeo.rng')

    @parameterized(description_docs)
    def test_is_valid_osddtime(self, osdd):
        """
        Check if the OSDD time elements are valid according to OGC's schema.
        """
        assert validate_against_rng(osdd, 'schemas/osddtime.rng')

    @parameterized(description_docs)
    def test_result_osdd(self, osdd):
        """Check if the OSDD passes OGC's result-osd test."""
        assert validate_against_rng(osdd, 'tests/result-osd.rng')

    @parameterized(description_docs)
    def test_result_osddgeo(self, osdd):
        """Check if the OSDD passes OGC's result-osdggeo test."""
        assert validate_against_rng(osdd, 'tests/result-osddgeo.rng')

    @parameterized(description_docs)
    def test_result_searchbygeometry(self, osdd):
        """Check if the OSDD passes OGC's result-searchbygeometry test."""
        assert validate_against_rng(osdd,
                                    'tests/result-searchbygeometry.rng')

    @parameterized(description_docs)
    def test_result_searchbyid(self, osdd):
        """Check if the OSDD passes OGC's result-searchbyid test."""
        assert validate_against_rng(osdd, 'tests/result-searchbyid.rng')

    @parameterized(description_docs)
    def test_result_searchbyname(self, osdd):
        """Check if the OSDD passes OGC's result-searchbyname test."""
        assert validate_against_rng(osdd, 'tests/result-searchbyname.rng')

    @parameterized(description_docs)
    def test_result_searchbypointradius(self, osdd):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(osdd,
                                    'tests/result-searchbypointradius.rng')

    @parameterized(description_docs)
    def test_result_searchbytime(self, osdd):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(osdd, 'tests/result-searchbytime.rng')

    @parameterized(description_docs)
    def test_result_spatialrelations(self, osdd):
        """Check if the OSDD passes OGC's result-spatialrelations test."""
        assert validate_against_rng(osdd,
                                    'tests/result-spatialrelations.rng')

    @parameterized(description_docs)
    def test_result_timerelations(self, osdd):
        """Check if the OSDD passes OGC's result-timerelations test."""
        assert validate_against_rng(osdd,
                                    'tests/result-timerelations.rng')


class TestCollectionResultsFeed(object):
    """Class for collection (step one) search results tests."""

    def __init__(self):
        """Initialize the class with a parsed results feed."""
        self.atom_feed = get_xml('/opensearch/collection_search.atom?q=*')

    def test_is_valid_atom_feed(self):
        """Check if the feed is valid according to OGC's Atom schema."""
        assert validate_against_rng(self.atom_feed, 'schemas/atom_feed.rng')

    def test_is_valid_osatom(self):
        """
        Check if the feed is a valid according to OGC's OpenSearch schema.
        """
        assert validate_against_rng(self.atom_feed, 'schemas/osatom.rng')

    def test_result_atom(self):
        """Check if the OSDD passes OGC's result-atom test."""
        assert validate_against_rng(self.atom_feed, 'tests/result-atom.rng')


class TestProductResultsFeed(object):
    """Class for product (step two) search results tests."""

    def __init__(self):
        """Initialize the class with a parsed results feed."""

        self.atom_feed = get_xml('/opensearch/search.atom?')

    def test_is_valid_atom_feed(self):
        """Check if the feed is valid according to OGC's Atom schema."""
        assert validate_against_rng(self.atom_feed, 'schemas/atom_feed.rng')

    def test_is_valid_osatom(self):
        """
        Check if the feed is a valid according to OGC's OpenSearch schema.
        """
        assert validate_against_rng(self.atom_feed, 'schemas/osatom.rng')

    def test_result_atom(self):
        """Check if the OSDD passes OGC's result-atom test."""
        assert validate_against_rng(self.atom_feed, 'tests/result-atom.rng')
