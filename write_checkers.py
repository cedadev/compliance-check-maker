#!/usr/bin/env python

import os, sys
from collections import OrderedDict as OD
import simplejson

from check_maker.renderers import write_spec_document, write_plugin_module
from checklib.register import get_check_class

CHECK_LIB_GIT_REPO = "https://github.com/cedadev/compliance-check-lib"

OUTPUT_DIR = "output"
INPUTS_DIR = "project"

CHECK_ATTRIBUTE_MAP = OD([
    ("check_id", "Check ID"),
    ("description", "Description"),
    ("vocabulary_ref", "Controlled Vocab ref"),
    ("check_level", "Level"),
    ("check_responses", "Responses"),
    ("comments", "Comments"),
    ("python_interface", "Python check (link to repository)"),
    ("check_unittest", "Python unittest")
])

def _check_exists(dr):
    """
    Ensures a directory ``dr`` exists.
    :param dr: directory path
    :return: None
    """
    if not os.path.isdir(dr): os.makedirs(dr)

def get_categories(project):
    """
    Reads in the categories of checks.

    :project: project ID [string]
    :return: a list of categories.
    """
    with open(os.path.join(INPUTS_DIR, project, "CATEGORIES.json")) as reader:
        content = simplejson.load(reader)["categories"]

    resp = OD()

    for item in content:
        key = item.keys()[0]
        value = item[key]
        resp[key] = value

    return resp

def get_project_metadata(project):
    """
    Return project metadata.

    :return: dictionary of metadata about the project.
    """
    with open(os.path.join(INPUTS_DIR, project, "PROJECT_METADATA.json")) as reader:
        return simplejson.load(reader)

def _parse_kwargs_string(s):
    """
    Parses string and returns a dictionary. All values are strings.
    :param s: string specifying key/value pairs in format: X=Y,A=10,B=hello
    :return: dictionary of parsed content
    """
    if not s: return {}
    d = dict([item.split("=") for item in s.split(";")])
    return d

def _build_check_specifier(check_line, keys):
    """
    Parse single line defining check and combines it with information from
    the checklib registers to create detailed dictionary.

    :param check_line: tab-separated line of text
    :param keys: a list of keys
    :return: dictionary defining details of a check.
    """
    items = check_line.split("\t")
    d = dict([(keys[i], value) for i, value in enumerate(items)])
    d["kwargs"] = _parse_kwargs_string(d.get("modifiers", ""))
    d["vocabulary_ref"] = d.get("vocabulary_ref", "")
    d["comments"] = d.get("comments", "")

    # Get class to work with
    cls = get_check_class(d["check_name"])
    check = cls(d["kwargs"])

    # Update info required for rendering
    d["check_responses"] = dict([(i, response) for i, response in enumerate(check.get_messages())])
    d["description"] = check.get_description()
    d["check_unittest"] = "DEFAULT"
    d["python_interface"] = "{}.{}".format(cls.__module__, cls.__name__)

    return d


def gather_checks(project, category):
    """
    Gathers all the checks for a single category and returns them as
    a list of dictionaries.

    :project: project ID [string]
    :param category: the category of checks [string]
    :return: list of dictionaries of checks
    """
    fname = os.path.join(INPUTS_DIR, project, "{}.txt".format(category))

    # Read in the tab-separated set of checks for this category
    with open(fname) as reader:
        content = [line.strip() for line in reader.readlines()]

    # Get the keys from the top line
    keys = content[0].strip().split("\t")

    checks = []

    # Populate a list of checks
    for check_line in content[1:]:
        d = _build_check_specifier(check_line, keys)
        d["category"] = category
        checks.append(d)

    # Check check IDs are unique
    check_ids = [check["check_id"] for check in checks]
    if len(check_ids) != len(set(check_ids)):
        raise Exception("Duplicate check IDs are not allowed. Found: {}".format(check_ids))

    return checks

def write_to_json(project, category, content):
    """
    Writes to a json file.

    :project: project ID [string]
    :param category: category [string]
    :param content: content as a list of dictionaries.
    :return: None
    """
    # Set up output path
    output_dir = os.path.join(OUTPUT_DIR, project, "json")
    _check_exists(output_dir)
    output_path = os.path.join(output_dir, "{}.json".format(category))

    # Write output to JSON
    with open(output_path, 'w') as writer:
        simplejson.dump(content, writer, indent=4, sort_keys=True)

    print "Wrote: {}".format(output_path)


def _html_tidy_cell_item(item, key):
    """
    Returns HTML-tidied item for putting in table cell.

    :param item: item to be tidied
    :param key: dictionary key (for reference)
    :return: tidied HTML item or string
    """
    if isinstance(item, dict):
        resp = "<br/>\n".join(["{}: {}".format(key, value) for key, value in item.items()])
        resp += "<br/>{}: SUCCESS!".format(int(key) + 1)
        return resp

    return item


def _get_check_url(check_module, check_class_name):
    """
    Returns the URL to the line in GitHub that represents that checker class.

    :param check_module: python module containing check
    :param check_class_name: name of check class
    :return: URL to check [string].
    """
    # Try to grep line number for class
    try:
        loc_of_module = "../compliance-check-lib/{}.py".format(check_module)
        with open(loc_of_module) as reader:
            for n, line in enumerate(reader):
                if line.find("class {}".format(check_class_name)) == 0:
                    line_number = n + 1
                    break
    except:
        line_number = ""

    return "{}/blob/master/{}.py#L{}".format(CHECK_LIB_GIT_REPO, check_module, line_number)


def _get_content_for_html_row(check):
    """
    Returns a list of content for each HTML cell in a table for a given check.

    :param check: check dictionary (from config)
    :return: list of check contents for HTML row.
    """
    contents = []

    for attr in CHECK_ATTRIBUTE_MAP.keys():
        item = _html_tidy_cell_item(check[attr], attr)

        # Handle python interface specifically
        if attr == "python_interface":
            rel_path = item.replace(".", "/")
            base, name = os.path.split(rel_path)

            check_url = _get_check_url(base, name)
            item = "<a href='{}'>{}</a>".format(check_url, name)
            item += "<br/>Parameters:"

            for key, value in check["kwargs"].items():
                item += "<br/><b>{}:</b> '{}'".format(key, value)

        elif attr == "check_id":
            item = "<b>{}</b>".format(item)

        contents.append(item)

    return contents


def write_specification(project, categories):
    """
    Writes specification file in HTML format.

    :project: project ID [string]
    :param categories: dictionary of categories
    :return: None
    """
    project_metadata = get_project_metadata(project)

    # Set up output path
    output_dir = os.path.join(OUTPUT_DIR, project, "html")
    _check_exists(output_dir)
    output_path = os.path.join(output_dir, "{}_data_specification_{}.html".format(project,
                                                                                  project_metadata["checks_version"]))

    content = OD()

    # Build content
    for category in categories:
        checks = gather_checks(project, category)
        content[category] = [_get_content_for_html_row(check) for check in checks]

    check_headers = CHECK_ATTRIBUTE_MAP.values()

    # Write a JSON file for each category
    write_spec_document(project_metadata, categories, content, check_headers, output_path)

    print "Wrote: {}".format(output_path)


def write_cc_plugin_modules(project, categories):
    """
    Writes CC plugin modules in python.

    :project: project ID [string]
    :param categories: dictionary of categories
    :return: None
    """
    project_metadata = get_project_metadata(project)

    for category, details in categories.items():

        # Set up output path
        output_dir = os.path.join(OUTPUT_DIR, project, "py")
        _check_exists(output_dir)

        output_path = os.path.join(output_dir, "{}.py".format(details["ccPluginPackage"].split(".")[1]))

        # Build content
        checks = gather_checks(project, category)

        # Write a JSON file for each category
        write_plugin_module(project_metadata, category, details, checks, output_path)

        print "Wrote: {}".format(output_path)


def run(project):
    """
    Write JSON rules files, specification document and code stubs.

    :project: project ID [string]
    :return: None
    """
    # Gather the data first as a list of dictionaries
    categories = get_categories(project)

    # Write a JSON file for each category
    for category in categories:
        checks = gather_checks(project, category)
        content = {"checks": checks}
        write_to_json(project, category, content)

    # Write the specification doc
    write_specification(project, categories)

    # Write python plugin classes for each category
    write_cc_plugin_modules(project, categories)


def main():
    """
    Run the check maker.

    :return: None
    """
    DEFAULT = "example_proj"
    if len(sys.argv) > 1:
        proj = sys.argv[1]
    else:
        proj = DEFAULT

    run(proj)


if __name__ == "__main__":

    main()


