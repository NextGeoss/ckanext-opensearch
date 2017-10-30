"""Tests for XML documents."""
import json
import pathlib
from io import BytesIO

from lxml import etree

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


class TestCollectionDescriptionDocument(object):
    """Class for collection OSDD tests."""

    def __init__(self):
        """Initialize the class with a parsed OSDD."""
        self.osdd = get_xml('/opensearch/description.xml?osdd=collection')

    def test_is_valid_osdd(self):
        """Check if the OSDD is valid according to OCG's schema."""
        assert validate_against_rng(self.osdd, 'schemas/osdd.rng')

    def test_is_valid_osddgeo(self):
        """
        Check if the OSDD geo elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddgeo.rng')

    def test_is_valid_osddtime(self):
        """
        Check if the OSDD time elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddtime.rng')

    def test_result_osd(self):
        """Check if the OSDD passes OGC's result-osd test."""
        assert validate_against_rng(self.osdd, 'tests/result-osd.rng')

    def test_result_osddgeo(self):
        """Check if the OSDD passes OGC's result-osdggeo test."""
        assert validate_against_rng(self.osdd, 'tests/result-osddgeo.rng')

    def test_result_searchbygeometry(self):
        """Check if the OSDD passes OGC's result-searchbygeometry test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbygeometry.rng')

    def test_result_searchbyid(self):
        """Check if the OSDD passes OGC's result-searchbyid test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyid.rng')

    def test_result_searchbyname(self):
        """Check if the OSDD passes OGC's result-searchbyname test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyname.rng')

    def test_result_searchbypointradius(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbypointradius.rng')

    def test_result_searchbytime(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbytime.rng')

    def test_result_spatialrelations(self):
        """Check if the OSDD passes OGC's result-spatialrelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-spatialrelations.rng')

    def test_result_timerelations(self):
        """Check if the OSDD passes OGC's result-timerelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-timerelations.rng')


class TestRecordDescriptionDocument(object):
    """Class for record OSDD tests."""

    def __init__(self):
        """Initialize the class with a parsed OSDD."""
        self.osdd = get_xml('/opensearch/description.xml?osdd=record')

    def test_is_valid_osdd(self):
        """Check if the OSDD is valid accoridng to OCG's schema."""
        assert validate_against_rng(self.osdd, 'schemas/osdd.rng')

    def test_result_osd(self):
        """Check if the OSDD passes OGC's result-osd test."""
        assert validate_against_rng(self.osdd, 'tests/result-osd.rng')

    def test_result_searchbyid(self):
        """Check if the OSDD passes OGC's result-searchbyid test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyid.rng')


class TestSENTINEL1_L1_SLCDescriptionDocument(object):
    """Class for SENTINEL1_L1_SLC OSDD tests."""

    def __init__(self):
        """Initialize the class with a parsed OSDD."""
        self.osdd = get_xml('/opensearch/description.xml?osdd=SENTINEL1_L1_SLC')  # noqa: E501

    def test_is_valid_osdd(self):
        """Check if the OSDD is valid according to OCG's schema."""
        assert validate_against_rng(self.osdd, 'schemas/osdd.rng')

    def test_is_valid_osddgeo(self):
        """
        Check if the OSDD geo elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddgeo.rng')

    def test_is_valid_osddtime(self):
        """
        Check if the OSDD time elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddtime.rng')

    def test_result_osd(self):
        """Check if the OSDD passes OGC's result-osd test."""
        assert validate_against_rng(self.osdd, 'tests/result-osd.rng')

    def test_result_osddgeo(self):
        """Check if the OSDD passes OGC's result-osdggeo test."""
        assert validate_against_rng(self.osdd, 'tests/result-osddgeo.rng')

    def test_result_searchbygeometry(self):
        """Check if the OSDD passes OGC's result-searchbygeometry test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbygeometry.rng')

    def test_result_searchbyid(self):
        """Check if the OSDD passes OGC's result-searchbyid test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyid.rng')

    def test_result_searchbyname(self):
        """Check if the OSDD passes OGC's result-searchbyname test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyname.rng')

    def test_result_searchbypointradius(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbypointradius.rng')

    def test_result_searchbytime(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbytime.rng')

    def test_result_spatialrelations(self):
        """Check if the OSDD passes OGC's result-spatialrelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-spatialrelations.rng')

    def test_result_timerelations(self):
        """Check if the OSDD passes OGC's result-timerelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-timerelations.rng')


class TestSENTINEL1_L1_GRDDescriptionDocument(object):
    """Class for SENTINEL1_L1_GRD OSDD tests."""

    def __init__(self):
        """Initialize the class with a parsed OSDD."""
        self.osdd = get_xml('/opensearch/description.xml?osdd=SENTINEL1_L1_GRD')  # noqa: E501

    def test_is_valid_osdd(self):
        """Check if the OSDD is valid according to OCG's schema."""
        assert validate_against_rng(self.osdd, 'schemas/osdd.rng')

    def test_is_valid_osddgeo(self):
        """
        Check if the OSDD geo elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddgeo.rng')

    def test_is_valid_osddtime(self):
        """
        Check if the OSDD time elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddtime.rng')

    def test_result_osd(self):
        """Check if the OSDD passes OGC's result-osd test."""
        assert validate_against_rng(self.osdd, 'tests/result-osd.rng')

    def test_result_osddgeo(self):
        """Check if the OSDD passes OGC's result-osdggeo test."""
        assert validate_against_rng(self.osdd, 'tests/result-osddgeo.rng')

    def test_result_searchbygeometry(self):
        """Check if the OSDD passes OGC's result-searchbygeometry test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbygeometry.rng')

    def test_result_searchbyid(self):
        """Check if the OSDD passes OGC's result-searchbyid test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyid.rng')

    def test_result_searchbyname(self):
        """Check if the OSDD passes OGC's result-searchbyname test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyname.rng')

    def test_result_searchbypointradius(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbypointradius.rng')

    def test_result_searchbytime(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbytime.rng')

    def test_result_spatialrelations(self):
        """Check if the OSDD passes OGC's result-spatialrelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-spatialrelations.rng')

    def test_result_timerelations(self):
        """Check if the OSDD passes OGC's result-timerelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-timerelations.rng')


class TestSENTINEL1_L2_OCNDescriptionDocument(object):
    """Class for SENTINEL1_L2_OCN OSDD tests."""

    def __init__(self):
        """Initialize the class with a parsed OSDD."""
        self.osdd = get_xml('/opensearch/description.xml?osdd=SENTINEL1_L2_OCN')  # noqa: E501

    def test_is_valid_osdd(self):
        """Check if the OSDD is valid according to OCG's schema."""
        assert validate_against_rng(self.osdd, 'schemas/osdd.rng')

    def test_is_valid_osddgeo(self):
        """
        Check if the OSDD geo elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddgeo.rng')

    def test_is_valid_osddtime(self):
        """
        Check if the OSDD time elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddtime.rng')

    def test_result_osd(self):
        """Check if the OSDD passes OGC's result-osd test."""
        assert validate_against_rng(self.osdd, 'tests/result-osd.rng')

    def test_result_osddgeo(self):
        """Check if the OSDD passes OGC's result-osdggeo test."""
        assert validate_against_rng(self.osdd, 'tests/result-osddgeo.rng')

    def test_result_searchbygeometry(self):
        """Check if the OSDD passes OGC's result-searchbygeometry test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbygeometry.rng')

    def test_result_searchbyid(self):
        """Check if the OSDD passes OGC's result-searchbyid test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyid.rng')

    def test_result_searchbyname(self):
        """Check if the OSDD passes OGC's result-searchbyname test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyname.rng')

    def test_result_searchbypointradius(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbypointradius.rng')

    def test_result_searchbytime(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbytime.rng')

    def test_result_spatialrelations(self):
        """Check if the OSDD passes OGC's result-spatialrelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-spatialrelations.rng')

    def test_result_timerelations(self):
        """Check if the OSDD passes OGC's result-timerelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-timerelations.rng')


class TestSENTINEL2_L1CDescriptionDocument(object):
    """Class for SENTINEL2_L1C OSDD tests."""

    def __init__(self):
        """Initialize the class with a parsed OSDD."""
        self.osdd = get_xml('/opensearch/description.xml?osdd=SENTINEL2_L1C')

    def test_is_valid_osdd(self):
        """Check if the OSDD is valid according to OCG's schema."""
        assert validate_against_rng(self.osdd, 'schemas/osdd.rng')

    def test_is_valid_osddgeo(self):
        """
        Check if the OSDD geo elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddgeo.rng')

    def test_is_valid_osddtime(self):
        """
        Check if the OSDD time elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddtime.rng')

    def test_result_osd(self):
        """Check if the OSDD passes OGC's result-osd test."""
        assert validate_against_rng(self.osdd, 'tests/result-osd.rng')

    def test_result_osddgeo(self):
        """Check if the OSDD passes OGC's result-osdggeo test."""
        assert validate_against_rng(self.osdd, 'tests/result-osddgeo.rng')

    def test_result_searchbygeometry(self):
        """Check if the OSDD passes OGC's result-searchbygeometry test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbygeometry.rng')

    def test_result_searchbyid(self):
        """Check if the OSDD passes OGC's result-searchbyid test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyid.rng')

    def test_result_searchbyname(self):
        """Check if the OSDD passes OGC's result-searchbyname test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyname.rng')

    def test_result_searchbypointradius(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbypointradius.rng')

    def test_result_searchbytime(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbytime.rng')

    def test_result_spatialrelations(self):
        """Check if the OSDD passes OGC's result-spatialrelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-spatialrelations.rng')

    def test_result_timerelations(self):
        """Check if the OSDD passes OGC's result-timerelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-timerelations.rng')


class TestSENTINEL2_L2ADescriptionDocument(object):
    """Class for SENTINEL2_L2A OSDD tests."""

    def __init__(self):
        """Initialize the class with a parsed OSDD."""
        self.osdd = get_xml('/opensearch/description.xml?osdd=SENTINEL2_L2A')

    def test_is_valid_osdd(self):
        """Check if the OSDD is valid according to OCG's schema."""
        assert validate_against_rng(self.osdd, 'schemas/osdd.rng')

    def test_is_valid_osddgeo(self):
        """
        Check if the OSDD geo elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddgeo.rng')

    def test_is_valid_osddtime(self):
        """
        Check if the OSDD time elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddtime.rng')

    def test_result_osd(self):
        """Check if the OSDD passes OGC's result-osd test."""
        assert validate_against_rng(self.osdd, 'tests/result-osd.rng')

    def test_result_osddgeo(self):
        """Check if the OSDD passes OGC's result-osdggeo test."""
        assert validate_against_rng(self.osdd, 'tests/result-osddgeo.rng')

    def test_result_searchbygeometry(self):
        """Check if the OSDD passes OGC's result-searchbygeometry test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbygeometry.rng')

    def test_result_searchbyid(self):
        """Check if the OSDD passes OGC's result-searchbyid test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbyid.rng')

    def test_result_searchbyname(self):
        """Check if the OSDD passes OGC's result-searchbyname test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyname.rng')

    def test_result_searchbypointradius(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbypointradius.rng')

    def test_result_searchbytime(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbytime.rng')

    def test_result_spatialrelations(self):
        """Check if the OSDD passes OGC's result-spatialrelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-spatialrelations.rng')

    def test_result_timerelations(self):
        """Check if the OSDD passes OGC's result-timerelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-timerelations.rng')


class TestSENTINEL3_SRAL_L1_CALDescriptionDocument(object):
    """Class for SENTINEL3_SRAL_L1_CAL OSDD tests."""

    def __init__(self):
        """Initialize the class with a parsed OSDD."""
        self.osdd = get_xml('/opensearch/description.xml?osdd=SENTINEL3_SRAL_L1_CAL')  # noqa: E501

    def test_is_valid_osdd(self):
        """Check if the OSDD is valid according to OCG's schema."""
        assert validate_against_rng(self.osdd, 'schemas/osdd.rng')

    def test_is_valid_osddgeo(self):
        """
        Check if the OSDD geo elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddgeo.rng')

    def test_is_valid_osddtime(self):
        """
        Check if the OSDD time elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddtime.rng')

    def test_result_osd(self):
        """Check if the OSDD passes OGC's result-osd test."""
        assert validate_against_rng(self.osdd, 'tests/result-osd.rng')

    def test_result_osddgeo(self):
        """Check if the OSDD passes OGC's result-osdggeo test."""
        assert validate_against_rng(self.osdd, 'tests/result-osddgeo.rng')

    def test_result_searchbygeometry(self):
        """Check if the OSDD passes OGC's result-searchbygeometry test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbygeometry.rng')

    def test_result_searchbyid(self):
        """Check if the OSDD passes OGC's result-searchbyid test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyid.rng')

    def test_result_searchbyname(self):
        """Check if the OSDD passes OGC's result-searchbyname test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyname.rng')

    def test_result_searchbypointradius(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbypointradius.rng')

    def test_result_searchbytime(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbytime.rng')

    def test_result_spatialrelations(self):
        """Check if the OSDD passes OGC's result-spatialrelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-spatialrelations.rng')

    def test_result_timerelations(self):
        """Check if the OSDD passes OGC's result-timerelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-timerelations.rng')


class TestSENTINEL3_SRAL_L1_SRADescriptionDocument(object):
    """Class for SENTINEL3_SRAL_L1_SRA OSDD tests."""

    def __init__(self):
        """Initialize the class with a parsed OSDD."""
        self.osdd = get_xml('/opensearch/description.xml?osdd=SENTINEL3_SRAL_L1_SRA')  # noqa: E501

    def test_is_valid_osdd(self):
        """Check if the OSDD is valid according to OCG's schema."""
        assert validate_against_rng(self.osdd, 'schemas/osdd.rng')

    def test_is_valid_osddgeo(self):
        """
        Check if the OSDD geo elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddgeo.rng')

    def test_is_valid_osddtime(self):
        """
        Check if the OSDD time elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddtime.rng')

    def test_result_osd(self):
        """Check if the OSDD passes OGC's result-osd test."""
        assert validate_against_rng(self.osdd, 'tests/result-osd.rng')

    def test_result_osddgeo(self):
        """Check if the OSDD passes OGC's result-osdggeo test."""
        assert validate_against_rng(self.osdd, 'tests/result-osddgeo.rng')

    def test_result_searchbygeometry(self):
        """Check if the OSDD passes OGC's result-searchbygeometry test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbygeometry.rng')

    def test_result_searchbyid(self):
        """Check if the OSDD passes OGC's result-searchbyid test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbyid.rng')

    def test_result_searchbyname(self):
        """Check if the OSDD passes OGC's result-searchbyname test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbyname.rng')

    def test_result_searchbypointradius(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbypointradius.rng')

    def test_result_searchbytime(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbytime.rng')

    def test_result_spatialrelations(self):
        """Check if the OSDD passes OGC's result-spatialrelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-spatialrelations.rng')

    def test_result_timerelations(self):
        """Check if the OSDD passes OGC's result-timerelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-timerelations.rng')


class TestSENTINEL3_SRAL_L2_LANDescriptionDocument(object):
    """Class for SENTINEL3_SRAL_L2_LAN OSDD tests."""

    def __init__(self):
        """Initialize the class with a parsed OSDD."""
        self.osdd = get_xml('/opensearch/description.xml?osdd=SENTINEL3_SRAL_L2_LAN')  # noqa: E501

    def test_is_valid_osdd(self):
        """Check if the OSDD is valid according to OCG's schema."""
        assert validate_against_rng(self.osdd, 'schemas/osdd.rng')

    def test_is_valid_osddgeo(self):
        """
        Check if the OSDD geo elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddgeo.rng')

    def test_is_valid_osddtime(self):
        """
        Check if the OSDD time elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddtime.rng')

    def test_result_osd(self):
        """Check if the OSDD passes OGC's result-osd test."""
        assert validate_against_rng(self.osdd, 'tests/result-osd.rng')

    def test_result_osddgeo(self):
        """Check if the OSDD passes OGC's result-osdggeo test."""
        assert validate_against_rng(self.osdd, 'tests/result-osddgeo.rng')

    def test_result_searchbygeometry(self):
        """Check if the OSDD passes OGC's result-searchbygeometry test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbygeometry.rng')

    def test_result_searchbyid(self):
        """Check if the OSDD passes OGC's result-searchbyid test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyid.rng')

    def test_result_searchbyname(self):
        """Check if the OSDD passes OGC's result-searchbyname test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyname.rng')

    def test_result_searchbypointradius(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbypointradius.rng')

    def test_result_searchbytime(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbytime.rng')

    def test_result_spatialrelations(self):
        """Check if the OSDD passes OGC's result-spatialrelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-spatialrelations.rng')

    def test_result_timerelations(self):
        """Check if the OSDD passes OGC's result-timerelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-timerelations.rng')


class TestSENTINEL3_SRAL_L2_WATDescriptionDocument(object):
    """Class for SENTINEL3_SRAL_L2_WAT OSDD tests."""

    def __init__(self):
        """Initialize the class with a parsed OSDD."""
        self.osdd = get_xml('/opensearch/description.xml?osdd=SENTINEL3_SRAL_L2_WAT')  # noqa: E501

    def test_is_valid_osdd(self):
        """Check if the OSDD is valid according to OCG's schema."""
        assert validate_against_rng(self.osdd, 'schemas/osdd.rng')

    def test_is_valid_osddgeo(self):
        """
        Check if the OSDD geo elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddgeo.rng')

    def test_is_valid_osddtime(self):
        """
        Check if the OSDD time elements are valid according to OGC's schema.
        """
        assert validate_against_rng(self.osdd, 'schemas/osddtime.rng')

    def test_result_osd(self):
        """Check if the OSDD passes OGC's result-osd test."""
        assert validate_against_rng(self.osdd, 'tests/result-osd.rng')

    def test_result_osddgeo(self):
        """Check if the OSDD passes OGC's result-osdggeo test."""
        assert validate_against_rng(self.osdd, 'tests/result-osddgeo.rng')

    def test_result_searchbygeometry(self):
        """Check if the OSDD passes OGC's result-searchbygeometry test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbygeometry.rng')

    def test_result_searchbyid(self):
        """Check if the OSDD passes OGC's result-searchbyid test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyid.rng')

    def test_result_searchbyname(self):
        """Check if the OSDD passes OGC's result-searchbyname test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbyname.rng')

    def test_result_searchbypointradius(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-searchbypointradius.rng')

    def test_result_searchbytime(self):
        """Check if the OSDD passes OGC's result-searchbypointradius test."""
        assert validate_against_rng(self.osdd, 'tests/result-searchbytime.rng')

    def test_result_spatialrelations(self):
        """Check if the OSDD passes OGC's result-spatialrelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-spatialrelations.rng')

    def test_result_timerelations(self):
        """Check if the OSDD passes OGC's result-timerelations test."""
        assert validate_against_rng(self.osdd,
                                    'tests/result-timerelations.rng')


class TestRecordResultsFeed(object):
    """Class for record search results tests."""

    def __init__(self):
        """Initialize the class with a parsed results feed."""
        params = 'identifier=S1A_IW_SLC__1SDV_20170226T105154_20170226T105221_015454_0195F7_BBA7'  # noqa: E501
        self.atom_feed = get_xml('/opensearch/view_record.atom?{}'
                                 .format(params))

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
        print self.atom_feed
        assert validate_against_rng(self.atom_feed, 'tests/result-atom.rng')


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
