"""
renderers.py
============

Functions to render output to:
 * HTML specification document
 * Python classes for IOOS compliance checker plugin

"""

from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader('check_maker', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)


def write_spec_document(project_metadata, plugin_interfaces, content, test_attributes, filepath):
    """
    Renders content of multiple tests into a specification document.

    :param project_metadata: dictionary of high-level metadata.
    :param plugin_interfaces: list of plugin_interfaces [strings]
    :param content: a dictionary of items to send into template.
    :param test_attributes: a list of attribute names (for table headers).
    :param filepath: output path to write to [string]
    :return: None
    """
    template = env.get_template('specification_doc.html.tmpl')
    context = {
        "project_metadata": project_metadata,
        "categories": plugin_interfaces,
        "content": content,
        "table_headers": test_attributes
    }

    with open(filepath, "w") as writer:
        writer.write(template.render(context))


def write_plugin_module(project_metadata, plugin_id, details, checks, filepath):
    """
    Renders a python plugin module based on a template.

    :param project_metadata: dictionary of high-level metadata.
    :param plugin_id: python plugin ID [string]
    :param details: dictionary of information about the plugin.
    :param checks: a list of checks to send into template.
    :param filepath: output path to write to [string]
    :return: None
    """
    template = env.get_template('cc_plugin_{}.py.tmpl'.format(details['ccPluginTemplate']))

    context = {
        "project_metadata": project_metadata,
        "plugin_id": plugin_id,
        "details": details,
        "checks": checks
    }

    with open(filepath, "w") as writer:
        writer.write(template.render(context))

