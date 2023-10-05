import json
import sys
from jsonschema import Draft4Validator, RefResolver, SchemaError
import os
import glob
import warnings
from pathlib import Path


def get_json_from_file(filename):
    """Loads JSON from a file."""
    try:
        with open(filename, "r") as f:
            fc = f.read()
        return json.loads(fc)
    except FileNotFoundError:
        warnings.warn("File not found: " + filename)
    except IOError as exc:
        warnings.warn("I/O error while opening " + filename + ": " + str(exc))
    except json.JSONDecodeError as exc:
        warnings.warn("Failed to parse JSON in " + filename + ": " + str(exc))


def get_validator(filename, base_uri=""):
    """Load schema from JSON file;
    Check whether it's a valid schema;
    Return a Draft4Validator object.
    Optionally specify a base URI for relative path
    resolution of JSON pointers (This is especially useful
    for local resolution via base_uri of form file://{some_path}/)
    """

    schema = get_json_from_file(filename)
    try:
        # Check schema via class method call. Works, despite IDE complaining
        # However, it appears that this doesn't catch every schema issue.
        Draft4Validator.check_schema(schema)
        print("%s is a valid JSON schema" % filename)
    except SchemaError:
        raise
    if base_uri:
        resolver = RefResolver(base_uri=base_uri, referrer=filename)
    else:
        resolver = None
    return Draft4Validator(schema=schema, resolver=resolver)


def validate(validator, instance):
    """Validate an instance of a schema and report errors."""
    if validator.is_valid(instance):
        print("Validation Passes")
        return True
    else:
        es = validator.iter_errors(instance)
        recurse_through_errors(es)
        print("Validation Fails")
        return False
        # sys.exit("Validation Fails")


def recurse_through_errors(es, level=0):
    """Recurse through errors posting message
    and schema path until context is empty"""
    for e in es:
        warnings.warn(
            "***" * level
            + " subschema level "
            + str(level)
            + "\t".join([str(e.message), "Path to error:" + str(e.absolute_schema_path)])
            + "\n"
        )
        if e.context:
            level += 1
            recurse_through_errors(e.context, level=level)


def run_validator(path_to_schema_dir, schema_file, path_to_test_dir):
    """Tests all instances in a test_folder against a single schema.
    Assumes all schema files in single dir.
    Assumes all *.json files in the test_dir should validate against the schema.
       * path_to_schema_dir:  Absolute or relative path to schema dir
       * schema_file: schema file name
       * test_dir: path to test directory (absolute or local to schema dir)
    """
    file_ext = "json"
    # Getting script directory, schema directory and test directory
    script_folder = Path(os.path.dirname(os.path.realpath(__file__)))
    schema_dir = Path(os.path.dirname(path_to_schema_dir))
    test_dir = Path(os.path.dirname(path_to_test_dir))
    if not os.path.exists(os.path.join(script_folder, schema_dir)):
        raise Exception("Please provide valid path_to_schema_dir")
    if not os.path.exists(os.path.join(script_folder, test_dir)):
        raise Exception("Please provide valid path_to_test_dir")
    else:
        sv = get_validator(os.path.join(script_folder, schema_dir, schema_file))
        test_dir_files = "".join(["/*.", file_ext])
        test_files = glob.glob(pathname=os.path.join(script_folder, test_dir) + test_dir_files)
        # print("Found test files: %s in %s" % (str(test_files), path_to_test_dir))
        for instance_file in test_files:
            i = get_json_from_file(instance_file)
            print("Testing: %s" % instance_file)
            validate(sv, i)


if __name__ == "__main__":
    run_validator(
        path_to_schema_dir="../", schema_file="general_schema.json", path_to_test_dir="../examples/"
    )
