# -*- coding: utf-8 -*-
from ckan.common import _, config

plugins = config.get('ckan.plugins')
if plugins and 'spatial_query' in plugins:
    from ckanext.spatial.lib import validate_bbox


class QueryValidator(object):
    """Validate query parameters and create a list of errors."""
    def __init__(self, param_dict, valid_params):
        self.param_dict = param_dict
        self.valid_params = valid_params
        self.param_counts = self._count_params()
        self.errors = []
        self._validate_query()

    def _has_params(self):
        """Verify that there really is a query."""
        if not self.param_dict:
            self.errors.append(_('You must specify at least one parameter.'))

    def _has_no_invalid_params(self):
        """Check for invalid query parameters."""
        for param in self.param_dict:
            if param not in self.valid_params:
                self.errors.append(_('Invalid parameter: {}.'.format(param)))

    def _count_params(self):
        """Count the instances of each valid parameter in the query."""
        param_counts = {}
        for param in self.param_dict:
            if param in self.valid_params:
                if param not in param_counts:
                    param_counts[param] = 1
                else:
                    param_counts[param] += 1

        return param_counts

    def _minimums_are_met(self):
        """
        Check that the minimum number of instances of each parameter are met.

        This also checks if required parameters are present, since they have
        minimum == 1.
        """
        for param, count in self.param_counts.items():
            minimum = self.valid_params[param]['minimum']
            if count < minimum:
                self.errors.append(_('You must have at least {} instances of "{}".'.format(minimum, param)))

    def _maximums_are_not_exceeded(self):
        """
        Check that the maximum number of instances of each parameter
        are not exceeded.
        """
        for param, count in self.param_counts.items():
            maximum = self.valid_params[param]['maximum']
            if maximum != '*' and count > maximum:
                self.errors.append(_('You cannot have more than {} instances of "{}".'.format(maximum, param)))

    def _value_is_in_bounds(self, param, minimum, maximum):
        """
        Check that a value is an integer and is between the minimum and
        maximum.
        """
        value = self.param_dict.get(param)
        error = False
        if value:
            try:
                value = int(value)
            except ValueError:
                error = True
            if not (value <= maximum and value > minimum):
                error = True
            if error:
                os_name = self.valid_params[param]['os_name']
                self.errors.append(_('{} must be an integer from {} to {}.'.format(os_name, minimum, maximum))) 

    def _rows_are_in_bounds(self):
        """Check that the rows value is in bounds, if the parameter is present."""
        return self._value_is_in_bounds('rows', 1, 1001)

    def _page_is_in_bounds(self):
        """Check that the page value is in bounds, if the parameter is present."""
        return self._value_is_in_bounds('page', 1, 99999999)

    def _bbox_is_valid(self):
        """Check if the bounding box has a valid form, if the parameter is present."""
        ext_bbox = self.param_dict.get('ext_bbox')
        if ext_bbox and not validate_bbox(ext_bbox):
            self.errors.append(_('geo:box must be in the form `west,south,east,north` or `minX,minY,maxX,maxY`.'))

    def _validate_query(self):
        """Update the error list."""
        checks = [
            self._has_params,
            self._has_no_invalid_params,
            self._minimums_are_met,
            self._maximums_are_not_exceeded,
            self._rows_are_in_bounds,
            self._page_is_in_bounds,
            self._bbox_is_valid
        ]
        for check in checks:
            check()
