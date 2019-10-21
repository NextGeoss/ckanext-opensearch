[![Travis](https://travis-ci.org/NextGeoss/ckanext-opensearch.svg?branch=master)](https://travis-ci.org/NextGeoss/ckanext-opensearch)

# ckanext-opensearch

ckanext-opensearch adds an OpenSearch interface to CKAN.

## About
This extension adds three endpoints to a CKAN portal: `opensearch/description.xml?`, `opensearch/search.atom?` and `opensearch/collection_search.atom?`. Each endpoint accepts a query and returns an XML document.

`opensearch/description.xm?` is the endpoint for accessing the "description document" that describes the parameters accepted by the `search.atom?` and `collection_search.atom` endpoints. When using OpenSearch, a client will first access a description document, which tells it where and how to submit queries. OpenSearch search results also include links to description documents in order to enable the user to continue searching within a different collection of results, or with a different but related endpoint, etc. `opensearch/description.xm?` accepts a single parameter: `osdd`. The value of `osdd` must be either `collection` (for accessing the description document for collection search), `dataset` (for accessing the description document for dataset search, which is equivalent to CKAN's package_search API or the normal dataset search on a portal's GUI), or a collection ID (for accessing the description document of a specific collection. Searching within a collection works like `dataset` search but 1) the results are restricted to datasets in that collection and 2) the parameters may vary from collection to collection).

The expected workflow for two-step search is:

1. User accesses the description document for `collection` search.
2. User performs a collection search using the parameters defined by the `collection` description document.
3. The search returns a list of collections that match the user's search criteria.
4. The user selects one of the collections to search within.
5. The search results contain a link to the description document for each collection, so when the user selects the collection, their client loads the collection's description document and they can now use the parameters that are specific to the collection to search for a dataset (or product in geo-speak).
6. The user performs a dataset (or product) search within the chosen collection using the endpoint and parameters defined by the relevant description document.
7. The search returns a list of datasets that match the user's search criteria.
8. The user selects a dataset. If they want to download a resource, the results contain links to each dataset's resources. If the user wants to bookmark or save a reference to the XML representation of the product, the results have links for that as well. This stage of the search is more or less equivalent to just searching normally on the portal, except with machine-readable XML.

`dataset` search is probably not useful for NextGEOSS users, since it will return very many similar results. However, it is included because a non-NextGEOSS portal that needs an OpenSearch interface will most likely only need basic `dataset` search.

The structures of the description documents (simple XML documents) and the dataset and collection search results feed (Atom feeds, which are also XML documents) are defined by Jinja2 templates in the `templates` directory. There are other ways to go about generating XML, but for this project, templates have been the easiest because they make it easy to compare the generator with the XML documents and snippets in the various specifications. There are several specifications that for different types of elements that have to be followed. The current templates are not as complex as they will eventually become. Providing full XML descriptions of Earth observation data involves some large, deeply nested elements. In the past, maintaining functions or methods to generate each of them proved to be unwieldy.

The extension uses TOML files to specify collections and parameters. The collection uses the TOML files, together with the Jinja2 templates, to generate the description documents. It also uses the TOML files to determine which parameters are accepted when users perform searches, as well as to validate the input and, if necessary, to transform it. When a user performs a collection search, the TOML files are used to get the description, name, etc. of each collection.

Each collection in `collections_list.toml` includes the collection ID, the name of the collection, its description, and an array listing the additional parameter sets that the collection accepts. All collections use the parameters defined in `dataset_parameters.toml`. The SENTINEL2_L2A collection also uses the `sentinel_base_parameters` (which are defined in `sentinel_base_parameters.toml`) and the `sentinel-2_parameters` (which are defined in `sentinel-2_parameters.toml`). The additional parameters are added to the collection in the order they appear in the list, so the SENTINEL2_L2A collection has _all_ the parameters defined in `dataset_parameters.toml` plus _all_ the parameters defined in the two additional parameters files. If there are two parameters with the same name (e.g., if `rows` were to appear in all three parameters files), then the version of `rows` in `sentinel_base_parameters.toml` would override the version in `dataset_parameters.toml`, and the version in `sentinel-2_parameters.toml` would override the version in `sentinel_base_parameters.toml`.

To add a new collection to the portal, just add a new collection to `collections_list.toml` and restart the portal.

To add or update the parameters associated with a collection, either add a new parameters file to the `additional_parameters` array or update the parameters in one of the parameters files that the collection is already using, and then restart the portal.

The collection's ID corresponds to the `collection_id` field that each dataset has. Right now, each collection can only have one value in the `collection_id` field, but it should be possible to have multiple values (possibly by converting the field to something like a tag vocabulary) in the future.

`namespaces.toml` is a list of all the XML namespaces for the XML elements in the description documents and the search results.

All the parameters in the `_parameters.toml` file must have a `namespace` value and they must match the name of one of the namespaces in `namespaces.toml`.

See the `dataset_parameters.toml` and `collection_parameters.toml` files for more information about how the parameters files are structured.

Each parameter may define validators and converters. The parameters files explain them in more depth.

To create a new parameter, just add the definition to one of the `_parameters.toml` files and restart the portal. You may also need to write a new validator or converter function, but if the parameter isn't too exotic, the ones that are already included may be enough. The new parameter will automatically appear in the description documents for all collections that use the `_parameters.toml` file and users will automatically be able to use it when searching those collections.

Right now, collection search is just a matter of performing a search of all datasets and facetting on `collection_id` and then creating a new set of search results that contains the collections from the facet, the number of datasets in that collection that match the search (these values are included in the facet) and the collection name, ID, description etc. based on the `collection_list.toml` definitions. One the one hand, this approach isn't ideal (a dataset can only belong to one collection, for instance). On the other, it works very well, because it's easy to determine which collections match a search query and easy to count the number of matches that the user can expect when executing the same search within a given collection. Remember, the user isn't searching based on collection metadata, they're searching based on the metadata of the contents of the collections. If we give a Sentinel dataset a spatial and temporal range, it will: the whole Earth, and several years. If the user wants to know if there are collections covering London in May of 2017, that collection-level metadata isn't good enough: even if the only datasets in the collection in May of 2017 were located in the Pacific Ocean, the collection would still match the search. But since we're searching at the dataset level, then we can say that the collection is _not_ a match for that search, even though, in general, it covers the same area and timerange.

## Overview
Since this extension is being developed for the NextGEOSS project, the current version of the extension is tweaked to support the project's requirements rather than to be fully generalized, but the goal is to release a fully generalized extension that users can customize with their own profiles and parameters.

In the Earth Observation community there is a need for "two-step" search, meaning search first at the collection level and then (within one of the collections returned in step one) at the dataset level, which is the level at which CKAN search usually operates. If collection search is activated and a dataset metadata field is selected for grouping results, users can search for a collection of datasets using one set of search parameters and then search within a collection using another set of parameters specific to that dataset.

If users need to be able to link to an XML/OpenSearch representation of a dataset that _doesn't_ depend on a search query (similar to how users of CKAN can refer to dataset/{dataset-name} rather than specifying a search query that will return that dataset), you can enable record views, which return one and only one record based on a unique identifier.

## For End Users
OpenSearch is intended as an M2M (machine to machine) interface. The end user does not use it; the end user's client uses it.

All the default parameters are defined in the description documents. They are all standards-based. For more information any given parameter (beyond what is described in the description document), consult the documentation for the related standard. For more information about the description documents and the result feeds in general, consult the OGC OpenSearch documentation.

### Accessing the Description Documents
By default, the description documents are located at `/opensearch/description.xml`. The `osdd` parameter is required and determines which description document will be returned.

```
/opensearch/description.xml?osdd=dataset
```
By default, any portal using the extension will have a `dataset` description document that describes how to search all the datasets on the portal using the available parameters. "dataset" search is equivalent in scope to the standard search on portal's web frontend and via the API.

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
<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<opensearch:OpenSearchDescription xmlns:om="http://www.opengis.net/om/2.0" xmlns:time="http://a9.com/-/opensearch/extensions/time/1.0/" xmlns:esipdiscovery="http://commons.esipfed.org/ns/discovery/1.2/" xmlns:georss="http://www.georss.org/georss" xmlns:geo="http://a9.com/-/opensearch/extensions/geo/1.0/" xmlns:eo="http://a9.com/-/opensearch/extensions/eo/1.0/" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:eop="http://www.opengis.net/eop/2.1" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:param="http://a9.com/-/opensearch/extensions/param/1.0/" xmlns:custom="http://example.com/opensearchextensions/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <opensearch:ShortName>NextGEOSS</opensearch:ShortName>
    <opensearch:Description>Search products in the SENTINEL3_OLCI_L1_EFR collection.</opensearch:Description>
    <opensearch:Tags>open data CKAN opendata</opensearch:Tags>
    <opensearch:SyndicationRight>open</opensearch:SyndicationRight>
    <opensearch:Url type="application/opensearchdescription+xml" template="http://localhost:5000/opensearch/description.xml?osdd=SENTINEL3_OLCI_L1_EFR" rel="self"/>
    <opensearch:Url pageOffset="1" type="application/atom+xml" rel="results" indexOffset="1" template="http://localhost:5000/opensearch/search.atom?collection_id=SENTINEL3_OLCI_L1_EFR&amp;rows={opensearch:maxResults?}&amp;timerange_end={time:end?}&amp;metadata_modified={eo:modificationDate?}&amp;FamilyName={custom:familyname?}&amp;bbox={geo:box?}&amp;q={opensearch:searchTerms?}&amp;identifier={geo:uid?}&amp;collection_id={custom:collection_id?}&amp;spatial_geom={geo:geometry?}&amp;timerange_start={time:start?}&amp;page={opensearch:startPage?}">
        <param:Parameter name="rows" value="{opensearch:maxResults}" title="Max. results per page" minimum="0" maximum="1" minInclusive="1" maxExclusive="1001"/>
        <param:Parameter name="timerange_end" value="{time:end}" title="End of time range that results should cover" minimum="0" maximum="1">
            <param:Option value="2017-12-21T:00:00:00" label="Example end time"/>
        </param:Parameter>
        <param:Parameter name="metadata_modified" value="{eo:modificationDate}" title="Date range within which metadata was modified" minimum="0" maximum="1">
            <param:Option value="[2017-11-05T00:00:00,2017-11-05T12:00:00]" label="Example modification date range"/>
        </param:Parameter>
        <param:Parameter name="FamilyName" value="{custom:familyname}" title="The name of the family to which the products belong" minimum="0" maximum="1">
            <param:Option value="Sentinel-3" label="Products in the Sentinel-3 family"/>
        </param:Parameter>
        <param:Parameter name="bbox" value="{geo:box}" title="Bounding box that intersects with results" minimum="0" maximum="1">
            <param:Option value="-0.489,51.28,0.236,51.686" label="Bounding Box of Greater London"/>
        </param:Parameter>
        <param:Parameter name="q" value="{opensearch:searchTerms}" title="Search terms in CKAN/Solr syntax" minimum="0" maximum="1">
            <atom:link title="This parameter follows CKAN's free text search syntax, which is based on Solr's query syntax." rel="profile" href="https://docs.ckan.org/en/latest/api/index.html#ckan.logic.action.get.package_search"/>
        </param:Parameter>
        <param:Parameter name="identifier" value="{geo:uid}" title="UID of a specific product" minimum="0" maximum="1"/>
        <param:Parameter name="collection_id" value="{custom:collection_id}" title="ID of collection to search within" minimum="0" maximum="1">
            <param:Option value="SENTINEL3_SLSTR_L2_LST" label="Sentinel-3 SLSTR Level-2 Land Surface Temperature Collection"/>
            <param:Option value="METNO-GLO-SEAICE_CONC-SOUTH-L4-NRT-OBS" label="Antarctic Ocean Observed Sea Ice Concentration"/>
        </param:Parameter>
        <param:Parameter name="spatial_geom" value="{geo:geometry}" title="Arbitrary WKT shape that intersects with results" minimum="0" maximum="1">
            <param:Option value="POLYGON((-6.284 24.727,-4.834 24.867,0.879 20.982,1.077 20.592,1.912 20.015,2.197 20.118,2.966 19.58,2.944 18.958,3.34 18.813,4.043 18.854,4.021 16.426,3.384 15.581,-0.747 15.242,-3.01 14.179,-3.56 13.411,-3.955 13.646,-4.57 13.261,-4.702 12.426,-5.669 11.867,-5.647 10.661,-6.196 10.92,-6.812 10.833,-7.031 10.445,-7.625 10.682,-7.866 10.509,-8.086 11.394,-9.009 12.726,-10.195 12.404,-11.096 12.469,-11.316 13.518,-11.909 14.499,-11.448 15.178,-10.833 14.796,-10.173 15.263,-5.295 15.305,-5.076 16.32,-5.427 16.784,-6.284 24.727))" label="Mali"/>
        </param:Parameter>
        <param:Parameter name="timerange_start" value="{time:start}" title="Beginning of time range that results should cover" minimum="0" maximum="1">
            <param:Option value="2014-04-03T:00:00:00" label="Example start time"/>
        </param:Parameter>
        <param:Parameter name="page" value="{opensearch:startPage}" title="Page number" minimum="0" maximum="1" minInclusive="1" maxExclusive="100000000"/>
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
    - atom:link rel="alternate"
    - atom:category
    - atom:link rel="enclosure"


