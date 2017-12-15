# -*- coding: utf-8 -*-
from ckanext.opensearch.config import NAMESPACES


class OSElement(object):
    """
    Base element class.

    Used for creating other element classes. Not used directly.
    """

    def __init__(self, ns, tag_name, content='', attr={}, children=None):
        self.ns = ns
        self.tag_name = tag_name
        self.tag = '{%s}%s' % (NAMESPACES[ns], tag_name)
        self.content = content
        self.attr = attr
        self.children = children
        self.element = self.add_children(self.to_dict())

    def to_dict(self):
        """
        Return a dictionary if content and/or attr are not None or
        if children is not None. Return None if neither content nor attr are
        not None and if children is None.
        """
        element = {
            'tag': self.tag,
            'content': self.content,
            'attr': self.attr
        }

        if not self.content and not self.attr and not self.children:
            element['empty'] = True
        else:
            element['empty'] = False

        return element

    def add_children(self, element):
        """Add children to the element if the element is not None."""
        if element and self.children:
            child_elements = []
            for child, arg in self.children:
                if arg is None:
                    child_element = child().element
                    if child_element:
                        child_elements.append(child_element)
                else:
                    if type(arg) == list and len(arg):
                        for i in arg:
                            child_element = child(i).element
                            if child_element:
                                child_elements.append(child_element)
                    elif type(arg) in [dict, str, unicode]:
                        child_element = child(arg).element
                        if child_element:
                            child_elements.append(child_element)
            element['children'] = child_elements

        return element

    def _get_from_extras(self, data_dict, keys):
        """Check extras for key/value pairs using a list of possible keys."""
        extras = data_dict.get('extras')

        # Iterate through the keys and return a value as soon as
        # a matching key is found.
        for key in keys:
            if key in extras:
                return extras[key]

        # If no keys are found, return an empty string.

        return ''
