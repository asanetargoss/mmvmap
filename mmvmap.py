# (C) asanetargoss

import os
from pathlib import Path
import json
import glob
import re
import csv
import shutil
import argparse

def check_folder(folder_string, folder_description, should_exist = True):
    folder_path = Path(folder_string).expanduser().resolve()
    
    exists = folder_path.exists()
    if exists and not folder_path.is_dir():
        print("Error: The specified " + folder_description + " '" + folder_string + "' is not a valid folder")
        return None
    
    if exists and not should_exist:
        print("Error: The specified " + folder_description + " '" + folder_string + "' already exists")
        return None
    elif not exists and should_exist:
        print("Error: The specified " + folder_description + " '" + folder_string + "' does not exist")
        return None
    
    print("Using " + folder_description + " '" + folder_string + "'")
    return folder_path

def get_mcmodinfo_version(input_folder):
    mcmodinfo_file = input_folder.joinpath("mcmod.info")
    if not mcmodinfo_file.exists():
        return None
    with open(mcmodinfo_file) as modinfo:
        infodata = json.load(modinfo)
        return infodata[0]["mcversion"]
    return None

number_at_end = re.compile('[0-9]+$')
def get_latest_mapping(mappings):
    if len(mappings) > 0:
        newest = mappings[0]
        newest_version = 0
        for mapping in mappings:
            version_maybe = number_at_end.match(mapping)
            if not version_maybe:
                continue
            version = int(version_maybe[0])
            if version > newest_version:
                newest_version = version
                newest = mapping
        return newest
    return None

def get_latest_mappings_version_file(version_folder):
    stable_mapping = get_latest_mapping(glob.glob(str(version_folder.joinpath("stable_*"))))
    if stable_mapping:
        return stable_mapping
    
    snapshot_mapping = get_latest_mapping(glob.glob(str(version_folder.joinpath("snapshot_*"))))
    if snapshot_mapping:
        return snapshot_mapping
    
    return None

mcp_folder_name = re.compile('(?<=/)[0-9a-z_]+$')
def get_latest_mappings_version(version_folder):
    version_file = get_latest_mappings_version_file(version_folder)
    if version_file:
        vfile = Path(version_file)
        return vfile.parts[len(vfile.parts) - 1]
    return None

def add_mappings(mappings, mappings_file):
    with open(str(mappings_file)) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        first_row = True
        for row in csvreader:
            if first_row:
                first_row = False
                if row[0] == "searge" or row[0] == "param":
                    continue
            mappings[row[0]] = row[1]

def get_mapped(mappings, javafile):
    # TODO: More efficient technique that doesn't involve iterating over all the mappings and copying the entire file each time
    javaout = javafile
    for mapping in mappings.items():
        javaout = javaout.replace(mapping[0], mapping[1])
    return javaout

def map_or_copy_file(mappings, input_file, output_file):
    if str(input_file).endswith(".java"):
        # Map input_file and output it to output_file
        print("Mapping file " + str(input_file))
        output = ""
        with open(str(input_file)) as javafile:
            output = get_mapped(mappings, javafile.read())
        with open(str(output_file), mode='x') as javaout:
            javaout.write(output)
    elif input_file.is_dir():
        # Copy directory but do not copy contents, assuming parent directory exists
        print("Copying directory " + str(input_file))
        output_file.mkdir()
    else:
        # Copy file, assuming parent directory exists
        print("Copying file " + str(input_file))
        shutil.copy(input_file, output_file)

# Return true if successful
def recursive_copy_with_mapping(input_folder, output_folder, mapping_folder):
    mappings = {}
    add_mappings(mappings, mapping_folder.joinpath("methods.csv"))
    add_mappings(mappings, mapping_folder.joinpath("fields.csv"))
    add_mappings(mappings, mapping_folder.joinpath("params.csv"))
    
    to_copy = [input_folder]
    while len(to_copy) > 0:
        input_file = to_copy.pop(len(to_copy)-1)
        relative_input_file = input_file.relative_to(input_folder)
        output_file = output_folder.joinpath(relative_input_file)
        map_or_copy_file(mappings, input_file, output_file)
        if input_file.is_dir():
            for child in input_file.iterdir():
                to_copy.append(child)
    # Assume success. We don't do any validation but at least no exception were thrown.
    return True

MMV_CACHE_DIRECTORY = "~/.cache/MCPMappingViewer/"
DEOBF_APPEND = "_deobf"

parser = argparse.ArgumentParser(description="Recursively remap minecraft mod files from srg to mcp and place the output in a new folder. .java files are parsed and remapped, while other files are simply copied. Mapping data is taken in the format that MCP Mapping Viewer uses. Use case example: you have just decompiled a third-party Minecraft mod and would like to convert func_12345 and similar to human-readable names so you can better document the mod's features.")

parser.add_argument("input_folder", help="The folder containing files to parse and copy")
parser.add_argument("--output_folder", "-o", help="The folder to which files will be mapped and copied, defaults to input_folder with '" + DEOBF_APPEND + "' appended")

group_folder_mapping = parser.add_argument_group(title="Mapping from folder")
group_folder_mapping.add_argument("--mapping_folder", "-map", help="The folder containing the mapping files if -mmv is not specified (fields.csv, methods.csv, params.csv).")

group_mmv_mapping = parser.add_argument_group("Mapping from MCPMappingViewer cache")
group_mmv_mapping.add_argument("-mmv", action="store_true", help="Use MCPMappingViewer cache to find mapping files (" + MMV_CACHE_DIRECTORY + "). The cache is populated by running MCPMappingViewer and selecting the desired mapping.")
group_mmv_mapping.add_argument("--version", "-v", help="With -mmv, the Minecraft version to use. Defaults to the version found in mcmod.info in the input folder")
group_mmv_mapping.add_argument("--mapping_version", "-mv", help="With -mmv, the specific MCP mapping version to use, usually prefixed with either 'snapshot' or 'stable'. Defaults to most recent available version in the local filesystem.")

args_raw = parser.parse_args()
args = vars(parser.parse_args())
if args["mapping_folder"] and args["mmv"]:
    print("Error: Only one of --mapping_folder or -mmv should be defined. See --help")
elif not args["mapping_folder"] and not args["mmv"]:
    print("Error: Either --mapping_folder or -mmv must be specified. See --help")
else:
    # TODO: Check that specified folders are valid in general (input and mapping should exist, output should not exist yet) (also, perhaps it would be better if we could guarantee the utility functions always got valid file objects instead of wildcard strings)
    
    input_folder = args["input_folder"]
    
    input_folder_file = check_folder(input_folder, "input folder", True)
    if input_folder_file:
        output_folder = args["output_folder"]
        if not output_folder:
            output_folder = str(input_folder_file) + DEOBF_APPEND
            print("--output_folder was not specified. The default output folder name will be used.")
            
        output_folder_file = check_folder(output_folder, "output folder", False)
        if output_folder_file:
            mapping_folder = args["mapping_folder"]
            if not mapping_folder:
                version = args["version"]
                if version:
                    print("Using Minecraft version " + version)
                else:
                    version = get_mcmodinfo_version(input_folder_file)
                    if version:
                        print("--version was not specified. Automatically detected Minecraft version " + version)
                if not version:
                    print("Error: The Minecraft version could not be automatically detected from the input folder contents (consider adding --version argument)")
                else:
                    mapping_version = args["mapping_version"]
                    if mapping_version:
                        print ("Using MCP mapping version " + mapping_version)
                    else:
                        version_folder_path = check_folder(MMV_CACHE_DIRECTORY + "/" + version, "version folder", True)
                        
                        if version_folder_path:
                            mapping_version = get_latest_mappings_version(version_folder_path)
                            if not mapping_version:
                                print("Error: No mapping folder found in '" + str(version_folder_path) + "' for Minecraft version " + version)
                            else:
                                print("--mapping_version was not specified. Latest MCP mapping version available in local files is " + mapping_version)
                    if mapping_version:
                        mapping_folder = MMV_CACHE_DIRECTORY + "/" + version + "/" + mapping_version
            if mapping_folder:
                mapping_folder_file = check_folder(mapping_folder, "mapping folder", True)
                # TODO: Verify mapping folder has valid contents
                
                if mapping_folder_file:
                    print("\nMapping to '" + str(output_folder_file) + "'...\n")
                    success = recursive_copy_with_mapping(input_folder_file, output_folder_file, mapping_folder_file)
                    if success:
                        print("\nMapping finished. Output is in '" + str(output_folder_file) + "'")
                    else:
                        print("\nMapping FAILED.")