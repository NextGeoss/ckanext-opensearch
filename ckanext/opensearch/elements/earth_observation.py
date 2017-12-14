# -*- coding: utf-8 -*-
"""Classes describing Earth Observation elements."""

from . import OSElement
from ..config import NAMESPACES


class EarthObservation(OSElement):
    """Define an EarthObservation element."""

    def __init__(self, entry_dict):
        children = [
            (PhenomenonTime, entry_dict),
            (Procedure, entry_dict),
            (MetaDataProperty, entry_dict),
        ]
        OSElement.__init__(self, 'eop', 'EarthObservation', children=children)


class PhenomenonTime(OSElement):
    """Define a phenomenonTime element."""

    def __init__(self, entry_dict):
        children = [
            (TimePeriod, entry_dict)
        ]
        OSElement.__init__(self, 'om', 'phenomenonTime', children=children)


class TimePeriod(OSElement):
    """Define a a GML TimePeriod element."""

    def __init__(self, entry_dict):
        id_string = 'tp_{}'.format(entry_dict['id'])
        attr_name = '{%s}%s' % (NAMESPACES['gml'], 'id')
        attr = {
            attr_name: id_string
        }
        children = [
            (BeginPosition, entry_dict),
            (EndPosition, entry_dict)
        ]
        OSElement.__init__(self, 'gml', 'TimePeriod', attr=attr,
                           children=children)


class BeginPosition(OSElement):
    """Define a GML beginPosition element (start of dataset time period)."""

    def __init__(self, entry_dict):
        keys = ['startposition']
        content = OSElement._get_from_extras(self, entry_dict, keys)
        OSElement.__init__(self, 'gml', 'beginPosition', content=content)


class EndPosition(OSElement):
    """Define a GML endPosition element (end of dataset time period)."""

    def __init__(self, entry_dict):
        keys = ['endposition']
        content = OSElement._get_from_extras(self, entry_dict, keys)
        OSElement.__init__(self, 'gml', 'endPosition', content=content)


class Procedure(OSElement):
    """
    Define an OM procedure element describing the instrument and sensor types.
    """

    def __init__(self, entry_dict):
        children = [
            (EarthObservationEquipment, entry_dict)
        ]
        OSElement.__init__(self, 'om', 'procedure', children=children)


class EarthObservationEquipment(OSElement):
    """Define an EarthObservationEquipment container element."""

    def __init__(self, entry_dict):
        id_string = 'eq_{}'.format(entry_dict['id'])
        attr_name = '{%s}%s' % (NAMESPACES['gml'], 'id')
        attr = {
            attr_name: id_string
        }
        children = [
            (PlatformContainer, entry_dict),
            (InstrumentContainer, entry_dict),
            (SensorContainer, entry_dict)
        ]
        OSElement.__init__(self, 'eop', 'EarthObservationEquipment',
                           attr=attr, children=children)


class PlatformContainer(OSElement):
    """Define a container platform element."""

    def __init__(self, entry_dict):
        children = [
            (PlatformElement, entry_dict)
        ]
        OSElement.__init__(self, 'eop', 'platform', children=children)


class PlatformElement(OSElement):
    """
    Define a Platform container element.

    This element will contain elements that contain actual
    information about the platform itself.
    """

    def __init__(self, entry_dict):
        children = [
            (PlatformShortName, entry_dict)
        ]
        OSElement.__init__(self, 'eop', 'Platform', children=children)


class PlatformShortName(OSElement):
    """Define a shortName element describing a platform."""

    def __init__(self, entry_dict):
        keys = ['platformname', 'PlatformName']
        content = OSElement._get_from_extras(self, entry_dict, keys)
        OSElement.__init__(self, 'eop', 'shortName', content=content)


class InstrumentContainer(OSElement):
    """Define an instrument container element."""

    def __init__(self, entry_dict):
        children = [
            (InstrumentElement, entry_dict)
        ]
        OSElement.__init__(self, 'eop', 'instrument', children=children)


class InstrumentElement(OSElement):
    """
    Define an Instrument container element.

    This element will contain elements that contain actual
    information about the instrument itself.
    """

    def __init__(self, entry_dict):
        children = [
            (InstrumentShortName, entry_dict)
        ]
        OSElement.__init__(self, 'eop', 'Instrument', children=children)


class InstrumentShortName(OSElement):
    """Define a shortName element describing a platform."""

    def __init__(self, entry_dict):
        keys = ['instrumentshortname']
        content = OSElement._get_from_extras(self, entry_dict, keys)
        OSElement.__init__(self, 'eop', 'shortName', content=content)


class SensorContainer(OSElement):
    """Define a sensor container element."""

    def __init__(self, entry_dict):
        children = [
            (SensorElement, entry_dict)
        ]
        OSElement.__init__(self, 'eop', 'sensor', children=children)


class SensorElement(OSElement):
    """
    Define a Sensor container element.

    This element will contain elements that contain actual
    information about the sensor itself.
    """

    def __init__(self, entry_dict):
        children = [
            (SensorType, entry_dict)
        ]
        OSElement.__init__(self, 'eop', 'Sensor', children=children)


class SensorType(OSElement):
    """Define a shortName element describing a platform."""

    def __init__(self, entry_dict):
        keys = ['SensorType']
        content = OSElement._get_from_extras(self, entry_dict, keys)
        OSElement.__init__(self, 'eop', 'sensorType', content=content)


class AcquisitionParameters(OSElement):
    """Define an acquisition parameters container element."""

    def __init__(self, entry_dict):
        children = [
            (Acquisition, entry_dict)
        ]
        OSElement.__init__(self, 'eop', 'acquisitionParameters',
                           children=children)


class Acquisition(OSElement):
    """
    Define an Acquisition container element.

    This element will contain elements that contain actual
    information about the acquisition itself.
    """

    def __init__(self, entry_dict):
        children = [
            (OrbitDirection, entry_dict)
        ]
        OSElement.__init__(self, 'eop', 'Acquisition', children=children)


class OrbitDirection(OSElement):
    """
    Define an orbitDirection element.

    This element describes the direction of orbit of the colleting satellite.
    """

    def __init__(self, entry_dict):
        keys = ['orbitdirection', 'OrbitDirection']
        content = OSElement._get_from_extras(self, entry_dict, keys)
        OSElement.__init__(self, 'eop', 'orbitDirection', content=content)


class OrbitNumber(OSElement):
    """
    Define an orbitNumber element.

    This element describes the orbit number of the collecting satellite.
    """

    def __init__(self, entry_dict):
        keys = ['orbitnumber', 'OrbitNumber']
        content = OSElement._get_from_extras(self, entry_dict, keys)
        OSElement.__init__(self, 'eop', 'orbitNumber', content=content)


class MetaDataProperty(OSElement):
    """Define a MetaDataProperty container element."""

    def __init__(self, entry_dict):
        children = [
            (EarthObservationMetaData, entry_dict)
        ]
        OSElement.__init__(self, 'eop', 'metaDataProperty', children=children)


class EarthObservationMetaData(OSElement):
    """Define an EarthObservationMetaData container element."""

    def __init__(self, entry_dict):
        children = [
            (EOPIdentifier, entry_dict),
            (ProductType, entry_dict),
            (AcquisitionType, entry_dict),
            (EOPStatus, entry_dict),
            (DownlinkedTo, entry_dict),
            (Processing, entry_dict)
        ]
        OSElement.__init__(self, 'eop', 'EarthObservationMetadata',
                           children=children)


class EOPIdentifier(OSElement):
    """Define an EOP Identifier element."""

    def __init__(self, entry_dict):
        content = entry_dict.get('id')
        OSElement.__init__(self, 'eop', 'identifier', content=content)


class ProductType(OSElement):
    """Define a ProductType element describing the type of EO product."""

    def __init__(self, entry_dict):
        keys = ['producttype', 'productType']
        content = OSElement._get_from_extras(self, entry_dict, keys)
        OSElement.__init__(self, 'eop', 'productType', content=content)


class AcquisitionType(OSElement):
    """Define an AcquisitionType element describing an EO product."""

    def __init__(self, entry_dict):
        keys = ['acquisitiontype']
        content = OSElement._get_from_extras(self, entry_dict, keys)
        OSElement.__init__(self, 'eop', 'acquisitionType', content=content)


class EOPStatus(OSElement):
    """Define an EOP Status element."""

    def __init__(self, entry_dict):
        keys = ['status']
        content = OSElement._get_from_extras(self, entry_dict, keys)
        OSElement.__init__(self, 'eop', 'status', content=content)


class DownlinkedTo(OSElement):
    """Define a downlinkedTo container element."""

    def __init__(self, entry_dict):
        children = [
            (DownlinkInformation, entry_dict)
        ]
        OSElement.__init__(self, 'eop', 'downlinkedTo', children=children)


class DownlinkInformation(OSElement):
    """Define a DownlinkInformation container element."""

    def __init__(self, entry_dict):
        children = [
            (AcquisitionStation, entry_dict)
        ]
        OSElement.__init__(self, 'eop', 'DownlinkInformation',
                           children=children)


class AcquisitionStation(OSElement):
    """
    Define an acquisitionStation element containing the name of the
    acquisition station.
    """

    def __init__(self, entry_dict):
        keys = []
        content = OSElement._get_from_extras(self, entry_dict, keys)
        OSElement.__init__(self, 'eop', 'acquisitionStation', content=content)


class Processing(OSElement):
    """Define a processing container element."""

    def __init__(self, entry_dict):
        children = [
            (ProcessingInformation, entry_dict)
        ]
        OSElement.__init__(self, 'eop', 'processing', children=children)


class ProcessingInformation(OSElement):
    """Define a processingInformation container element."""

    def __init__(self, entry_dict):
        children = [
            (ProcessingCenter, entry_dict)
        ]
        OSElement.__init__(self, 'eop', 'processingInformation', children=children)


class ProcessingCenter(OSElement):
    """
    Define a processingCenter element containing an identifier for the
    processing center.
    """

    def __init__(self, entry_dict):
        keys = []
        content = OSElement._get_from_extras(self, entry_dict, keys)
        OSElement.__init__(self, 'eop', 'processingCenter', content=content)


class OMResult(OSElement):
    """Define an om result element, which contains additional metadata."""

    def __init__(self, entry_dict):
        children = [
            (OptEarthObservationResult, entry_dict),
            ()
        ]