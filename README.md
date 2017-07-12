# Compliance Check Maker - a tool to write project-specific plugins and data specifications for the IOOS compliance checker

## Overview

Most data projects require that the products comply with some pre-agreed specification.

There is a need to:
 - provide a specification document to data providers
 - provide a compliance checking tool to validate products against the specification

This code-base scans in a set of "checks" in tab-separated variable (TSV) files and
then automatically writes:
 - an HTML specification document
 - the python stubs for modules that can be implemented as plugins within the
   [IOOS compliance checker](https://github.com/ioos/compliance-checker)

## Using the tool for your own project

To get this tool working with a new project, you need to do the following:

 1. Copy the `project/example_proj` directory to a `project/<your_project>`.
 2. Edit the `project/<your_project>/PROJECT_METADATA.json` file to reflect information
    about your project.
 3. Edit the `project/<your_project>/CATEGORIES.json` file to reflect information about
    the categories of "checks" that you want to build.
 4. For each category of checks: write a `project/<your_project>/<category>.txt` file
    based on the structure of the `project/<your_project>/example-category.txt` format.

### The format of the TSV files

Each TSV file must follow the structure of the `project/<your_project>/global-attrs.txt`
file. This means that the header line should contain the following columns:

 - check_id: the short ID for each check
 - check_name: the name of the python class that runs the actual check
 - check_level: HIGH, MEDIUM or LOW (which equate to MUST, SHOULD, INFO) [OPTIONAL]
 - vocabulary_ref: an identifier for the controlled vocabulary to be looked up [OPTIONAL]
 - modifiers: specified key/value parameters to send into the check [OPTIONAL]
 - comments: notes to explain the purpose of context of the check [OPTIONAL]
