[![Travis](https://travis-ci.org/NextGeoss/ckanext-opensearch.svg?branch=master)](https://travis-ci.org/NextGeoss/ckanext-opensearch)
[![Coveralls](https://coveralls.io/repos/NextGeoss/ckanext-opensearch/badge.svg)](https://coveralls.io/r/NextGeoss/ckanext-opensearch)

# ckanext-opensearch

ckanext-opensearch adds an OpenSearch interface to CKAN. 

## Contents

1. [Oveview](#overview)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Config Settings](#config-settings)
5. [Development Installation](#development-installation)
6. [Running the Tests](#running-the-tests)


## <a name="overview"></a>Overview
Since this extension is being developed for the NextGEOSS project, the current version of the extension is tweaked to support the project's requirements rather than to be fully generalized, but the goal is to release a fully generalized extension that users can customize with their own profiles and parameters. Even if you intend to use the defaults, you should have a look at the [config settings](#config-settings).

The extension will also optionally enable two additional OpenSearch interfaces: collection search and record views.

In the Earth Observation community there is a need for "two-step" search, meaning search first at the collection level and then (within one of the collections returned in step one) at the dataset level, which is the level at which CKAN search usually operates. If collection search is activated and a dataset metadata field is selected for grouping results, users can search for a collection of datasets using one set of search parameters and then search within a collection using another set of parameters specific to that dataset.

If users need to be able to link to an XML/OpenSearch representation of a dataset that _doesn't_ depend on a search query (similar to how users of CKAN can refer to dataset/{dataset-name} rather than specifying a search query that will return that dataset), you can enable record views, which return one and only one record based on a unique identifier.

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