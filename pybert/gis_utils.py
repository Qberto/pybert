__author__ = 'Alberto Nieto'
__version__ = "0.0.1"

import os
import general_utils
import arcpy
import shutil
import time
import logging as log
from datetime import datetime


# TODO Add lambda function for Pandas column write based on other column
# def nps_range_calc(survey_result_text):
# if survey_result_text == "Definitely not recommend":
# return 1
# elif survey_result_text == "Probably not":
# return 2
# elif survey_result_text == "Might or might not":
# return 3
# elif survey_result_text == "Probably":
# return 4
# elif survey_result_text == "Definitely recommend":
#     return 5
# else:
#     return 99999

# # Apply the nps_range function to a new dataframe column
# nps_df['NPS_Range'] = nps_df.apply(lambda x: nps_range_calc(x['u39_resp00']), axis=1)
# END TODO


def ArcGISVersionChecker():
    """
    Determines the version of ArcGIS Desktop that the user has installed and returns outputs based on the input
    parameter
    :args:
    :return:
    desktop_version (string) - String corresponding to the full version of ArcGIS Desktop
    guid_folder (string) - String corresponding to the installation GUID key
    program_files_folder (string) - String corresponding to the program files folder based on the version
    """
    installer_folder = r"C:\Windows\Installer"  # Establishes a path to the default Windows installer folder

    # Establishes a version dictionary containing the guid values and program files folder corresponding to each
    # version of ArcGIS Desktop
    arcgis_version_dictionary = {
        "ArcGIS_10.3.1": {"guid": "{831DD630-F230-49C6-AD41-312E8E0F9CEE}", "program_files_folder": "Desktop10.3"},
        "ArcGIS_10.3": {"guid": "{9A0BC33A-EAA8-4ED4-8D0C-CB9B42B06D7F}", "program_files_folder": "Desktop10.3"},
        "ArcGIS_10.2.2": {"guid": "{761CB033-D425-4A16-954D-EA8DEF4D053B}", "program_files_folder": "Desktop10.2"},
        "ArcGIS_10.2.1": {"guid": "{8777990C-4F53-4782-9A38-E60343B5053D}", "program_files_folder": "Desktop10.2"},
        "ArcGIS_10.2": {"guid": "{44EF0455-5764-4158-90B3-CA483BCB1F75}", "program_files_folder": "Desktop10.2"},
        "ArcGIS_10.1": {"guid": "{6C8365F4-1102-4064-B696-68842D20B933}", "program_files_folder": "Desktop10.1"}
    }

    """ Main iteration """
    # Iterate on each key in the arcgis_version_dictionary
    for version in arcgis_version_dictionary:
        # Create the installer_path variable by linking it to the installer_folder string
        installer_path = str(installer_folder) + "\\" + str(arcgis_version_dictionary[version]["guid"])

        # Perform verification to determine if the installer_path exists
        if arcpy.Exists(installer_path):
            # Designate the desktop_version variable for output
            desktop_version = str(version)
            # Designate the guid_folder folder for output
            guid_folder = arcgis_version_dictionary[version]["guid"]
            # Designate the program_files_folder variable for output
            program_files_folder = arcgis_version_dictionary[version]["program_files_folder"]

            # Break iteration upon the first installation folder found in sequence from newest to oldest
            break

        else:
            desktop_version = None
            guid_folder = None
            program_files_folder = None

    #TODO Check Business Analyst data

    #TODO Check BG Geoprocessing result

    return desktop_version, guid_folder, program_files_folder


def get_network_routing_dataset():
    """
    Method that determines which version of ArcGIS exists on the running system and retrieves the correct
    network analyst path
    :return: Path to Network Analyst routing dataset
    """

    # Set 'DesktopVersion' variable for use in directory reference paths by invoking the ArcGISVersionChecker function
    # We need to explicitly return the index 2 result since this points to the process folder path needed for this tool
    desktop_version = ArcGISVersionChecker()[2]

    if desktop_version == "Desktop10.3":
        network_dataset = r"C:\ArcGIS\Business Analyst\US_2014\Data\Streets Data\NAVTEQ_2014_Q1_NA.gdb\Routing\Routing_ND"
    elif desktop_version == "Desktop10.2":
        network_dataset = r"C:\ArcGIS\Business Analyst\US_2013\Data\Streets Data\NAVTEQ_2013_Q1_NA.gdb\Routing\Routing_ND"
    else:
        network_dataset = None

    return network_dataset


def make_attribute_dict(fc, key_field, attr_list=['*']):
    """
    Creates a python dictionary from the attribute table of a GIS feature class
    :param fc: Feature Class
    :param key_field: Key ID field to use in the operation
    :param attr_list: List of attributes to bring to the dictionary
    :return: Python dictionary of attributes
    """
    # Import needed modules
    import arcpy

    attdict = {}
    fc_field_objects = arcpy.ListFields(fc)
    fc_fields = [field.name for field in fc_field_objects if field.type != 'Geometry']
    if attr_list == ['*']:
        valid_fields = fc_fields
    else:
        valid_fields = [field for field in attr_list if field in fc_fields]
    # Ensure that key_field is always the first field in the field list
    cursor_fields = [key_field] + list(set(valid_fields) - set([key_field]))
    with arcpy.da.SearchCursor(fc, cursor_fields) as cursor:
        for row in cursor:
            attdict[row[0]] = dict(zip(cursor.fields, row))
    return attdict


# Utility to transfer GIS table attributes to Python dictionary
def make_single_attribute_dict(fc, key_field, attr_field):
    """ Create a dictionary of feature class/table attributes.
        Default of ['*'] for attr_list (instead of actual attribute names)
        will create a dictionary of all attributes. """
    # Import needed modules
    import arcpy
    # Build dictionary container
    attr_dict = {}
    # Ensure that key_field is always the first field in the field list
    cursor_fields = [key_field, attr_field]
    # Start hydrating dictionary with field values
    with arcpy.da.SearchCursor(fc, cursor_fields) as cursor:
        for row in cursor:
            attr_dict[row[0]] = row[1]
    # Return the output dictionary
    return attr_dict


def build_lookup_dict(fc, id_field, val_field):
    """
    Creates a python lookup dictionary out of the feature class
    :param fc: sites feature class path
    :param did_field: did field in the sites fc
    :param name_field: name field in the sites fc
    :param format_field: format field in the sites fc
    :param micromarket_field: micromarket field in the sites fc
    :return: dictionary where key=did; value=name
    """
    # Create empty dict
    lookup_dict = {}
    # Iterate on the fc to start building the dictionary
    with arcpy.da.SearchCursor(fc, [id_field, val_field]) as cursor:
        for row in cursor:
            # Extract field values to vars
            id_val = str(row[0])
            source_val = row[1]

            # Create id dict
            id_dict = {str(id_field): id_val,
                       str(val_field): source_val}

            # Write the did_dict in the dictionary key for the did
            lookup_dict[id_val] = id_dict

    # Return the final lookup dictionary
    return lookup_dict


def build_site_dict(sites_fc, did_field, name_field, micromarket_field, format_field):
    """
    Creates a python dictionary out of the sites feature class
    :param sites_fc: sites feature class path
    :param did_field: did field in the sites fc
    :param name_field: name field in the sites fc
    :param format_field: format field in the sites fc
    :param micromarket_field: micromarket field in the sites fc
    :return: dictionary where key=did; value=name
    """
    # Create site_dict
    site_dict = {}
    # Iterate on the sites fc to start building the dictionary
    with arcpy.da.SearchCursor(sites_fc, [did_field,
                                          name_field,
                                          micromarket_field,
                                          format_field
    ]) as cursor:
        for row in cursor:
            # TODO Write fields to values and continue expanding dictionary

            # Extract field values to vars
            did = row[0]
            name = row[1]
            micromarket = row[2]
            format = row[3]

            # Create did dict
            did_dict = {'name': name,
                        'micromarket': micromarket,
                        'format': format}

            # Write the did_dict in the dictionary key for the did
            site_dict[did] = did_dict

    # Return the final site_dict
    return site_dict


def validate_fgdb(gdb_path):
    """
    Validates file geodatabase given a file path
    :param gdb_path: Local UNC path to file geodatabase
    :return: Boolean
    """
    desc = arcpy.Describe(gdb_path)
    if desc.dataType == "Workspace":
        print("file gdb validated.")
        return True
    else:
        print("Validation failed. Path data type returned as {0}".format(desc.dataType))
        return False


def validate_egdb_connection(conn_path):
    """
    Validates a connection to an enterprise geodatabase
    :param conn_path: UNC path to connection file
    :return: Boolean
    """
    if arcpy.Exists(conn_path):
        print("Connection path '{0}' exists.".format(conn_path))
        return True
    else:
        print("Connection path '{0}' invalid.".format(conn_path))
        return False


def validate_fc_exists(fc_path):
    """
    Validates a feature class exists given a full path
    :param fc_path:
    :return: Boolean
    """
    if arcpy.Exists(fc_path):
        print("Feature class at '{0}' exists.".format(fc_path))
        return True
    else:
        print("Feature class path '{0}' invalid.".format(fc_path))


def gis_table_to_csv(in_table,
                     outdir,
                     outname,
                     append_to_existing_csv=False,
                     included_fields="*"):
    """
    Converts a gis table to a csv file
    :param in_table:
    :param outdir:
    :param outname:
    :param append_to_existing_csv:
    :param included_fields:
    :return:
    """
    import csv

    inclFields = [f.name for f in arcpy.ListFields(in_table, included_fields)]
    if not append_to_existing_csv:
        # print "First time opening output csv!"
        with open(os.path.join(outdir, outname), 'wb') as f:
            writer = csv.writer(f)
            writer.writerow(inclFields)
            with arcpy.da.SearchCursor(in_table, inclFields) as cursor:
                for row in cursor:
                    writer.writerow(row)
        f.close()
    else:
        # print "NOT First time opening output csv!"
        with open(os.path.join(outdir, outname), 'a') as f:
            writer = csv.writer(f)
            writer.writerow(inclFields)
            with arcpy.da.SearchCursor(in_table, inclFields) as cursor:
                for row in cursor:
                    writer.writerow(row)
        f.close()


def field_exists(feature_class,
                 field_name):
    """
    Determines if a field exists in a feature class, returning a boolean value
    :param feature_class:
    :param field_name:
    :return:
    """
    try:
        field_list = arcpy.ListFields(feature_class, field_name)
        field_count = len(field_list)
        if field_count == 1:
            return True
        else:
            return False
    except Exception, e:
        print e.message
        return False


def get_field_type(fc, field):
    """
    Determine the field type of a field in a feature class
    :param fc:
    :param field:
    :return:
    """
    field_object = arcpy.ListFields(fc, field)[0]
    return field_object.type


def verify_data_requirements(required_data_list):
    """
    Validate that the user has required datasets from a list installed on their local machine
    :param required_data_list:
    :return:
    """

    # For each required dataset in the required dataset list:
    for required_dataset in required_data_list:
        # If the given require dataset does not exist on the system:
        if arcpy.Exists(required_dataset) == False:
            # Raise a Fatal Error
            print "\t\t\t\t" + "verify_data_requirements: Required Dataset not found. The Required Dataset " + str(
                required_dataset) + " could not be located on the system."
            return False
        # Otherwise:
        else:
            print "\t\t\t\t" + "verify_data_requirements: All Required Datasets found."
            # Return a boolean True value
            return True


def check_workspace_folders(work_folders_expected):
    """
    Performs a check on the current configuration of the procedure and fixes workspace folders if needed
    :return:
    """
    method_message = "\t\tADPTaskScheduler.verify_workspace: "

    # Create the directory if it does not already exist
    print("{0}Performing workspace verification...".format(method_message))
    for folder in work_folders_expected:
        if not os.path.exists(folder):
            print("{0}Expected folder '{1}' not found. Creating...".format(method_message, folder))
            os.makedirs(folder)


def calculate_field(workspace, common_id_field, target_fc, target_field, source_fc, source_field, verbose=False):
    """
    Start an edit session, allowing the user to calculate values into a field in a target feature class
    :param target_fc:
    :param target_id_field:
    :param target_field:
    :param source_field:
    :return:
    """
    print("calculate_field: Determining input field types...")
    target_field_type = get_field_type(target_fc, target_field)
    source_field_type = get_field_type(source_fc, source_field)
    if target_field_type != source_field_type:
        print("Target Field ({0}) and Source Field ({1}) differed in data type!".format(target_field_type,
                                                                                        source_field_type))
        print("Make sure the two fields are of the same type dummy!")
    else:
        print("Source and Target fields matched data type ({0}, {1}). Continuing...".format(source_field_type,
                                                                                            target_field_type))

        # Start an edit session. Must provide the workspace.
        edit = arcpy.da.Editor(workspace)
        # Edit session is started without an undo/redo stack for versioned data
        #  (for second argument, use False for unversioned data)
        edit.startEditing(False, True)
        # Start an edit operation
        edit.startOperation()

        # Build site dictionary to bring names, micromarket, and format values to the output
        print("calculate_field: Building lookup dictionary...")
        lookup_dict = build_lookup_dict(source_fc, common_id_field, source_field)

        # Use the site dictionary to calc values into the needed fields
        print("calculate_field: Performing attribute calc...")
        with arcpy.da.UpdateCursor(target_fc, [common_id_field, target_field]) as cursor:
            for row in cursor:
                # Declare var for the current id
                id_val = str(row[0])
                try:
                    # Determine what the source value is based on the lookup_dict
                    source_val = lookup_dict[id_val][source_field]
                    # Write the lookup source value to the target attribute
                    row[1] = source_val if source_val else row[1]
                    # Update the current row
                    cursor.updateRow(row)
                    if verbose:
                        print("ID '{0}' successfully calculated.".format(id_val))
                except KeyError as e:
                    if verbose:
                        print("ID '{0}' did not have a corresponding source value. Passing.".format(id_val))
                    pass

        # Stop the edit operation.
        edit.stopOperation()
        # Stop the edit session and save the changes
        edit.stopEditing(True)


def create_where_clause_from_list(targetdata, targetdata_field, attributelist):
    """
    Create a SQL statement given a list of attributes
    :param targetdata:
    :param targetdata_field:
    :param attributelist:
    :return:
    """
    whereclause = ""
    strlist = []
    #Check to see if attribute list is an empty list
    if not (attributelist):
        raise ValueError("Empty List")
    #Assign strlist if a list of strings is passed
    if all(isinstance(item, (str)) for item in attributelist):
        strlist = "'" + "','".join(attributelist) + "'"
    #Assign strlist if a list of numbers is passed
    if all(isinstance(item, (int, float, long)) for item in attributelist):
        strlist = ",".join([str(item) for item in attributelist])
    #Create the whereclause from strlist and return the whereclause
    if strlist:
        whereclause = "{0} in ({1})".format(arcpy.AddFieldDelimiters(targetdata, targetdata_field), strlist)
        return whereclause
    #Raise a value error if the attribute list was not all strings or all numbers
    else:
        raise ValueError("List items are not all strings or all numbers.")


def select_diff_records(feature_layer,
                        joined_layer_name,
                        id_field,
                        diff_field,
                        selection_type="NEW_SELECTION",
                        diff_type="both",  # left/right/both
                        only_use_joined_records=False,
                        diff_print=False,
                        calc_values_over=False,
                        allow_field_calc=False):
    """
    Function to perform a selection on records where the values differ between two fields
    :param data:
    :param field_one:
    :param field_two:
    :return:
    """
    # Create an empty list that will contain id values for the diff records
    diff_ids = []

    # Variables for field names
    source_id_field = "{0}.{1}".format(feature_layer, id_field)
    joined_id_field = "{0}.{1}".format(joined_layer_name, id_field)
    field_one = "{0}.{1}".format(feature_layer, diff_field)
    field_two = "{0}.{1}".format(joined_layer_name, diff_field)

    # Determine if we want to perform a diff on only the records that were successfully joined
    # i.e. if 450 records are joined to 800, perform the diff on only 450 records
    if only_use_joined_records:
        where_clause = arcpy.AddFieldDelimiters(feature_layer, joined_id_field) + " IS NOT NULL"
        arcpy.SelectLayerByAttribute_management(feature_layer, where_clause=where_clause)
        print("Using {0} joined records as total record list.".format(arcpy.GetCount_management(feature_layer)))

    # Iterate on the feature class, adding ids to the diff_ids list as it finds differences
    with arcpy.da.SearchCursor(feature_layer,
                               [source_id_field, field_one, field_two]) as cursor:
        for row in cursor:
            if row[1] != row[2]:
                # Handle diff type
                if diff_type == "values_from_both":
                    diff_ids.append(str(row[0]))
                elif diff_type == "values_from_left":
                    if row[1] == None:
                        diff_ids.append(str(row[0]))
                elif diff_type == "values_from_right":
                    if row[2] == None:
                        diff_ids.append(str(row[0]))

    if len(diff_ids) == 0:
        print("Diff resulted in no records with a difference.")
        diff_flag = False
        arcpy.SelectLayerByAttribute_management(feature_layer, selection_type="CLEAR_SELECTION")
    else:
        print("Diff IDs list complete.")
        print("{0} records being selected...".format(len(diff_ids)))
        diff_flag = True
        diff_where_clause = create_where_clause_from_list(feature_layer, source_id_field, diff_ids)
        arcpy.SelectLayerByAttribute_management(feature_layer,
                                                selection_type=selection_type,
                                                where_clause=diff_where_clause)

    if diff_print and diff_flag:
        print("Printing diff results...\n\n")
        with arcpy.da.SearchCursor(feature_layer, [source_id_field, field_one, field_two], where_clause) as cursor:
            for row in cursor:
                print("\nID '{0}': \t'{1}'={2}\t'{3}'={4}".format(str(row[0]),
                                                                  field_one, str(row[1]),
                                                                  field_two, str(row[2])))

    # if allow_field_calc:
    #     calc_values = get_valid_response("Calculate values over? ('Y'/'N')\n", ['Y', 'N'])
    #     if calc_values == 'Y':
    #         print("Calculating values from field '{0}' to field '{1}'...".format(str(field_two), str(field_one)))
    #         with arcpy.da.UpdateCursor(feature_layer, [source_id_field, field_one, field_two], where_clause) as cursor:
    #             for row in cursor:
    #                 row[1] = row[2]
    #                 cursor.updateRow(row)
    #         print("Calc operation complete.")

    if calc_values_over and diff_flag:
        print("Calculating values from field '{0}' to field '{1}'...".format(str(field_two), str(field_one)))
        arcpy.CalculateField_management(feature_layer, field_one, "!{0}!".format(str(field_two)), "PYTHON_9.3")
        # with arcpy.da.UpdateCursor(feature_layer, [source_id_field, field_one, field_two], where_clause) as cursor:
        #     for row in cursor:
        #         row[1] = row[2]
        #         cursor.updateRow(row)
        print("Calc operation complete.")


# select_diff_records('capitalonegis.sde.Sites', 'Sites_FieldTest', 'did', 'excess_sq_ft', diff_type="values_from_both", only_use_joined_records=True, diff_print=True, calc_values_over=False)


def get_diff_records_as_list(feature_layer, id_field, field_one, field_two, selection_type="NEW_SELECTION"):
    """
    Function to create a list of records where the values differ between two fields
    :param data:
    :param field_one:
    :param field_two:
    :return:
    """
    # Create an empty list that will contain id values for the diff records
    diff_ids = []
    # Iterate on the feature class, adding ids to the diff_ids list as it finds differences
    with arcpy.da.SearchCursor(feature_layer, [id_field, field_one, field_two]) as cursor:
        for row in cursor:
            if row[1] != row[2]:
                diff_ids.append(str(row[0]))
    if len(diff_ids) == 0:
        print("Diff resulted in no records with a difference.")
        return diff_ids
    else:
        print("Diff IDs list complete.")
        print("{0} records in diff list.".format(len(diff_ids)))
        return diff_ids


def create_multifield_diff_report(log_file_path, feature_layer_name, joined_feature_layer_name, id_field):
    """
    Function to produce a diff log file on a field by field basis - requires a joined table for comparison!
    :param feature_layer:
    :param id_field:
    :param field_one:
    :param field_two:
    :return:
    """
    import logging
    from datetime import datetime
    # Establish logging configuration
    logging.basicConfig(filename=log_file_path, level=logging.WARNING)
    # Create list of fields to compare
    fields_list = arcpy.ListFields(feature_layer_name)
    logging.warning("\n*** Operation Started at {0}***".format(datetime.now().strftime("%H:%M:%S\n\n")))

    # Iterate on each field, performing a diff operation and logging results
    for field in fields_list:
        # Filter fields list since the returned names have the dataset designation in the field name
        print(field.name)
        if feature_layer_name in field.name:
            print("Field is part of the source table. Cleaning up field name for diff operation.")
            field_name = field.name.split('.')[-1]
            if field_name == "shape":
                print("Skipping 'Shape' field...")
                continue
            print("Performing diff on '{0}'".format(field_name))
            field_one = "{0}.{1}".format(feature_layer_name, field_name)
            field_two = "{0}.{1}".format(joined_feature_layer_name, field_name)
            joined_id_field = "{0}.{1}".format(feature_layer_name, id_field)
            field_diff_list = get_diff_records_as_list(feature_layer_name, joined_id_field, field_one, field_two)
            if len(field_diff_list) > 0:
                logging.warning("Field '{0}' had {1} discrepant records.".format(field_name, len(field_diff_list)))
            else:
                logging.info("Field '{0}' had no discrepant records.".format(field_name))
        else:
            print("field is not part of the source table. Skipping...")


# create_multifield_diff_report(r"D:\SHARED\Alberto_TransferFolder\johndiff02.log", 'capitalonegis.sde.Sites', 'Sites_FieldTest_One', 'did')


# Main driver function to perform diff operation on the two tables
def attribute_diff(source_table,
                   source_table_att_field,
                   source_table_id_field,
                   target_table,
                   target_table_att_field,
                   target_table_id_field,
                   output_log):
    """
    Performs an attribute diff operation between a source table and a target table
    :param source_table:
    :param source_table_att_field:
    :param source_table_id_field:
    :param target_table:
    :param target_table_att_field:
    :param target_table_id_field:
    :param output_log:
    :return:
    """
    print("Performing diff operation...")
    # Import needed modules
    import arcpy
    # Reset log
    general_utils.ResetLog(output_log, "INFO")
    # Call the make_attribute_dict function to transfer needed diff values to Python memory
    print("Building source dictionary...")
    # source_dict = make_attribute_dict(source_table, source_table_id_field, attr_list=[source_table_att_field])
    source_dict = make_single_attribute_dict(source_table, source_table_id_field, source_table_att_field)
    print source_dict
    # Call the make_attribute_dict function to transfer needed diff values to Python memory
    print("Building target dictionary...")
    # target_dict = make_attribute_dict(target_table, target_table_id_field, attr_list=[target_table_att_field])
    target_dict = make_single_attribute_dict(target_table, target_table_id_field, target_table_att_field)
    print target_dict
    # Run the diff operation on the dictionaries
    print("Performing dictionary diff...")
    diff = general_utils.DictDiffer(target_dict, source_dict)
    # Log diff information
    general_utils.LogMessage(output_log,
                             "{0} Total UnChanged Records: {1}".format(len(diff.unchanged()), diff.unchanged()), "INFO")
    general_utils.LogMessage(output_log, "{0} Total Changed Records: {1}".format(len(diff.changed()), diff.changed()),
                             "WARNING")
    general_utils.LogMessage(output_log, "{0} Total Added Records: {1}".format(len(diff.added()), diff.added()),
                             "WARNING")
    general_utils.LogMessage(output_log, "{0} Total Removed Records: {1}".format(len(diff.removed()), diff.removed()),
                             "WARNING")


# Main driver function to perform diff operation on the two tables
def attribute_diff_pandas(source_table,
                          source_table_att_field,
                          source_table_id_field,
                          target_table,
                          target_table_att_field,
                          target_table_id_field,
                          output_log):
    """
    Performs an attribute diff operation between a source table and a target table
    :param source_table:
    :param source_table_att_field:
    :param source_table_id_field:
    :param target_table:
    :param target_table_att_field:
    :param target_table_id_field:
    :param output_log:
    :return:
    """
    print("Performing diff operation...")
    # Import needed modules
    import arcpy
    import pandas as pd
    import numpy as np
    # Reset log
    general_utils.ResetLog(output_log, "INFO")
    # Call the make_attribute_dict function to transfer needed diff values to Python memory
    print("Building source dictionary...")
    # source_dict = make_attribute_dict(source_table, source_table_id_field, attr_list=[source_table_att_field])
    source_dict = make_single_attribute_dict(source_table, source_table_id_field, source_table_att_field)
    # Call the make_attribute_dict function to transfer needed diff values to Python memory
    print("Building target dictionary...")
    # target_dict = make_attribute_dict(target_table, target_table_id_field, attr_list=[target_table_att_field])
    target_dict = make_single_attribute_dict(target_table, target_table_id_field, target_table_att_field)

    # Convert the dicts to dataframes
    source_df = pd.DataFrame.from_dict(source_dict, orient='index')
    source_df.columns = ['Source_AttributeValue']
    source_df.sort_index(inplace=True)

    target_df = pd.DataFrame.from_dict(target_dict, orient='index')
    target_df.columns = ['Target_AttributeValue']
    target_df.sort_index(inplace=True)

    # Concatenate the two dataframes and compute attribute difference
    full_df = pd.concat([source_df, target_df], axis=1)
    full_df['Attribute_Diff'] = full_df['Source_AttributeValue'] - full_df['Target_AttributeValue']
    print full_df

    diff_df = full_df.loc[full_df['Attribute_Diff'] != 0]
    diff_df = diff_df[diff_df['Attribute_Diff'].notnull()]
    print "{0} records reported a difference in value...".format(len(diff_df))
    print diff_df

    general_utils.LogMessage(output_log, "{0} records reported a difference in value...".format(len(diff_df)), "INFO")
    general_utils.LogMessage(output_log, "\n\n*****Diff Dataframe Result: \n\n".format(len(diff_df)), "INFO")
    general_utils.LogMessage(output_log, diff_df, "INFO", timestamp=False)
    general_utils.LogMessage(output_log, "\n\n*****Full Dataframe Result: \n\n".format(len(diff_df)), "INFO")
    general_utils.LogMessage(output_log, full_df, "INFO", timestamp=False)


def create_point_fc(input_table,
                    in_x_field,
                    in_y_field,
                    workspace_gdb,
                    point_fc,
                    point_fc_name,
                    spatial_reference=arcpy.SpatialReference('WGS 1984'),
                    table_format='csv',  # Enter 'gis_table' as an alternate option
):
    """
    Converts an input table (csv or GIS) to a point feature class
    :param input_table:
    :param in_x_field:
    :param in_y_field:
    :param workspace_gdb:
    :param point_fc:
    :param point_fc_name:
    :param spatial_reference:
    :param table_format: 'csv' or 'gis_table'
    :return:
    """
    if table_format == 'csv':
        print("Converting csv to gis_table format...")
        gis_table_name = point_fc_name + "_temptable"
        if arcpy.Exists("{0}//{1}".format(workspace_gdb, gis_table_name)):
            print("\nExisting {0} GIS table exists. Replacing...".format(gis_table_name))
            try:
                arcpy.Delete_management("{0}//{1}".format(workspace_gdb, gis_table_name))
            except Exception as e:
                print e.message
        # Convert the csv to a GIS FGDB table
        input_table = arcpy.TableToTable_conversion(input_table, workspace_gdb, gis_table_name)

    print "Creating the point feature class..."
    if arcpy.Exists(input_table):
        if arcpy.Exists(point_fc):
            arcpy.Delete_management(point_fc)
        try:
            arcpy.MakeXYEventLayer_management(input_table, in_x_field, in_y_field, point_fc, spatial_reference)
            arcpy.FeatureClassToFeatureClass_conversion(point_fc, workspace_gdb, point_fc)
            print "point layer successfully created.\n"
        except Exception as e:
            print e.message
            print "An error occurred while creating the point feature class. Please check the script log.\n"

    else:
        print "The " + input_table + " table does not exist in the geodatabase. The point feature class could not be created.\n"


def CalcLatLong(fcName,
                longLatFieldNames,
                longLatFieldsDataType="DOUBLE",
                overwriteExistingFields=False,
                srObj=arcpy.SpatialReference('WGS 1984')):
    """Calculate Latitude and Longitude values for a given feature class containing points
    Credit: Sundar Venkatararaman
    :param fcName: Name of the feature class
    :type fcName: str
    :param longLatFieldNames: Longitude and Latitude field names, *in THAT order*
    :type longLatFieldNames: list
    :param longLatFieldsDataType: Data type of the longitude and latitude fields, "DOUBLE" by default
    :type longLatFieldsDataType: str
    :param overwriteExistingFields: Should the existing fields be overwritten? False by default
    :type overwriteExistingFields: bool
    :returns: None
    """
    calcLongFieldAddedInMethod = False
    calcLatFieldAddedInMethod = False
    fieldList = arcpy.ListFields(fcName)
    fieldNames = [elem.name.upper() for elem in fieldList]
    if longLatFieldNames[0].upper() in fieldNames or longLatFieldNames[1].upper() in fieldNames:
        if not overwriteExistingFields:
            raise Exception("ERROR: Attempted to overwrite an existing field in the Feature Class!!")
    if not (longLatFieldNames[0].upper() in fieldNames):
        arcpy.AddField_management(fcName, longLatFieldNames[0], field_type=longLatFieldsDataType)
        calcLongFieldAddedInMethod = True
    if not (longLatFieldNames[1].upper() in fieldNames):
        arcpy.AddField_management(fcName, longLatFieldNames[1], field_type=longLatFieldsDataType)
        calcLatFieldAddedInMethod = True
    # srObj = arcpy.Describe(fcName).spatialReference.GCS
    row = None
    try:
        with arcpy.da.UpdateCursor(fcName, ["SHAPE@XY", longLatFieldNames[0], longLatFieldNames[1]], "",
                                   srObj) as cursor:
            for row in cursor:
                if row[0][0]:
                    row[1] = row[0][0]
                if row[0][1]:
                    row[2] = row[0][1]
                cursor.updateRow(row)
    except Exception as ex:
        if calcLongFieldAddedInMethod:
            arcpy.DeleteField_management(fcName, longLatFieldNames[0])
        if calcLatFieldAddedInMethod:
            arcpy.DeleteField_management(fcName, longLatFieldNames[1])
        raise Exception("ERROR: " + str(ex))
    finally:
        del row, cursor
        # arcpy.CalculateField_management(fcName, calcFieldName, calcExpression, expression_type)


def check_for_leading_zero(input_dataset, field_name, characters_needed):
    """
    Function used to determine if block group IDs were truncated during a GIS ingest
    :param input_dataset:
    :param field_name:
    :param characters_needed:
    :return:
    """
    with arcpy.da.UpdateCursor(input_dataset, [field_name]) as cursor:
        for row in cursor:
            # arcpy.AddMessage(len(str(row[0])))
            # arcpy.AddMessage(int(characters_needed)-1)
            if len(str(row[0])) == int(characters_needed) - 1:
                arcpy.AddMessage("Appending '0' to truncated ID field value " + str(row[0]))
                value = "0" + str(row[0])
                row[0] = value
                cursor.updateRow(row)
            else:
                pass


# Function to get all the uniques in a given field


def get_subgeography_id_from_point(point_fc, point_id_field, point_id, subgeography_fc, subgeography_id_field):
    """
    Extracts the subgeography id that a point feature resides on

    :param point_fc: Point feature class containing the record to check subgeography ID
    :param point_id_field: Field in point feature class designating the point unique ID
    :param point_id: Current ID in iteration
    :param subgeography_fc: Feature class containing the subgeography coverage that the point resides on
    :param subgeography_id_field: Field in subgeography feature class containing the subgeography unique ID value
    :return: ID for the subgeography record that the point_id record resides on
    """

    arcpy.env.overwriteOutput = True

    method_message = "get_subgeography_id_from_point: "

    arcpy.AddMessage(
        "\t\t\t\t" + "get_subgeography_id_from_point: Determining ID of subgeography record containing ID " + str(
            point_id) + "...")
    # Create where_clause to select the point_id value from the point_fc
    # during the generation of a point_ly feature layer
    where_clause = arcpy.AddFieldDelimiters(point_fc, str(point_id_field)) + " = '" + str(point_id) + "'"

    # Perform verification/deletion of existing feature layer
    if arcpy.Exists("point_lyr"):
        arcpy.Delete_management("point_lyr")

    # Create 'point_ly' feature layer from point_fc to facilitate selections
    # against the dataset
    arcpy.MakeFeatureLayer_management(point_fc, "point_lyr", where_clause)

    # Perform verification that point_lyr contains one record
    count = int(arcpy.GetCount_management("point_lyr").getOutput(0))
    if count == 1:
        pass
    elif count > 1:
        arcpy.AddMessage(method_message + "WARNING: Site ID " + str(
            point_id) + " provided resulted in a selection of more than one record. Verify that the site ID field in the sites Feature Class has unique values.")
    else:
        arcpy.AddMessage(method_message + "ERROR: Site ID " + str(
            point_id) + " provided resulted in NO records from a selection in the site feature class. Verify that your sites feature class was correctly generated and that the site ID is valid.")

    # Perform verification/deletion of existing feature layer
    if arcpy.Exists("subgeography_lyr"):
        arcpy.Delete_management("subgeography_lyr")

    # Create 'subgeography_ly' feature layer from subgeography_fc to
    # facilitate selections against the dataset
    arcpy.MakeFeatureLayer_management(subgeography_fc, "subgeography_lyr")

    # Create a "selectLayerByLocation" analysis to determine the
    # subgeography record that the point resides on
    arcpy.SelectLayerByLocation_management("subgeography_lyr", "CONTAINS", "point_lyr", "", "NEW_SELECTION")

    # Read the subgeograhy_id_field value for the selected subgeography
    # record and return
    with arcpy.da.SearchCursor("subgeography_lyr", subgeography_id_field) as cursor:
        for row in cursor:
            subgeography_id = str(row[0])
    arcpy.AddMessage(method_message + "Subgeography ID is " + subgeography_id)
    return subgeography_id


def clearWSLocks(input_workspace):
    '''Attempts to clear locks on a workspace, returns stupid message.'''
    if all([arcpy.Exists(input_workspace), arcpy.Compact_management(input_workspace), arcpy.Exists(input_workspace)]):
        print 'Workspace (%s) clear to continue...' % input_workspace
        return True
    else:
        print '!!!!!!!! ERROR WITH WORKSPACE %s !!!!!!!!' % input_workspace
        return False


def get_unique_values(table, field, where_clause):
    """
    Gets unique values in a table's designated field
    :param table:
    :param field:
    :param where_clause:
    :return:
    """
    with arcpy.da.SearchCursor(table, [field], where_clause) as cursor:
        return sorted({row[0] for row in cursor})


def create_points_from_xy_table(input_matrix, in_x_field, in_y_field, output_fc):
    """
    Creates a point feature layer from a table of x/y data
    :param input_matrix:
    :param in_x_field:
    :param in_y_field:
    :param output_fc:
    :return:
    """
    spatial_reference = arcpy.SpatialReference('WGS 1984')
    arcpy.MakeXYEventLayer_management(input_matrix, in_x_field, in_y_field, output_fc, spatial_reference)
    return output_fc


def create_odcm(gdb,
                origins_fc,
                origins_id_field,
                destinations_fc,
                destinations_id_field,
                market_name,
                network_dataset,
                impedance_value,
                impedance_attribute):
    """ Origin-Destination Cost Matrix Process"""
    # Set standardized method messaging title
    method_message = "\t\t\t\t" + "create_ODCM: "

    print("\t\t\t\t" + "create_ODCM: Initializing Origin-Destination Cost Matrix process...")

    # Establish workspace parameters
    workspace = gdb
    arcpy.env.workspace = workspace
    arcpy.env.overwriteOutput = True

    # Determine which version of arcgis desktop is being used
    DesktopVersion = ArcGISVersionChecker()[2]

    print method_message + "Acquiring Network Analyst extension..."
    # Acquire Network Analyst extension
    if arcpy.CheckExtension("Network") <> "Available":
        # Raise a custom exception
        ##            raise LicenseError
        print method_message + "ERROR: A Network Analyst License is required in order to create the ODCM; the ODCM will not be produced. Please consult with the GIS Developer if a license is expected to be available..."

    elif arcpy.CheckExtension("Network") == "Available":
        arcpy.CheckOutExtension("Network")

        # Perform verification of origins and destinations feature classes
        print("\t\t\t\t" + "create_ODCM: Acquiring Origins...")
        if arcpy.Exists(origins_fc):
            pass
        else:
            arcpy.AddError("Unable to acquire Origins!")
        print("\t\t\t\t" + "create_ODCM: Acquiring Destinations...")
        if arcpy.Exists(destinations_fc):
            pass
        else:
            arcpy.AddError("Unable to acquire Destinations!")
        print("\t\t\t\t" + "create_ODCM: Acquiring Network Dataset...")
        # network_dataset = r"C:\ArcGIS\Business Analyst\US_2013\Data\Streets Data\NAVTEQ_2013_Q1_NA.gdb\Routing\Routing_ND"
        if DesktopVersion == "Desktop10.3":
            network_dataset = r"C:\ArcGIS\Business Analyst\US_2014\Data\Streets Data\NAVTEQ_2014_Q1_NA.gdb\Routing\Routing_ND"
        elif DesktopVersion == "Desktop10.2":
            network_dataset = r"C:\ArcGIS\Business Analyst\US_2013\Data\Streets Data\NAVTEQ_2013_Q1_NA.gdb\Routing\Routing_ND"
        print("\t\t\t\t" + "create_ODCM: Establishing Network Analyst Layer...")
        outNALayerName = "Origins2Destinations"
        outLayerFile = outNALayerName + ".lyr"
        print("\t\t\t\t" + "create_ODCM: The established impedence attribute is: " + str(impedance_attribute))
        # Create variable that refers to the Impedence Attribute Field from the default ODCM Table
        impedanceAttributeField = "Total_" + impedance_attribute
        print(
            "\t\t\t\t" + "create_ODCM: Establishing Destination Search Distance Cut-Off from Impedance Cut Off parameter...")
        # Import user parameter 'Impedance Cutoff'
        print("\t\t\t\t" + "create_ODCM: Impedance Cutoff: " + str(impedance_value))
        # Create the Composite Origin-Destination Cost Matrix Network Analysis Layer.
        print("\t\t\t\t" + "create_ODCM: Creating Origin-Destination Cost Matrix...")
        outNALayer = arcpy.MakeODCostMatrixLayer_na(network_dataset, outNALayerName, impedance_attribute,
                                                    impedance_value, "", "", "", "", "USE_HIERARCHY", "", "NO_LINES")
        # Acquire the result
        print("\t\t\t\t" + "create_ODCM: Acquiring Composite Network Analysis Layer...")
        outNALayer = outNALayer.getOutput(0)
        # Acquire the SubLayers from the Composite Origin-Destination Cost Matrix Network Analysis Layer
        print("\t\t\t\t" + "create_ODCM: Acquiring Composite Network Analysis SubLayers...")
        subLayerNames = arcpy.na.GetNAClassNames(outNALayer)
        # Acquire the Origin's SubLayer
        print("\t\t\t\t" + "create_ODCM: Acquiring Origins SubLayer...")
        originsLayerName = subLayerNames["Origins"]
        # Create a Field Map object to Map the 'CovLogic_Centroid' IDs to the Origins field of the Origin-Destination Cost Matrix
        originsFieldMap = arcpy.na.NAClassFieldMappings(outNALayer, originsLayerName)
        originsFieldMap["Name"].mappedFieldName = origins_id_field
        # Load the Origins into the Composite Network Analysis Layer.
        print("\t\t\t\t" + "create_ODCM: Loading Origins into Composite Network Analysis Layer...")
        arcpy.na.AddLocations(outNALayer, originsLayerName, origins_fc, originsFieldMap)
        # Acquire the Destinations SubLayer.
        print("\t\t\t\t" + "create_ODCM: Acquiring Destinations SubLayer...")
        destinationsLayerName = subLayerNames["Destinations"]
        # Create a Field Map object to map the 'proForma' DIDs to the Destinations field of the Origin-Destination Cost Matrix.
        destinationsFieldMap = arcpy.na.NAClassFieldMappings(outNALayer, destinationsLayerName)
        destinationsFieldMap["Name"].mappedFieldName = destinations_id_field
        # Load the Destinations into the Composite Network Analysis Layer.
        print("\t\t\t\t" + "create_ODCM: Loading Destinations into Composite Network Analysis Layer...")
        arcpy.na.AddLocations(outNALayer, destinationsLayerName, destinations_fc, destinationsFieldMap)
        # Solve the Network
        print("\t\t\t\t" + "create_ODCM: Solving Network 'Origins2Destinations' Origin-Destination Cost Matrix...")
        arcpy.na.Solve(outNALayer)
        # Verify if the directory, C:\Temp exists on the client system
        if not os.path.exists(r"C:\Temp"):
            # IF the directory, C:\Temp does not exist, create it
            os.makedirs(r"C:\Temp")
        # Set the Workspace to C:\Temp
        print("\t\t\t\t" + "create_ODCM: Resetting Workspace to C:\Temp...")
        arcpy.env.workspace = r"C:\Temp"
        # Extract the 'in_memory' result layer and save it as a Layer File in the workspace.
        print("\t\t\t\t" + "create_ODCM: Extracting Result Layer from memory...")
        arcpy.SaveToLayerFile_management(outNALayer, outLayerFile, "RELATIVE")
        # Establish a reference to the Result Layer
        print("\t\t\t\t" + "create_ODCM: Acquiring Result Layer...")
        ResultLayer = arcpy.mapping.Layer(r"C:\Temp\Origins2Destinations.lyr")
        # Reset the Workspace to the workspace
        print("\t\t\t\t" + "create_ODCM: Resetting Workspace to " + str(workspace) + "...")
        arcpy.env.workspace = workspace
        # Establish a reference to a standard ESRI Map Template
        print("\t\t\t\t" + "create_ODCM: Acquiring ESRI Template MXD...")
        TempMXD = arcpy.mapping.MapDocument(r"C:\Program Files (x86)\ArcGIS\\" + str(
            DesktopVersion) + "\\MapTemplates\Traditional Layouts\LetterPortrait.mxd")
        # Establish a reference to the DataFrame within the ESRI Map Template
        print("\t\t\t\t" + "create_ODCM: Acquiring ESRI Template MXD DataFrame...")
        TempDF = arcpy.mapping.ListDataFrames(TempMXD)[0]
        # Add the 'ResultLayer' to the DataFrame in the 'TempMXD'
        print("\t\t\t\t" + "create_ODCM: Adding Result Layer to ESRI Template MXD...")
        arcpy.mapping.AddLayer(TempDF, ResultLayer)
        # Create a container and dynamically populate it with the layer in the Dataframe named 'Lines'
        LinesLYR = arcpy.mapping.ListLayers(TempMXD, "Lines", TempDF)
        if len(LinesLYR) > 1:
            arcpy.AddError(
                "Multiple OD Cost Matrices populated in Template MXD. Cannot identify correct OD Cost Matrix.")
        elif len(LinesLYR) < 1:
            arcpy.AddError("OD Cost Matrix was not populated in Template MXD. Unable to extract result.")
        else:
            for lyr in LinesLYR:
                # Export the table associated with the 'Lines' layer to a new table in the Workspace
                print("\t\t\t\t" + "create_ODCM: Extracting Retail Node Sites Origin-Destination Cost Matrix...")
                arcpy.TableToTable_conversion(lyr, workspace, str(market_name) + "_ODCM")
                # Remove the layer from the TempMXD's DataFrame
                print("\t\t\t\t" + "create_ODCM: Removing Result Layer from ESRI Template MXD...")
                arcpy.mapping.RemoveLayer(TempDF, lyr)
                # Delete the 'ResultLayer' file from disk
                print("\t\t\t\t" + "create_ODCM: Deleting Result Layer from disk...")
                arcpy.Delete_management(r"C:\Temp\Origins2Destinations.lyr")
        # Establish a reference to the ProForma Sites Origin-Destination Cost Matrix
        print("\t\t\t\t" + "create_ODCM: Acquiring Origin-Destination Cost Matrix...")
        ODCM = workspace + "\\" + str(market_name) + "_ODCM"
        # Display a message to the user that the Origin-Destination Cost Matrix generation process completed
        print("\t\t\t\t" + "create_ODCM: Origin-Destination Cost Matrix data loading process complete.")

        """ [SP] Hydrate Origin-Destination Cost Matrix"""
        # Delete any unnecessary fields ('DestinationID', 'OriginID', 'DestinationRank') from the Retail Node Sites
        # Origin-Destination Cost Matrix
        print(
            "\t\t\t\t" + "create_ODCM: Performing Origin-Destination Cost Matrix preparation and preliminary calculations...")
        print(
            "\t\t\t\t" + "create_ODCM: Deleting fields 'DestinationID' | 'OriginID' | 'DestinationRank' from OD Cost Matrix...")
        arcpy.DeleteField_management(ODCM, ["DestinationID", "OriginID", "DestinationRank"])
        # Create a new field 'OriginID' in the 'ODCM' table
        print("\t\t\t\t" + "create_ODCM: Creating new field 'OriginID'...")
        arcpy.AddField_management(ODCM, "OriginID", "TEXT", "", "", 15, "Origin ID", "NULLABLE",
                                  "REQUIRED")
        # Calculate the 'OriginID' field in the 'ODCM' table, populating the field with the subgeography IDs from the
        # 'Name' field in the Table
        print("\t\t\t\t" + "create_ODCM: Calculating 'OriginID' field...")
        arcpy.CalculateField_management(ODCM, "OriginID", "!Name![:12]", "PYTHON")
        # Create a new field 'DestID' in the 'ODCM' table
        print("\t\t\t\t" + "create_ODCM: Creating new field 'DestID_TEST'...")
        arcpy.AddField_management(ODCM, "DestID", "TEXT", "", "", 20, "Destination ID",
                                  "NULLABLE", "REQUIRED")
        # Calculate the 'DestID' field in the 'ODCM' table, populating the field with the 'Retail Node' sites DID
        print("\t\t\t\t" + "create_ODCM: Calculating 'DestID' field...")
        arcpy.CalculateField_management(ODCM, "DestID", "!Name![15:]", "PYTHON")
        # Create a new field 'Dij' in the 'ODCM' table
        print("\t\t\t\t" + "create_ODCM: Creating new field 'Dij'...")
        arcpy.AddField_management(ODCM, "Dij", "DOUBLE", 15, 5, "", "Dij", "NULLABLE",
                                  "REQUIRED")
        # Calculate the 'Dij' field in the 'ODCM' table
        print("\t\t\t\t" + "create_ODCM: Calculating 'Dij' field...")
        arcpy.CalculateField_management(ODCM, "Dij", "!" + impedanceAttributeField + "!", "PYTHON")
        # Round the values held in the 'Dij' field in the 'ODCM' table to the nearest 5 significant digits
        arcpy.CalculateField_management(ODCM, "Dij", "round(!Dij!, 5)", "PYTHON")
        ##        # Delete the default impedence attribute field from the 'ODCM' table
        ##        print("Removing default impedence attribute field...")
        ##        arcpy.DeleteField_management(ODCM, str(impedanceAttributeField))

        return ODCM
        arcpy.CheckInExtension("Network")


def create_odcm_sbpipeline(gdb,
                           origins_fc,
                           origins_id_field,
                           destinations_fc,
                           destinations_id_field,
                           market_name,
                           network_dataset,
                           impedance_value,
                           impedance_attribute,
                           sites_fc,
                           sites_fc_id_field,
                           sites_fc_name_field,
                           sites_fc_micromarket_field,
                           sites_fc_format_field,
                           output_origin_field_name='origin_did',
                           output_originname_field_name='origin_name',
                           output_originformat_field_name='origin_format',
                           output_originmicromarket_field_name='origin_micromarket',
                           output_dest_field_name='destination_did',
                           output_destname_field_name='destination_name',
                           output_destformat_field_name='destination_format',
                           output_destmicromarket_field_name='destination_micromarket'):
    """ Origin-Destination Cost Matrix Process"""
    # Set standardized method messaging title
    method_message = "\t\t\t\t" + "create_ODCM: "

    print("\t\t\t\t" + "create_ODCM: Initializing Origin-Destination Cost Matrix process...")

    # Establish workspace parameters
    workspace = gdb
    arcpy.env.workspace = workspace
    arcpy.env.overwriteOutput = True
    DesktopVersion = ArcGISVersionChecker()[2]

    print method_message + "Acquiring Network Analyst extension..."
    # Acquire Network Analyst extension
    if arcpy.CheckExtension("Network") != "Available":
        # Raise a custom exception
        # #            raise LicenseError
        print method_message + "ERROR: A Network Analyst License is required in order to create the ODCM; the ODCM will not be produced. Please consult with the GIS Developer if a license is expected to be available..."

    elif arcpy.CheckExtension("Network") == "Available":
        arcpy.CheckOutExtension("Network")

        # Perform verification of origins and destinations feature classes
        print("\t\t\t\t" + "create_ODCM: Acquiring Origins...")
        if arcpy.Exists(origins_fc):
            pass
        else:
            arcpy.AddError("Unable to acquire Origins!")
        print("\t\t\t\t" + "create_ODCM: Acquiring Destinations...")
        if arcpy.Exists(destinations_fc):
            pass
        else:
            arcpy.AddError("Unable to acquire Destinations!")

        # Set reference to the network analyst layer name (to be created)
        print("\t\t\t\t" + "create_ODCM: Establishing Network Analyst Layer...")
        outNALayerName = "Origins2Destinations"
        outLayerFile = outNALayerName + ".lyr"

        print("\t\t\t\t" + "create_ODCM: The established impedance attribute is: " + str(impedance_attribute))
        # Create variable that refers to the Impedence Attribute Field from the default ODCM Table
        impedanceAttributeField = "Total_" + impedance_attribute
        print(
            "\t\t\t\t" + "create_ODCM: Establishing Destination Search Distance Cut-Off from Impedance Cut Off parameter...")
        # Import user parameter 'Impedance Cutoff'
        print("\t\t\t\t" + "create_ODCM: Impedance Cutoff: " + str(impedance_value))
        # Create the Composite Origin-Destination Cost Matrix Network Analysis Layer.
        print("\t\t\t\t" + "create_ODCM: Creating Origin-Destination Cost Matrix...")
        outNALayer = arcpy.MakeODCostMatrixLayer_na(network_dataset, outNALayerName, impedance_attribute,
                                                    impedance_value, "", "", "", "", "USE_HIERARCHY", "",
                                                    "STRAIGHT_LINES").getOutput(0)
        # # Acquire the result
        # print("\t\t\t\t" + "create_ODCM: Acquiring Composite Network Analysis Layer...")
        # outNALayer = outNALayer.getOutput(0)
        # Acquire the SubLayers from the Composite Origin-Destination Cost Matrix Network Analysis Layer
        print("\t\t\t\t" + "create_ODCM: Acquiring Composite Network Analysis SubLayers...")
        subLayerNames = arcpy.na.GetNAClassNames(outNALayer)
        # Acquire the Origin's SubLayer
        print("\t\t\t\t" + "create_ODCM: Acquiring Origins SubLayer...")
        originsLayerName = subLayerNames["Origins"]
        # Create a Field Map object to Map the 'CovLogic_Centroid' IDs to the Origins field of the Origin-Destination Cost Matrix
        originsFieldMap = arcpy.na.NAClassFieldMappings(outNALayer, originsLayerName)
        originsFieldMap["Name"].mappedFieldName = origins_id_field
        # Load the Origins into the Composite Network Analysis Layer.
        print("\t\t\t\t" + "create_ODCM: Loading Origins into Composite Network Analysis Layer...")
        arcpy.na.AddLocations(outNALayer, originsLayerName, origins_fc, originsFieldMap)
        # Acquire the Destinations SubLayer.
        print("\t\t\t\t" + "create_ODCM: Acquiring Destinations SubLayer...")
        destinationsLayerName = subLayerNames["Destinations"]
        # Create a Field Map object to map the 'proForma' DIDs to the Destinations field of the Origin-Destination Cost Matrix.
        destinationsFieldMap = arcpy.na.NAClassFieldMappings(outNALayer, destinationsLayerName)
        destinationsFieldMap["Name"].mappedFieldName = destinations_id_field
        # Load the Destinations into the Composite Network Analysis Layer.
        print("\t\t\t\t" + "create_ODCM: Loading Destinations into Composite Network Analysis Layer...")
        arcpy.na.AddLocations(outNALayer, destinationsLayerName, destinations_fc, destinationsFieldMap)
        # Solve the Network
        print("\t\t\t\t" + "create_ODCM: Solving Network 'Origins2Destinations' Origin-Destination Cost Matrix...")
        arcpy.na.Solve(outNALayer)

        # Verify if the directory, C:\Temp exists on the client system
        if not os.path.exists(r"C:\Temp"):
            # IF the directory, C:\Temp does not exist, create it
            os.makedirs(r"C:\Temp")
        # Set the Workspace to C:\Temp
        print("\t\t\t\t" + "create_ODCM: Resetting Workspace to C:\Temp...")
        arcpy.env.workspace = r"C:\Temp"

        # Extract the 'in_memory' result layer and save it as a Layer File in the workspace.
        print("\t\t\t\t" + "create_ODCM: Extracting Result Layer from memory...")
        arcpy.SaveToLayerFile_management(outNALayer, outLayerFile, "RELATIVE")

        # Establish a reference to the Result Layer
        print("\t\t\t\t" + "create_ODCM: Acquiring Result Layer...")
        ResultLayer = arcpy.mapping.Layer(r"C:\Temp\Origins2Destinations.lyr")

        # Reset the Workspace to the workspace
        print("\t\t\t\t" + "create_ODCM: Resetting Workspace to " + str(workspace) + "...")
        arcpy.env.workspace = workspace
        # Establish a reference to a standard ESRI Map Template
        print("\t\t\t\t" + "create_ODCM: Acquiring ESRI Template MXD...")
        TempMXD = arcpy.mapping.MapDocument(r"C:\Program Files (x86)\ArcGIS\\" + str(
            DesktopVersion) + "\\MapTemplates\Traditional Layouts\LetterPortrait.mxd")
        # Establish a reference to the DataFrame within the ESRI Map Template
        print("\t\t\t\t" + "create_ODCM: Acquiring ESRI Template MXD DataFrame...")
        TempDF = arcpy.mapping.ListDataFrames(TempMXD)[0]
        # Add the 'ResultLayer' to the DataFrame in the 'TempMXD'
        print("\t\t\t\t" + "create_ODCM: Adding Result Layer to ESRI Template MXD...")
        arcpy.mapping.AddLayer(TempDF, ResultLayer)
        # Create a container and dynamically populate it with the layer in the Dataframe named 'Lines'
        LinesLYR = arcpy.mapping.ListLayers(TempMXD, "Lines", TempDF)
        if len(LinesLYR) > 1:
            arcpy.AddError(
                "Multiple OD Cost Matrices populated in Template MXD. Cannot identify correct OD Cost Matrix.")
        elif len(LinesLYR) < 1:
            arcpy.AddError("OD Cost Matrix was not populated in Template MXD. Unable to extract result.")
        else:
            for lyr in LinesLYR:
                # Export the table associated with the 'Lines' layer to a new table in the Workspace
                print("\t\t\t\t" + "create_ODCM: Extracting Retail Node Sites Origin-Destination Cost Matrix...")
                # arcpy.TableToTable_conversion(lyr, workspace, str(market_name) + "_ODCM")
                ODCM = arcpy.FeatureClassToFeatureClass_conversion(lyr, workspace,
                                                                   str(market_name) + "_ODCM").getOutput(0)
                # Remove the layer from the TempMXD's DataFrame
                print("\t\t\t\t" + "create_ODCM: Removing Result Layer from ESRI Template MXD...")
                arcpy.mapping.RemoveLayer(TempDF, lyr)
                # Delete the 'ResultLayer' file from disk
                # print("\t\t\t\t" + "create_ODCM: Deleting Result Layer from disk...")
                # arcpy.Delete_management(r"C:\Temp\Origins2Destinations.lyr")
        # Establish a reference to the ProForma Sites Origin-Destination Cost Matrix
        # print("\t\t\t\t" + "create_ODCM: Acquiring Origin-Destination Cost Matrix...")
        # ODCM = workspace + "\\" + str(market_name) + "_ODCM"
        # Display a message to the user that the Origin-Destination Cost Matrix generation process completed
        print("\t\t\t\t" + "create_ODCM: Origin-Destination Cost Matrix data loading process complete.")

        """ [SP] Hydrate Origin-Destination Cost Matrix"""
        # Delete any unnecessary fields ('DestinationID', 'OriginID', 'DestinationRank') from the Retail Node Sites
        # Origin-Destination Cost Matrix
        print(
            "\t\t\t\t" + "create_ODCM: Performing Origin-Destination Cost Matrix preparation and preliminary calculations...")
        print(
            "\t\t\t\t" + "create_ODCM: Deleting fields 'DestinationID' | 'OriginID' from OD Cost Matrix...")
        arcpy.DeleteField_management(ODCM, ["DestinationID", "OriginID"])

        # Create a new fields for origin and destinations in the 'ODCM' table

        # Add id field for origins
        print("\t\t\t\t" + "create_ODCM: Creating new field '{0}'...".format(output_origin_field_name))
        arcpy.AddField_management(ODCM, output_origin_field_name, "TEXT", "", "", 20, output_origin_field_name,
                                  "NULLABLE",
                                  "REQUIRED")
        # Add name field for origins
        print("\t\t\t\t" + "create_ODCM: Creating new field '{0}'...".format(output_originname_field_name))
        arcpy.AddField_management(ODCM, output_originname_field_name, "TEXT", "", "", 100,
                                  output_originname_field_name,
                                  "NULLABLE", "REQUIRED")

        # Add format field for origins
        print("\t\t\t\t" + "create_ODCM: Creating new field '{0}'...".format(output_originformat_field_name))
        arcpy.AddField_management(ODCM, output_originformat_field_name, "TEXT", "", "", 20,
                                  output_originformat_field_name,
                                  "NULLABLE",
                                  "REQUIRED")
        # Add micromarket field for origins
        print("\t\t\t\t" + "create_ODCM: Creating new field '{0}'...".format(output_originmicromarket_field_name))
        arcpy.AddField_management(ODCM, output_originmicromarket_field_name, "TEXT", "", "", 100,
                                  output_originmicromarket_field_name,
                                  "NULLABLE",
                                  "REQUIRED")


        # Destinations fields
        # Add id field for destinations
        print("\t\t\t\t" + "create_ODCM: Creating new field '{0}'...".format(output_dest_field_name))
        arcpy.AddField_management(ODCM, output_dest_field_name, "TEXT", "", "", 20,
                                  output_dest_field_name,
                                  "NULLABLE", "REQUIRED")
        # Add name field for destinations
        print("\t\t\t\t" + "create_ODCM: Creating new field '{0}'...".format(output_destname_field_name))
        arcpy.AddField_management(ODCM, output_destname_field_name, "TEXT", "", "", 100,
                                  output_destname_field_name,
                                  "NULLABLE", "REQUIRED")

        # Add format field for origins
        print("\t\t\t\t" + "create_ODCM: Creating new field '{0}'...".format(output_destformat_field_name))
        arcpy.AddField_management(ODCM, output_destformat_field_name, "TEXT", "", "", 20, output_destformat_field_name,
                                  "NULLABLE",
                                  "REQUIRED")
        # Add micromarket field for origins
        print("\t\t\t\t" + "create_ODCM: Creating new field '{0}'...".format(output_destmicromarket_field_name))
        arcpy.AddField_management(ODCM, output_destmicromarket_field_name, "TEXT", "", "", 100,
                                  output_destmicromarket_field_name,
                                  "NULLABLE",
                                  "REQUIRED")


        # Calculate the 'OriginID' field in the 'ODCM' table, populating the field with the subgeography IDs from the
        # 'Name' field in the Table
        print("\t\t\t\t" + "create_ODCM: Calculating 'OriginID' field...")
        with arcpy.da.UpdateCursor(ODCM, ['Name', output_origin_field_name, output_dest_field_name]) as cursor:
            for row in cursor:
                string = row[0]
                origin_id = string.split(' - ')[0]
                dest_id = string.split(' - ')[1]
                row[1] = origin_id
                row[2] = dest_id
                cursor.updateRow(row)

        # Build site dictionary to bring names, micromarket, and format values to the output
        print("\t\t\t\t" + "create_ODCM: Building sites dictionary...")
        sites_dict = build_site_dict(sites_fc,
                                     sites_fc_id_field,
                                     sites_fc_name_field,
                                     sites_fc_micromarket_field,
                                     sites_fc_format_field)

        # Use the site dictionary to calc values into the needed fields
        print("\t\t\t\t" + "create_ODCM: Hydrating ODCM with sites dictionary values...")
        with arcpy.da.UpdateCursor(ODCM, [output_origin_field_name,
                                          output_originname_field_name,
                                          output_originformat_field_name,
                                          output_originmicromarket_field_name,
                                          output_dest_field_name,
                                          output_destname_field_name,
                                          output_destformat_field_name,
                                          output_destmicromarket_field_name]) as cursor:
            for row in cursor:
                # Query the sites dict using the current DID to determine needed values
                inorigindid = row[0]
                outoriginname = sites_dict[inorigindid]['name']
                outoriginformat = sites_dict[inorigindid]['format']
                outoriginmicromarket = sites_dict[inorigindid]['micromarket']

                indestdid = row[4]
                outdestname = sites_dict[indestdid]['name']
                outdestformat = sites_dict[indestdid]['format']
                outdestmicromarket = sites_dict[indestdid]['micromarket']

                # Write queried values to the row attributes
                row[1] = outoriginname if outoriginname else ""
                row[2] = outoriginformat if outoriginformat else ""
                row[3] = outoriginmicromarket if outoriginmicromarket else ""

                row[5] = outdestname if outdestname else ""
                row[6] = outdestformat if outdestformat else ""
                row[7] = outdestmicromarket if outdestmicromarket else ""

                cursor.updateRow(row)

        # Perform final corrections for destination rank
        with arcpy.da.UpdateCursor(ODCM, ['DestinationRank', impedanceAttributeField]) as cursor:
            for row in cursor:
                if row[1] == 0:
                    cursor.deleteRow()
                else:
                    row[0] -= 1
                    cursor.updateRow(row)

        # arcpy.TableToTable_conversion(odcm_lyr, workspace, str(market_name)+"_ODCM")
        return ODCM
        arcpy.CheckInExtension("Network")


def convert_runtime_gdbs_in_folder(folder_path):
    """
    Converts runtime geodatabase files in a specified folder to file geodatabases
    :param folder_path:
    :return:
    """

    runtime_gdbs = []

    for (root, dirs, files) in os.walk(folder_path):
        for file_name in files:
            # Find only files that have the .mxd extension
            if os.path.splitext(file_name)[1] == ".geodatabase":
                file_path = root + "\\" + file_name
                print file_path
                runtime_gdbs.append(file_path)

    print runtime_gdbs

    output_counter = 1

    for rgdb in runtime_gdbs:
        print("\nin_file: {0}".format(rgdb))
        print("out_file: {0}".format(folder_path + "\\converted_{0}.gdb".format(str(output_counter))))

        arcpy.CopyRuntimeGdbToFileGdb_conversion(rgdb, folder_path + "\\converted_{0}.gdb".format(str(output_counter)))
        output_counter += 1


def getDatabaseItemCount(workspace):
    arcpy.env.workspace = workspace
    feature_classes = []
    for dirpath, dirnames, filenames in arcpy.da.Walk(workspace, datatype="Any", type="Any"):
        for filename in filenames:
            feature_classes.append(os.path.join(dirpath, filename))
    return feature_classes, len(feature_classes)


def replicateEnterpriseGDB(dbConnection, targetGDB):
    """
    Function that replicates the contents of an enterprise geodatabase in a local file geodatabase
    :param dbConnection: Full path to enterprise geodatabase connection file
    :param targetGDB: Full path to the target file geodatabase
    :return: None
    """
    print("Checking for python executable to determine if an EGDB connection can be made...")
    if not general_utils.check_for_arcgis_python():
        print("ArcGIS' python needed in order to use the egdb as the dataset source. Exiting...")
        validation = False
    else:
        validation = True

        startTime = time.time()

        featSDE, cntSDE = getDatabaseItemCount(dbConnection)
        featGDB, cntGDB = getDatabaseItemCount(targetGDB)

        now = datetime.now()
        logName = now.strftime("SDE_REPLICATE_SCRIPT_%Y-%m-%d_%H-%M-%S.log")
        log.basicConfig(datefmt='%m/%d/%Y %I:%M:%S %p', format='%(asctime)s %(message)s', \
                        filename=logName, level=log.INFO)

        print "Old Target Geodatabase: %s -- Feature Count: %s" % (targetGDB, cntGDB)
        log.info("Old Target Geodatabase: %s -- Feature Count: %s" % (targetGDB, cntGDB))
        print "Geodatabase being copied: %s -- Feature Count: %s" % (dbConnection, cntSDE)
        log.info("Geodatabase being copied: %s -- Feature Count: %s" % (dbConnection, cntSDE))

        arcpy.env.workspace = dbConnection

        #deletes old targetGDB
        try:
            shutil.rmtree(targetGDB)
            print "Deleted Old %s" % (os.path.split(targetGDB)[-1])
            log.info("Deleted Old %s" % (os.path.split(targetGDB)[-1]))
        except Exception as e:
            print e
            log.info(e)

        #creates a new targetGDB
        GDB_Path, GDB_Name = os.path.split(targetGDB)
        print "Now Creating New %s" % (GDB_Name)
        log.info("Now Creating New %s" % (GDB_Name))
        arcpy.CreateFileGDB_management(GDB_Path, GDB_Name)

        datasetList = [arcpy.Describe(a).name for a in arcpy.ListDatasets()]
        featureClasses = [arcpy.Describe(a).name for a in arcpy.ListFeatureClasses()]
        tables = [arcpy.Describe(a).name for a in arcpy.ListTables()]

        #Compiles a list of the previous three lists to iterate over
        allDbData = datasetList + featureClasses + tables

        for sourcePath in allDbData:
            targetName = sourcePath.split('.')[-1]
            targetPath = os.path.join(targetGDB, targetName)
            if arcpy.Exists(targetPath) == False:
                try:
                    print "Atempting to Copy %s to %s" % (targetName, targetPath)
                    log.info("Atempting to Copy %s to %s" % (targetName, targetPath))
                    arcpy.Copy_management(sourcePath, targetPath)
                    print "Finished copying %s to %s" % (targetName, targetPath)
                    log.info("Finished copying %s to %s" % (targetName, targetPath))
                except Exception as e:
                    print "Unable to copy %s to %s" % (targetName, targetPath)
                    print e
                    log.info("Unable to copy %s to %s" % (targetName, targetPath))
                    log.info(e)
            else:
                print "%s already exists....skipping....." % (targetName)
                log.info("%s already exists....skipping....." % (targetName))
        featGDB, cntGDB = getDatabaseItemCount(targetGDB)
        print "Completed replication of %s -- Feature Count: %s" % (dbConnection, cntGDB)
        log.info("Completed replication of %s -- Feature Count: %s" % (dbConnection, cntGDB))
        totalTime = (time.time() - startTime)
        totalTime = general_utils.formatTime(totalTime)
        log.info("Script Run Time: %s" % (totalTime))


def get_fc_name_from_full_path(fc_path):
    return fc_path.split("\\")[-1]


def get_unique_vals_in_fc_field(fc, field):
    """
    Return a set of values from a specified feature class field
    :param fc:
    :param field:
    :return:
    """
    unique_vals = set(row[0] for row in arcpy.da.SearchCursor(fc, [field]))
    return unique_vals


# Method used to retrieve the lower value from a comparison of two fields and write the value to a third field
def return_lower_value(dataset, fieldA, fieldB, fieldC):
    fields = [fieldA, fieldB, fieldC]
    with arcpy.da.UpdateCursor(dataset, fields) as cursor:
        for row in cursor:
            fieldA_val = row[0]
            fieldB_val = row[1]
            # Determine which value is lower between Huff Model and Distance Decay
            if fieldA_val < fieldB_val:
                row[2] = fieldA_val
                # arcpy.AddMessage("Comparative analysis result: "+str(fieldA)+" value was lower than "+str(fieldB)+" value; the "+str(fieldA)+" demand share value will be selected.")
            elif fieldB_val < fieldA_val:
                row[2] = fieldB_val
                # arcpy.AddMessage("Comparative analysis result: "+str(fieldB)+" value was lower than "+str(fieldA)+" value; the "+str(fieldB)+" demand share value will be selected.")
            elif fieldA_val == fieldB_val:
                row[2] = fieldA_val
                # arcpy.AddMessage("Comparative analysis result: "+str(fieldA)+" and "+str(fieldB)+" values were equal and selected.")
            else:
                print("ERROR during comparative analysis process. Please contact the GIS developer for assistance.")
            cursor.updateRow(row)


    # def copy_featureclass(fc, target_location):
    #
    #     # Create description variables for source feature class
    #     source_desc = arcpy.Describe(fc)
    #     source_name = source_desc.name
    #     print("Source variables set...\n")
    #     print("\nFC name: {0}".format(source_name))
    #
    #     # Create description variables for target location
    #     target_desc = arcpy.Describe(target_location)
    #     gdb = target_desc.path
    #     # If the target location is a feature dataset, get the spatial reference
    #     if target_desc
    #     sr = target_desc.spatialReference
    #     print("Target location variables set...\n")
    #     print("\n")
    #
    #     arcpy.CreateFeatureDataset_management(gdb, source_name, sr)