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

        return element

    def add_children(self, element):
        """Add children to the element if the element is not None."""
        if element and self.children:
            child_elements = []
            for child, arg in self.children:
                if arg == None:
                    child_element = child().element
                    if child_element:
                        child_elements.append(child_element)
                else:
                    if type(arg) == list and len(arg):
                        for i in arg:
                            child_element = child(i).element
                            if child_element:
                                child_elements.append(child_element)
                    elif type(arg) == dict:
                        child_element = child(arg).element
                        if child_element:
                            child_elements.append(child_element)
            element['children'] = child_elements

        return element

    def _get_from_extras(self, data_dict, key):
        """Get a specific value from the extras list using a key."""
        extras = data_dict.get('extras')
        value = ''
        for i in extras:
            if i['key'] == key:
                value = i['value']

        return value
