
# -*- coding: utf-8 -*-
"""
Contains functions for converting OpenSearch parameters to CKAN/Solr parameters.
"""


def range_array_to_solr_range(range_array):
    """
    Convert an array range like '[start,stop]' to a Solr range like '[start TO stop]'
    """
    start, stop = range_array[1:-1].split(",")

    return "[{} TO {}]".format(start.strip(), stop.strip())


def add_timezone(datetime_query):
    """
    If a field in the index is a datetime, Solr requires that the datetime string
    in the query include the timezone.

    Note that not all fields in the index that look like datetimes _are_ datetimes:
    it's possible to store date-like metadata as a string, in which case this conversion
    is not necessary.
    """
    if datetime_query.startswith("["):
        # It's a range
        start, stop = datetime_query[1:-1].split(" TO ")
        if ":" in start and not start.endswith("Z"):
            start += "Z"
        if ":" in stop and not stop.endswith("Z"):
            stop += "Z"
        datetime_query = "[{} TO {}]".format(start, stop)
    else:
        if ":" not in datetime_query and not datetime_query.endswith("Z"):
            datetime_query += "Z"

    return datetime_query


def solr_timerange_start(start_time):
    """Convert a single start time into a timerange for Solr."""
    if not start_time:
        start_time = "*"

    return "[{} TO {}]".format(start_time, "NOW")


def solr_timerange_stop(stop_time):
    """Convert a single stop time into a timerange for Solr."""
    if not stop_time:
        stop_time = "NOW"

    return "[{} TO {}]".format("*", stop_time)


def solr_timerange(start_time, stop_time):
    return "[{} TO {}]".format(start_time, stop_time)


def intersects_spatial(geometry):
    """Convert a geometry parameter into Solr Intersects query."""
    return '"Intersects({})"'.format(geometry)
