[![Travis](https://travis-ci.org/NextGeoss/ckanext-opensearch.svg?branch=master)](https://travis-ci.org/NextGeoss/ckanext-opensearch)

# ckanext-opensearch

ckanext-opensearch adds an OpenSearch interface to CKAN. 

## Contents

1. [Overview](#overview)
2. [For End Users](#forendusers)
3. [Requirements](#requirements)
4. [Customizing](#customizing)
5. [Installation](#installation)
6. [Config Settings](#config-settings)
7. [Development Installation](#development-installation)
8. [Running the Tests](#running-the-tests)


## <a name="overview"></a>Overview
Since this extension is being developed for the NextGEOSS project, the current version of the extension is tweaked to support the project's requirements rather than to be fully generalized, but the goal is to release a fully generalized extension that users can customize with their own profiles and parameters. Even if you intend to use the defaults, you should have a look at the [config settings](#config-settings).

The extension will also optionally enable two additional OpenSearch interfaces: collection search and record views.

In the Earth Observation community there is a need for "two-step" search, meaning search first at the collection level and then (within one of the collections returned in step one) at the dataset level, which is the level at which CKAN search usually operates. If collection search is activated and a dataset metadata field is selected for grouping results, users can search for a collection of datasets using one set of search parameters and then search within a collection using another set of parameters specific to that dataset.

If users need to be able to link to an XML/OpenSearch representation of a dataset that _doesn't_ depend on a search query (similar to how users of CKAN can refer to dataset/{dataset-name} rather than specifying a search query that will return that dataset), you can enable record views, which return one and only one record based on a unique identifier.

## <a name="forendusers"></a>For End Users
OpenSearch is intended as an M2M (machine to machine) interface. The end user does not use it; the end user's client uses it.

All the default parameters are defined in the description documents. They are all standards-based. For more information any given parameter (beyond what is described in the description document), consult the documentation for the related standard. For more information about the description documents and the result feeds in general, consult the OGC OpenSearch documentation.

### Accessing the Description Documents
By default, the description documents are located at `/opensearch/description.xml`. The `osdd` parameter is required and determines which description document will be returned.

```
/opensearch/description.xml?osdd=dataset
```
By default, any portal using the extension will have a `dataset` description document that describes how to search all the datasets on the portal using the available parameters. "dataset" search is equivalent in scope to the standard search on portal's web frontend and via the API.

```
/opensearch/description.xml?osdd=record
```
If `record_view` is enabled, the portal will have a `record` description document that describes how to access an XML representation of individual datasets in the OpenSearch Atom format. This provides a way to link to individual datasets without relying on search terms that may change. The record view endpoint accepts one and only one required parameter that refers to a unique identifier (by default, this will be the `identifier` extra). The machine-readable description document describes the parameter in more detail.

```
/opensearch/description.xml?osdd=collection
```
If collections are enabled, the portal will have a `collection` description document that describes how to search for _collections_ of datasets. This is step one in two step search, where the user first searches for a collection that meets their search criteria and then searches within the collection to find the dataset or datasets they need. The result of a collection search is a list of links to description documents for individual collections. The user selects a collection and then executes a new search using the parameters defined in the collection's description document.

```
/opensearch/description.xml?osdd={collection_id}
```
If collections are enabled, the portal will have a description document for each collection that is available. These description documents are used in step two of two-step search (see preceding paragraph). The result of a search within a specific collection is a list of datasets _belonging to that collection_ that match the search parameters. Each collection description document may be unique—some collections may support parameters that others don't. For instance, one collection might support queries about sensor type (because sensor type is part of the metadata of its datasets) while another might not (because its datasets do not contain sensort type metadata, or because sensor type is irrelevant).

### Example of a Description Document
```
<opensearch:OpenSearchDescription xmlns:time="http://a9.com/-/opensearch/extensions/time/1.0/" xmlns:referrer="http://www.opensearch.org/Specifications/OpenSearch/Extensions/Referrer/1.0" xmlns:geo="http://a9.com/-/opensearch/extensions/geo/1.0/" xmlns:eo="http://a9.com/-/opensearch/extensions/eo/1.0/" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:eop="http://www.opengis.net/eop/2.1" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/" xmlns:param="http://a9.com/-/opensearch/extensions/param/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <opensearch:ShortName>NextGEOSS</opensearch:ShortName>
    <opensearch:Description>Search collections of products.</opensearch:Description>
    <opensearch:Tags>open data CKAN opendata</opensearch:Tags>
    <opensearch:SyndicationRight>open</opensearch:SyndicationRight>
    <opensearch:Url type="application/opensearchdescription+xml" template="http://localhost:5000/opensearch/description.xml?osdd=collection" rel="self"/>
    <opensearch:Url pageOffset="1" type="application/atom+xml" rel="collection" indexOffset="1" template="http://localhost:5000/opensearch/search.atom?q={opensearch:searchTerms?}&amp;rows={opensearch:maxResults?}&amp;page={opensearch:startPage?}&amp;ext_bbox={geo:box?}&amp;identifier={geo:uid?}&amp;begin={time:start?}&amp;end={time:end?}&amp;client_id={referrer:source?}&amp;date_modified={eo:modificationDate?}&amp;ext_geometry={geo:geometry?}">
        <param:Parameter name="q" maximum="1" value="{opensearch:searchTerms}">
            <atom:link title="This parameter follows the Solr free text search implementation." rel="profile" href="https://wiki.apache.org/solr/SolrQuerySyntax"/>
        </param:Parameter>
        <param:Parameter name="rows" value="{opensearch:maxResults}" maximum="1" minInclusive="1" maxExclusive="10001"/>
        <param:Parameter name="page" value="{opensearch:startPage}" maximum="1" minInclusive="1" maxExclusive="100000000"/>
        <param:Parameter name="ext_bbox" maximum="1" value="{geo:box}">
            <param:Option value="-0.489,51.28,0.236,51.686" label="Bounding Box of Greater London"/>
        </param:Parameter>
        <param:Parameter name="identifier" value="{geo:uid}" maximum="1"/>
        <param:Parameter name="begin" maximum="1" value="{time:start}">
            <param:Option value="2014-04-03" label="example start time"/>
        </param:Parameter>
        <param:Parameter name="end" maximum="1" value="{time:end}">
            <param:Option value="2017-12-21" label="example end time"/>
        </param:Parameter>
        <param:Parameter name="client_id" value="{referrer:source}" maximum="1"/>
        <param:Parameter name="date_modified" maximum="1" value="{eo:modificationDate}">
            <param:Option value="[2017-11-05T00:00:00,2017-11-05T12:00:00]" label="example modification date range"/>
        </param:Parameter>
        <param:Parameter name="ext_geometry" maximum="1" value="{geo:geometry}">
            <param:Option value="POLYGON((-6.284 24.727,-4.834 24.867,0.879 20.982,1.077 20.592,1.912 20.015,2.197 20.118,2.966 19.58,2.944 18.958,3.34 18.813,4.043 18.854,4.021 16.426,3.384 15.581,-0.747 15.242,-3.01 14.179,-3.56 13.411,-3.955 13.646,-4.57 13.261,-4.702 12.426,-5.669 11.867,-5.647 10.661,-6.196 10.92,-6.812 10.833,-7.031 10.445,-7.625 10.682,-7.866 10.509,-8.086 11.394,-9.009 12.726,-10.195 12.404,-11.096 12.469,-11.316 13.518,-11.909 14.499,-11.448 15.178,-10.833 14.796,-10.173 15.263,-5.295 15.305,-5.076 16.32,-5.427 16.784,-6.284 24.727))" label="Mali"/>
        </param:Parameter>
    </opensearch:Url>
</opensearch:OpenSearchDescription>
```
### Default Search Parameters
Consult a description document and the related standards for details about the supported search parameters.

By default, the following parameters are supported:
- opensearch:searchTerms
- opensearch:maxResults
- opensearch:startPage
- geo:box
- geo:uid
- time:start
- time:end
- referrer:source
- eo:modificationDate
- geo:geometry

### Example of Atom Results Feed
```
<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<atom:feed xmlns:time="http://a9.com/-/opensearch/extensions/time/1.0/" xmlns:referrer="http://www.opensearch.org/Specifications/OpenSearch/Extensions/Referrer/1.0" xmlns:georss="http://www.georss.org/georss" xmlns:geo="http://a9.com/-/opensearch/extensions/geo/1.0/" xmlns:eo="http://a9.com/-/opensearch/extensions/eo/1.0/" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:eop="http://www.opengis.net/eop/2.1" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:param="http://a9.com/-/opensearch/extensions/param/1.0/" xmlns:custom="http://example.com/opensearchextensions/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <atom:title>NextGEOSS OpenSearch Search Results</atom:title>
    <atom:subtitle>1 results for your search</atom:subtitle>
    <atom:id>http://localhost:5000/opensearch/view_record.atom?identifier=S1A_IW_GRDH_1SDV_20170226T153347_20170226T153421_015456_019609_5E64</atom:id>
    <atom:generator version="0.1" uri="http://localhost:5000/opensearch/view_record.atom?identifier=S1A_IW_GRDH_1SDV_20170226T153347_20170226T153421_015456_019609_5E64">NextGEOSS search results</atom:generator>
    <atom:author>
        <atom:name>No author information available</atom:name>
    </atom:author>
    <atom:updated>2018-04-18T15:59:04Z</atom:updated>
    <opensearch:totalResults>1</opensearch:totalResults>
    <opensearch:startIndex>1</opensearch:startIndex>
    <opensearch:itemsPerPage>20</opensearch:itemsPerPage>
    <opensearch:Query geo:uid="S1A_IW_GRDH_1SDV_20170226T153347_20170226T153421_015456_019609_5E64" role="request"/>
    <georss:box>-180.0 -90.0 180.0 90.0</georss:box>
    <atom:link href="http://localhost:5000/opensearch/description.xml?osdd=dataset" type="application/opensearchdescription+xml" rel="search" title="Dataset search description document"/>
    <atom:link href="http://localhost:5000/opensearch/view_record.atom?identifier=S1A_IW_GRDH_1SDV_20170226T153347_20170226T153421_015456_019609_5E64" type="application/atom+xml" rel="self" title="self"/>
    <atom:link href="http://localhost:5000/opensearch/view_record.atom?identifier=S1A_IW_GRDH_1SDV_20170226T153347_20170226T153421_015456_019609_5E64&amp;page=1" type="application/atom+xml" rel="first" title="first"/>
    <atom:link href="http://localhost:5000/opensearch/view_record.atom?identifier=S1A_IW_GRDH_1SDV_20170226T153347_20170226T153421_015456_019609_5E64&amp;page=None" type="application/atom+xml" rel="next" title="next"/>
    <atom:link href="http://localhost:5000/opensearch/view_record.atom?identifier=S1A_IW_GRDH_1SDV_20170226T153347_20170226T153421_015456_019609_5E64&amp;page=None" type="application/atom+xml" rel="prev" title="prev"/>
    <atom:link href="http://localhost:5000/opensearch/view_record.atom?identifier=S1A_IW_GRDH_1SDV_20170226T153347_20170226T153421_015456_019609_5E64&amp;page=1" type="application/atom+xml" rel="last" title="last"/>
    <atom:entry>
        <atom:title>Sentinel-1 Level-1 (GRD)</atom:title>
        <atom:id>http://localhost:5000/opensearch/view_record.atom?&amp;identifier=S1A_IW_GRDH_1SDV_20170226T153347_20170226T153421_015456_019609_5E64</atom:id>
        <dc:identifier>S1A_IW_GRDH_1SDV_20170226T153347_20170226T153421_015456_019609_5E64</dc:identifier>
        <atom:link href="http://localhost:5000/opensearch/search.atom?collection_id=SENTINEL1_L1_GRD&amp;identifier=S1A_IW_GRDH_1SDV_20170226T153347_20170226T153421_015456_019609_5E64" rel="self" title="self"/>
        <atom:link href="http://localhost:5000?collection_id=SENTINEL1_L1_GRD" type="application/atom+xml" rel="up" title="Link to collection"/>
        <dc:publisher>ESA Sentinel</dc:publisher>
        <atom:published>2018-03-22T13:23:05.589408</atom:published>
        <atom:updated>2018-03-22T13:23:05.589413</atom:updated>
        <atom:summary>The Sentinel-1 Level-1 Ground Range Detected (GRD) products consist of focused SAR data that has been detected, multi-looked and projected to ground range using an Earth ellipsoid model. Phase information is lost. The resulting product has approximately square resolution pixels and square pixel spacing with reduced speckle at the cost of reduced geometric resolution.</atom:summary>
        <dc:date>2017-02-26T15:33:47.749Z/2017-02-26T15:34:21.637Z</dc:date>
        <georss:polygon>43.23555 -20.659054 45.591873 -20.104935 46.151516 -22.13032 43.765354 -22.694042 43.23555 -20.659054</georss:polygon>
        <atom:link href="http://localhost:5000/dataset/07ed5ef7-0938-4e51-97b2-0e45dbc914c8" type="text/html" rel="alternate"/>
        <atom:category term="GRD"/>
        <atom:category term="Sentinel-1"/>
        <atom:link length="2160000" href="https://scihub.copernicus.eu/dhus/odata/v1/Products('ce20c25f-d459-4a8b-88a3-d4f652edf562')/$value" type="application/zip" rel="enclosure" title="Product Download from SciHub"/>
        <atom:link href="https://scihub.copernicus.eu/dhus/odata/v1/Products('ce20c25f-d459-4a8b-88a3-d4f652edf562')/Nodes('S1A_IW_GRDH_1SDV_20170226T153347_20170226T153421_015456_019609_5E64.SAFE')/Nodes('manifest.safe')/$value" type="application/xml" rel="via" title="Metadata Download from SciHub"/>
        <atom:link href="https://scihub.copernicus.eu/dhus/odata/v1/Products('ce20c25f-d459-4a8b-88a3-d4f652edf562')/Products('Quicklook')/$value" type="image/jpeg" rel="icon" title="Quicklook image"/>
    </atom:entry>
</atom:feed>
```

### Default Elements in Atom Results Feed
These defaults are chosen to comply with OGC OpenSearch best practices. For more details, consult OGC's documentation.

#### Default Elements
- atom:feed
- atom:title
- atom:subtitle
- atom:id
- atom:generator
- atom:author
- atom:updated
- opensearch:totalResults
- opensearch:startIndex
- opensearch:itemsPerPage
- opensearch:Query
- georss:box
- atom:link rel="search"
- atom:link rel="self"
- atom:link rel="first"
- atom:link rel="next"
- atom:link rel="prev"
- atom:link rel="last"
- atom:entry
    - atom:title
    - atom:id
    - dc:identifier
    - atom:link rel="self"
    - atom:link rel="up"
    - dc:publisher
    - atom:published
    - atom:updated
    - atom:summary
    - dc:date
    - georss:polygon
    - atom:link rel="alternate"/>
    - atom:category
    - atom:link rel="enclosure"

## <a name="requirements"></a>Requirements

The default search parameters included in this plugin include advanced spatial search parameters (like arbitrary geometries instead of just bounding boxes). These parameters require that you install ckanext-spatial, that you configure CKAN to use `solr-spatial-field` for the spatial search backend, and that you update your Solr configuration according to the instructions in the ckanext-spatial documentation. The defaults will not work without ckanext-spatial nor will they work with the `postgis` or `solr` spatial search backends. However, you don't need to use the defaults—if you remove the advanced spatial search parameters, you can use any ckanext-spatial configuration, or not use ckanext-spatial at all.

## <a name="customizing"></a>Customizing

The search parameters, description documents, and results feeds are all customizable.

To customize the parameters that are accepted and how they're named, create a new JSON parameters file and update your .ini file to tell the extension where to find it.

The description documents are created based on the settings described below and use the parameters files. To change the content of your description document, update your config and/or your parameters files.

If you want to change the formatting of the description documents, you can override the description_document.xml template.

To customize the results feeds, override the search_results.xml and/or the collection_results.xml templates. Both templates receive a list of dicts containing the dictized datasets (or collections) that are in the search results, just like the standard HTML search templates do.

If you need to change the way one or more of the fields included in the results dictionaries are represented (creating an element with several attributes based on one of the fields, for example), you can create and register a new helper function in the plugin.py file for your theme and then use that helper function in your modified results template.

The plugin has a helper function for converting a dictionary into a string of attributes for use in XML elements, so you just need to write a function that creates a dictionary with whatever attributes you need. Make sure you use the `|safe` filter after inserting attributes in this way to ensure that Jinja2 doesn't escape the quotes.

## <a name="installation"></a>Installation

To install ckanext-opensearch:

1. Activate your CKAN virtual environment, for example:

```
. /usr/lib/ckan/default/bin/activate
```

2. Install the ckanext-opensearch Python package into your virtual environment:

```
pip install ckanext-opensearch
```

3. Add `opensearch` to the `ckan.plugins` setting in your CKAN config file (by default the config file is located at `/etc/ckan/default/production.ini`).

4. Make sure that any additional plugins or requirements that are required for your search parameters are installed and activated. For instance, if you want to enable advanced spatial queries as in the default settings here, you'll need to have ckanext-spatial installed and activated _and_ you'll need to have configured CKAN to use `solr-spatial-field` for the spatial search back end, which also requires changes to your Solr configuration.

5. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

```
sudo service apache2 reload
```

## <a name="config-settings"></a>Config Settings

Enable collections search (enable two-step search):
```
ckanext.opensearch.enable_collections = true (default is false)
```

Set name of field to group on for collection search:
```
ckanext.opensearch.group_on = collection_id (default is title)
```

Enable record view interface (unique, fixed OpenSearch/XML endpoints for each dataset, independent of search queries):
```
ckanext.opensearch.record_view = true (default is false)
```

Set fields to use for temporal search queries (may be two unique fields, or may be the same field each time):
```
ckanext.opensearch.temporal_start = name_of_field_queried_for_start_of_temporal_range
ckanext.opensearch.temporal_end = name_of_field_queries_for_end_of_temporal_range
```

Location of JSON file defining the search parameters for the record view interface:
```
ckanext.opensearch.record_parameters (default is ckanext.opensearch.defaults:record_parameters.json)
```

Location of JSON file defining the search parameters for collection search (step one of two-step search):
```
ckanext.opensearch.collection_parameters (default is ckanext.opensearch.defaults:collection_parameters.json)
```

Location of list of collections to return in collection search and their parameter files
```
ckanext.opensearch.collection_params_list (default is ckanext.opensearch.defaults:collection_params_list.json)
```

Locations of parameter files for individual collections:

Determined by the `collection_params_list` file, which specifies a parameter file for each collection. For defaults see the default collection_params_list.json file.

## <a name="development-installation"></a>Development Installation

To install ckanext-opensearch for development, activate your CKAN virtualenv and
do:

```
git clone https://github.com/ViderumGlobal/ckanext-opensearch.git
cd ckanext-opensearch
python setup.py develop
pip install -r dev-requirements.txt
```

## <a name="running-the-tests"></a>Running the Tests

To run the tests, do:

```
nosetests --nologcapture --with-pylons=test.ini
```

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (`pip install coverage`) then run:

```
nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.opensearch --cover-inclusive --cover-erase --cover-tests
```