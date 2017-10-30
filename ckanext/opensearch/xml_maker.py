# -*- coding: utf-8 -*-
from lxml.builder import ElementMaker


def make_xml(frame, namespaces, ns_root):
    """Return a ready-to-use XML tree."""
    element_factory = create_element_factory(namespaces, ns_root)
    element_tree = construct_tree(element_factory, frame)

    return element_tree


def construct_tree(element_factory, json_list, parent=None):
    """
    Loop through a list of dictionaries, create XML elements, append 
    them to a parent element if possible, loop through any lists of 
    dictionaries contained within a given node, and then return the
    top-level XML element (with all of its children and siblings).
    """
    for element_dict in json_list:
        new_element = construct_element(element_factory, element_dict)
        if parent is not None:
            parent.append(new_element)
        if element_dict.get('children'):
            construct_tree(element_factory, element_dict['children'], parent=new_element)

    return new_element


def construct_element(element_factory, element_dict):
    """
    Construct an XML element using a namespace and a dictionatry.
    """

    """
    If the tag is already part of the object, then we can just pass the entire dictionary
    directly to the element factory, no need for additional logic.

    Given the fact that we can pass the dict directly to the factory, this function really
    only serves two purposes:
    one: create the tag out of the 
    """

    tag = element_dict['tag']
    content = element_dict.get('content')
    attr = element_dict.get('attr')

    if not content and not attr:
        new_el = element_factory(tag)
    elif content and not attr:
        new_el = element_factory(tag, content)
    elif attr and not content:
        new_el = element_factory(tag, attr)
    else:
        new_el = element_factory(tag, content, attr)

    return new_el



def create_nsmap(namespaces, root):
    """
    Create a dictionary for use in the nsmap attribute.
    """
    nsmap = {}
    for key, value in namespaces.items():
        if key == root:
            key = None
        nsmap[key] = value

    return nsmap


def create_element_factory(namespaces, root):
    """Return an lxml Element factory."""
    namespace = namespaces[root]
    nsmap = create_nsmap(namespaces, root)
    element_factory = ElementMaker(namespace=namespace, nsmap=nsmap)

    return element_factory
