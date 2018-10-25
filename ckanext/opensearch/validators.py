# -*- coding: utf-8 -*-
"""This module contains the validator class."""

import re

import shapely.wkt
from shapely.errors import ReadingError, WKTReadingError

from plugin import OpenSearchError


def valid_occurances(count, min_occurances, max_occurances, display_name):
    """Validate the number of occurances of the parameter."""
    try:
        assert count >= min_occurances
        if max_occurances != "*":
            assert count <= max_occurances
    except AssertionError:
        raise OpenSearchError(
            "Minimum {} and maximum {} instances of {} are permitted.".format(
                min_occurances, max_occurances, display_name
            )
        )


def valid_value_min_max(
    param_value, value_min_inclusive, value_max_exclusive, display_name
):
    """Validate the value of the parameter against a min and max value."""
    if value_min_inclusive or value_max_exclusive:
        try:
            value = int(param_value)
            if value_min_inclusive:
                assert value_min_inclusive <= value
            if value_max_exclusive:
                assert value < value_max_exclusive
        except (ValueError, AssertionError):
            raise OpenSearchError(
                "{} must be an integer from {} to {}.".format(
                    display_name, value_min_inclusive, value_max_exclusive
                )
            )


def valid_bbox(bbox, display_name):
    """Check if a bounding box is valid."""
    try:
        minX, minY, maxX, maxY = [float(i) for i in bbox.split(",")]
        assert minX < maxX
        assert minX >= -180.0
        assert maxX <= 180.0
        assert minY < maxY
        assert minY >= -90.0
        assert maxY <= 90.0
    except (AssertionError, ValueError):
        raise OpenSearchError(
            "{} must be in the form `west,south,east,north` or `minX,minY,maxX,maxY`.".format(  # noqa: E501
                display_name
            )
        )


def valid_geometry(geometry, display_name):
    """Check if a geometry is valid."""
    try:
        shapely.wkt.loads(geometry)
    except (ReadingError, WKTReadingError):
        raise OpenSearchError(
            "{} must be expressed as a valid WKT geometry. The following geometries are supported: POINT, LINESTRING, POLYGON, MULTIPOINT, MULTILINESTRING, and MULTIPOLYGON.".format(  # noqa: E501
                display_name
            )
        )


def valid_datetime_string(datetime_string, display_name):
    """
    Check if a datetime string is valid.

    OpenSearch parameters in description documents can include a pattern for each
    parameter that the client can use to create a well-formed query. The goal is
    to base this and other validation functions on those patterns and so that
    we can define each pattern once for use by both the OSDD template and the
    related validator.
    """
    pattern = re.compile(
        r"^[0-9]{4}-[0-9]{2}-[0-9]{2}(T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?(Z|[\+\-][0-9]{2}:[0-9]{2})?)?$"  # noqa: E501
    )
    if not pattern.match(datetime_string):
        raise OpenSearchError(
            "{} must be in the form YYYY-MM-DDTHH:MM:SS".format(display_name)
        )


def valid_date_range(date_range, display_name):
    """Check if the date range array is well-formed."""
    pattern = re.compile(
        r"\[[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}]"  # noqa: E501
    )
    if not pattern.match(date_range):
        raise OpenSearchError(
            "{} must be in the form [YYYY-MM-DDTHH:MM:SS,YYYY-MM-DDTHH:MM:SS]".format(
                display_name
            )
        )
