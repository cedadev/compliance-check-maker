#!/usr/bin/env python

"""
write_checkers.py
=================

Writes checkers for a given project.

Usage:
------

    write_checkers.py <project_id>

"""

# Standard library imports
import os, sys, glob, re
from collections import OrderedDict as OD

# Third-party imports
import simplejson
import yaml

# Local imports
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


def get_check_defn_files(project):
    """
    Returns a list of check definition YAML files for `project`.

    :param project: project ID [string].
    :return: list of file paths.
    """
    yml_files = glob.glob(os.path.join(INPUTS_DIR, project, "*.yml"))
    yml_files.remove(os.path.join(INPUTS_DIR, project, "PROJECT_METADATA.yml"))
    return yml_files


def get_project_metadata(project):
    """
    Return project metadata.

    :return: dictionary of metadata about the project.
    """
    with open(os.path.join(INPUTS_DIR, project, "PROJECT_METADATA.yml")) as reader:
        return yaml.load(reader, Loader=yaml.Loader)[0]


def _parse_kwargs_string(s):
    """
    Parses string and returns a dictionary. All values are strings.
    :param s: string specifying key/value pairs in format: X=Y,A=10,B=hello
    :return: dictionary of parsed content
    """
    if not s: return {}
    d = dict([item.split("=") for item in s.split(";")])
    return d


def _build_check_specifier(dct):
    """
    Parse dictionary `dct` defining check and combines it with information from
    the checklib registers to create and return detailed dictionary.

    :param dct: dictionary of input details for check
    :return: dictionary defining details of a check.
    """
    # Clone the dictionary using empty strings for None values
    d = dict([(key, value or "") for key, value in dct.items()])
    d["kwargs"] = d["modifiers"] or {}
     
    d["vocabulary_ref"] = d.get("vocabulary_ref", "")
    d["comments"] = d.get("comments", "")

    # Get class to work with
    cls = get_check_class(d["check_name"])
    check = cls(d["kwargs"])

    # Update info required for rendering
    d["check_responses"] = dict([(i, response) for i, response in enumerate(check.get_messages())])
    d["description"] = check.get_description()

    # Define python interfaces
    d["python_interface"] = "{}.{}".format(cls.__module__, cls.__name__)
    d["check_unittest"] = ""

    return d


def parse_checks_definitions(check_defn_file):
    """
    Parses input files defining:
      - plugin interface to compliance checker class
      - a list of checks to implement within that class.

    :param check_defn_file: file path - defining the interface and checks [string]
    :return: tuple of (plugin interface dict, list of dictionaries of checks)
    """
    # Read in the tab-separated set of checks for this set of checks
    with open(check_defn_file) as reader:
        content = yaml.load(reader, Loader=yaml.Loader)

    # Check plugin interface is always first dictionary
    plugin_interface = content[0]
 
    checks = []

    # Populate a list of checks from remaining dictionaries
    for check_dict in content[1:]:
        d = _build_check_specifier(check_dict)
        d["plugin_id"] = plugin_interface
        checks.append(d)

    # Check check IDs are unique
    check_ids = [check["check_id"] for check in checks]
    if len(check_ids) != len(set(check_ids)):
        raise Exception("Duplicate check IDs are not allowed. Found: {}".format(check_ids))

    return plugin_interface, checks


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


def _get_unittest_details(check_class_name):
    """
    Returns the information about the module in GitHub that contains unit tests for this class.
    Response is a tuple of (unittest_module_name, unittest_url).

    :param check_class_name: name of check class
    :return: Tuple of (unittest_module_name, URL).
    """
    # Grep each module in the unittests folder until we match a function name with
    # the check class name
    candidate_modules = glob.glob("../compliance-check-lib/checklib/test/test_*.py")

    for mod in candidate_modules:

        with open(mod) as reader:
            for line in reader:

                if re.match("^def .*{}".format(check_class_name), line):
                    module_name = os.path.split(mod)[-1]
                    url = "{}/blob/master/checklib/test/{}".format(CHECK_LIB_GIT_REPO, module_name)
                    return module_name, url

    print ("[WARNING] Could not locate unit test for: {}.".format(check_class_name))
    return "", ""


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

            if check["kwargs"]:
                item += "<br/>Parameters:"

                for key, value in check["kwargs"].items():
                    item += "<br/><b>{}:</b> '{}'".format(key, value)
            else: # If no parameters tell report i
                item += "<br/>No parameters."

        elif attr == "check_unittest":
            name = check['python_interface'].split(".")[-1]
            unittest_module, unittest_url = _get_unittest_details(name)
            
            if unittest_module:
                item = "<a href='{}'>{}</a>".format(unittest_url, unittest_module)

        elif attr == "check_id":
            item = "<b>{}</b>".format(item)

        contents.append(item)

    return contents


def write_specification(project, plugin_interfaces, checks_dict):
    """
    Writes specification file in HTML format.

    :project: project ID [string]
    :param plugin_interfaces: ordered dictionary of python plugin interfaces
    :param checks_dict: dictionary of details of all checks.
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
    for plugin_interface in plugin_interfaces:
        checks = checks_dict[plugin_interface]
        content[plugin_interface] = [_get_content_for_html_row(check) for check in checks]

    check_headers = CHECK_ATTRIBUTE_MAP.values()

    # Write the HTML specification document
    write_spec_document(project_metadata, plugin_interfaces, content, check_headers, output_path)

    print "Wrote: {}".format(output_path)


def write_cc_plugin_modules(project, plugin_interfaces, checks_dict):
    """
    Writes CC plugin modules in python.

    :project: project ID [string]
    :param plugin_interfaces: ordered dictionary of python plugin interfaces
    :param checks_dict: ditionary of checks
    :return: None
    """
    project_metadata = get_project_metadata(project)

    for plugin_id, details in plugin_interfaces.items():

        # Set up output path
        output_dir = os.path.join(OUTPUT_DIR, project, "py")
        _check_exists(output_dir)

        output_path = os.path.join(output_dir, "{}.py".format(details["ccPluginPackage"].split(".")[1]))

        # Build content
        checks = checks_dict[plugin_id]

        # Write a JSON file for each plugin
        write_plugin_module(project_metadata, plugin_id, details, checks, output_path)

        print "Wrote: {}".format(output_path)


def run(project):
    """
    Write JSON rules files, specification document and code stubs.

    :project: project ID [string]
    :return: None
    """
    # Gather the data first as a list of file paths
    check_defn_files = get_check_defn_files(project)

    # Collect each of the plugin interface dicts in a list
    plugin_interfaces = OD()

    # Collect up dictionary of checks
    checks_dict = {}

    # Write a JSON file for each plugin
    for check_defn_file in check_defn_files:
        plugin_interface, checks = parse_checks_definitions(check_defn_file)
        plugin_id = plugin_interface['ccPluginId']

        plugin_interfaces[plugin_id] = plugin_interface
        checks_dict[plugin_id] = checks
        content = {"checks": checks}

    # Write the specification doc
    write_specification(project, plugin_interfaces, checks_dict)

    # Write python plugin classes for each plugin
    write_cc_plugin_modules(project, plugin_interfaces, checks_dict)


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


