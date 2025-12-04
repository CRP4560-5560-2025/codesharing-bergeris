# Python version 3.9.18 utf-8
# Toolbox that converts GeoJSON to a feature class, joins CSV, offers display options, and plots with matplotlib.
# Created by Ian Berger for CRP 4560/5560 taught by Dr. Brian Gelder
# 2025-12-01

import arcpy
import os
import sys
import traceback
from collections import Counter

# Import matplotlib here so failures are reported in execute() rather than at import time for ArcGIS environments
try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name appears in ArcGIS)."""
        self.label = "GeoJSON CSV Join & Plot Toolbox"
        self.alias = "geo_csv_join"
        self.tools = [GeoCSVJoinTool]

class GeoCSVJoinTool(object):
    def __init__(self):
        self.label = "GeoJSON -> FeatureClass + CSV Join + Plot"
        self.description = ("Converts a GeoJSON to a feature class, joins a CSV on a user-specified attribute, "
                            "applies a simple display choice (Pro), and makes a basic matplotlib plot saved to PNG.")
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = []

        # 0: GeoJSON input file
        p0 = arcpy.Parameter(
            displayName="Input GeoJSON file",
            name="in_geojson",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        p0.filter.list = ["geojson", "json"]
        params.append(p0)

        # 1: CSV input file
        p1 = arcpy.Parameter(
            displayName="Input CSV file",
            name="in_csv",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        p1.filter.list = ["csv"]
        params.append(p1)

        # 2: Output workspace / where to save files (folder or geodatabase)
        p2 = arcpy.Parameter(
            displayName="Output workspace (folder or file geodatabase)",
            name="out_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        params.append(p2)

        # 3: Name for output feature class (user can type)
        p3 = arcpy.Parameter(
            displayName="Output feature class name",
            name="out_fc_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        p3.value = "geojson_fc"
        params.append(p3)

        # 4: Join field name (the attribute that exists in both feature class & CSV)
        p4 = arcpy.Parameter(
            displayName="Join field name (same in CSV and feature class)",
            name="join_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        p4.value = ""
        params.append(p4)

        # 5: Display options (drop-down)
        p5 = arcpy.Parameter(
            displayName="Display option (symbology)",
            name="display_option",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        p5.filter.type = "ValueList"
        p5.filter.list = ["Single Symbol", "Unique Values", "Graduated Colors"]
        p5.value = "Single Symbol"
        params.append(p5)

        # 6: Graph save path (PNG)
        p6 = arcpy.Parameter(
            displayName="Save graph as (PNG file)",
            name="out_graph_png",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")
        p6.filter.list = ["png"]
        params.append(p6)

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        # Called when a parameter changes. We can suggest default output filename based on geojson name.
        try:
            if parameters[0].value and (not parameters[3].altered):
                geojson_path = parameters[0].value
                base = os.path.splitext(os.path.basename(geojson_path))[0]
                parameters[3].value = base + "_fc"
        except Exception:
            pass
        return

    def updateMessages(self, parameters):
        # Basic validation: ensure join_field is provided
        if parameters[4].value is None or str(parameters[4].value).strip() == "":
            parameters[4].setErrorMessage("Please enter the attribute/field name used for joining (exists in both CSV and GeoJSON attributes).")

    def execute(self, parameters, messages):
        try:
            in_geojson = parameters[0].valueAsText
            in_csv = parameters[1].valueAsText
            out_workspace = parameters[2].valueAsText
            out_fc_name = parameters[3].valueAsText
            join_field = parameters[4].valueAsText
            display_choice = parameters[5].valueAsText
            out_png = parameters[6].valueAsText

            messages.addMessage("Parameters received:")
            messages.addMessage(" GeoJSON: {}".format(in_geojson))
            messages.addMessage(" CSV: {}".format(in_csv))
            messages.addMessage(" Output workspace: {}".format(out_workspace))
            messages.addMessage(" Output feature class name: {}".format(out_fc_name))
            messages.addMessage(" Join field: {}".format(join_field))
            messages.addMessage(" Display choice: {}".format(display_choice))
            messages.addMessage(" Output PNG: {}".format(out_png))

            # Validate outputs
            if not os.path.exists(in_geojson):
                raise arcpy.ExecuteError("Input GeoJSON does not exist: {}".format(in_geojson))
            if not os.path.exists(in_csv):
                raise arcpy.ExecuteError("Input CSV does not exist: {}".format(in_csv))

            # Create output path for feature class
            # If workspace is a folder, create a file geodatabase? We'll support both folder and FGDB.
            # Determine if workspace is a file geodatabase
            is_fgdb = out_workspace.endswith(".gdb")
            if is_fgdb:
                out_fc = os.path.join(out_workspace, out_fc_name)
            else:
                # use folder: create a new file geodatabase to store the FC (recommended)
                # create a small FGDB named outputs.gdb inside the folder (if not exists)
                gdb_path = os.path.join(out_workspace, "geojson_out.gdb")
                if not arcpy.Exists(gdb_path):
                    messages.addMessage("Creating file geodatabase: {}".format(gdb_path))
                    arcpy.management.CreateFileGDB(out_workspace, "geojson_out.gdb")
                out_fc = os.path.join(gdb_path, out_fc_name)

            messages.addMessage("Converting GeoJSON to feature class...")
            # Use JSON To Features tool (ArcGIS)
            # arcpy.JSONToFeatures_conversion(in_json_file, out_feature_class)
            arcpy.JSONToFeatures_conversion(in_geojson, out_fc)
            messages.addMessage("Created feature class: {}".format(out_fc))

            # Add CSV to geodatabase as table (copy)
            csv_table_name = os.path.splitext(os.path.basename(in_csv))[0]
            csv_table_out = os.path.join(os.path.dirname(out_fc), csv_table_name)
            messages.addMessage("Copying CSV to geodatabase as table: {}".format(csv_table_out))
            arcpy.management.CopyRows(in_csv, csv_table_out)

            # Confirm join field exists in both
            fields_fc = [f.name for f in arcpy.ListFields(out_fc)]
            fields_csv = [f.name for f in arcpy.ListFields(csv_table_out)]
            if join_field not in fields_fc:
                messages.addWarningMessage("Join field '{}' not found in feature class fields: {}".format(join_field, ", ".join(fields_fc[:10])))
            if join_field not in fields_csv:
                messages.addWarningMessage("Join field '{}' not found in CSV table fields: {}".format(join_field, ", ".join(fields_csv[:10])))

            # Perform join using JoinField (permanent join of attributes)
            messages.addMessage("Joining CSV attributes to feature class (JoinField)...")
            # JoinField (in_table, in_field, join_table, join_field, {fields})
            # We'll join all non-shape fields from CSV (except join_field duplicate)
            csv_field_names = [f for f in fields_csv if f != join_field and f.lower() != 'objectid']
            if len(csv_field_names) == 0:
                messages.addMessage("No CSV fields (other than join field) found to join.")
            arcpy.management.JoinField(out_fc, join_field, csv_table_out, join_field, csv_field_names)
            messages.addMessage("Join complete.")

            # Add layer to current project map (ArcGIS Pro) if possible and try to apply symbology
            sym_applied = False
            try:
                aprx = arcpy.mp.ArcGISProject("CURRENT")
                m = aprx.activeMap
                if m is None:
                    messages.addWarningMessage("Could not find active map in CURRENT project to add layer/symbology.")
                else:
                    # Add the feature class as a layer
                    layer_name = out_fc_name
                    # Create temporary layer file path
                    temp_layer = os.path.join(arcpy.env.scratchGDB if arcpy.env.scratchGDB else arcpy.env.scratchFolder or out_workspace, layer_name + "_temp.lyrx")
                    # Make a layer in memory and save to layer file
                    arcpy.management.MakeFeatureLayer(out_fc, layer_name)
                    # Save to layer file in scratch (if possible)
                    try:
                        arcpy.management.SaveToLayerFile(layer_name, temp_layer, "RELATIVE")
                    except Exception:
                        # fallback: create layer file in out_workspace if allowed
                        temp_layer = os.path.join(out_workspace, layer_name + "_temp.lyrx")
                        try:
                            arcpy.management.SaveToLayerFile(layer_name, temp_layer, "RELATIVE")
                        except Exception:
                            temp_layer = None

                    # If we have a layer file, use arcpy.mp to add it
                    if temp_layer and os.path.exists(temp_layer):
                        ly = arcpy.mp.LayerFile(temp_layer)
                        m.addLayer(ly)
                    else:
                        # Fall back to adding by path (ArcGIS Pro will create a layer)
                        m.addDataFromPath(out_fc)

                    # Attempt to set symbology using ArcGIS Pro API
                    # find the newly added layer (match by name)
                    candidate_layers = [l for l in m.listLayers() if l.name == os.path.basename(out_fc_name) or l.name == layer_name]
                    if len(candidate_layers) == 0:
                        # try last layer
                        candidate_layers = m.listLayers()
                    target_layer = candidate_layers[-1] if candidate_layers else None
                    if target_layer is not None:
                        messages.addMessage("Attempting to set symbology in the active map (ArcGIS Pro)...")
                        try:
                            sym = target_layer.symbology
                            # Choose renderer by user's selection
                            if display_choice == "Single Symbol":
                                sym.updateRenderer("SimpleRenderer")
                                # nothing else needed
                            elif display_choice == "Unique Values":
                                # ensure join_field exists in symbology fields
                                sym.updateRenderer("UniqueValueRenderer")
                                # unique value renderer expects a list for fields
                                try:
                                    sym.renderer.fields = [join_field]
                                except Exception:
                                    pass
                            elif display_choice == "Graduated Colors":
                                sym.updateRenderer("GraduatedColorsRenderer")
                                try:
                                    sym.renderer.classificationField = join_field
                                except Exception:
                                    pass
                            # assign back
                            target_layer.symbology = sym
                            sym_applied = True
                            messages.addMessage("Symbology applied (attempt). If you don't see changes, check that ArcGIS Pro supports symbology for this field type.")
                            # save the project to keep layer changes? Do not force save; leave to user.
                        except Exception as e:
                            messages.addWarningMessage("Could not apply symbology automatically: {}".format(str(e)))
                    else:
                        messages.addWarningMessage("Could not find the newly added layer in the active map to apply symbology.")
            except Exception as e:
                messages.addWarningMessage("Symbology step was skipped or failed (likely not ArcGIS Pro / CURRENT project unavailable). Detail: {}".format(str(e)))

            # Prepare data for plotting using arcpy.da.SearchCursor
            messages.addMessage("Preparing data for plotting from joined feature class...")
            # Try to determine whether join_field is numeric or categorical by inspecting field type
            field_obj = None
            for f in arcpy.ListFields(out_fc):
                if f.name == join_field:
                    field_obj = f
                    break

            values = []
            # We'll try to extract fields (joined fields) for plotting; choose a numeric field if available
            # Strategy: if join_field is numeric -> create histogram of that field; else find the first numeric field from CSV join to plot its distribution
            numeric_field = None
            if field_obj and field_obj.type in ("Integer", "SmallInteger", "Single", "Double", "OID"):
                numeric_field = join_field
            else:
                # look for any numeric field in FC that came from CSV
                for f in arcpy.ListFields(out_fc):
                    if f.type in ("Integer", "SmallInteger", "Single", "Double") and f.name != join_field:
                        numeric_field = f.name
                        break

            # If numeric_field found, gather numeric values; otherwise gather categorical counts for join_field
            if numeric_field:
                messages.addMessage("Numeric field for plotting: {}".format(numeric_field))
                cursor_field = numeric_field
                with arcpy.da.SearchCursor(out_fc, [cursor_field]) as cursor:
                    for row in cursor:
                        try:
                            val = row[0]
                            if val is not None:
                                values.append(float(val))
                        except Exception:
                            pass
                # Plot numeric distribution (histogram)
                if plt is None:
                    messages.addWarningMessage("matplotlib not available in this environment. Plot will not be created.")
                else:
                    plt.figure()
                    plt.hist(values, bins=20)
                    plt.title("Distribution of {}".format(cursor_field))
                    plt.xlabel(cursor_field)
                    plt.ylabel("Frequency")
                    plt.tight_layout()
                    plt.savefig(out_png)
                    plt.close()
                    messages.addMessage("Saved histogram to: {}".format(out_png))
            else:
                # categorical plotting on join_field
                cursor_field = join_field
                counts = Counter()
                with arcpy.da.SearchCursor(out_fc, [cursor_field]) as cursor:
                    for row in cursor:
                        k = row[0]
                        counts[k] += 1
                items = [(str(k) if k is not None else "None", v) for k, v in counts.items()]
                # Sort descending
                items.sort(key=lambda x: x[1], reverse=True)
                labels = [i[0] for i in items][:30]  # limit to top 30 categories
                freqs = [i[1] for i in items][:30]

                if plt is None:
                    messages.addWarningMessage("matplotlib not available in this environment. Plot will not be created.")
                else:
                    plt.figure(figsize=(10, 6))
                    plt.bar(range(len(labels)), freqs)
                    plt.xticks(range(len(labels)), labels, rotation=45, ha='right')
                    plt.title("Counts by {}".format(cursor_field))
                    plt.xlabel(cursor_field)
                    plt.ylabel("Count")
                    plt.tight_layout()
                    plt.savefig(out_png)
                    plt.close()
                    messages.addMessage("Saved bar chart to: {}".format(out_png))

            messages.addMessage("Tool finished. Check messages for any warnings about symbology or plotting.")
            return

        except arcpy.ExecuteError:
            msgs = arcpy.GetMessages(2)
            arcpy.AddError(msgs)
            raise
        except Exception as ex:
            tb = traceback.format_exc()
            arcpy.AddError(str(ex))
            arcpy.AddError(tb)
            raise

