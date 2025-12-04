Project: Code Sharing assignment
Author: Ian Berger
Date Created: December 2, 2025



Purpose of the Code

This project provides a custom ArcGIS Python Toolbox (.pyt) that allows users to:

Select a GeoJSON file and convert it to a feature class.

Select a CSV file containing attributes to join to the feature class.

Specify a workspace for saving all outputs.

Provide an attribute field name shared by both datasets for performing a join.

Choose a display (symbology) option for how the data should appear in ArcGIS Pro.

Automatically add the resulting feature class to the current ArcGIS Pro map.

Generate a basic matplotlib plot based on the joined attribute data.

Save the plot as a PNG file at a user-specified location.

The toolbox streamlines spatial + tabular integration workflows and adds quick visualization capabilities.



Data Accessed

This toolbox works with user-supplied data.

The user must supply GeoJSON Input and a CSV Input

CSV files containing tabular attributes that can be joined to the GeoJSON feature class. Examples include:

U.S. Census Data (ACS) such as:

B01001 – Sex by Age

B19013 – Median Household Income

B02001 – Race

B25077 – Median Home Value

Or in this case

T01001 - Total population | filtered for other black or African American alone, not specified.

The toolbox does not directly fetch tables; the user must supply the CSV file.



How to Run the Code Package
Requirements:

ArcGIS Pro 

A Python environment with:

arcpy

matplotlib

Your CSV and GeoJSON files.



Steps:

Place the toolbox file (GeoCSVJoinToolbox.pyt) in your project folder.

Open ArcGIS Pro and load your project.

In the Catalog pane, right-click Toolboxes → Add Toolbox, then select the .pyt file.

Open the tool:
GeoJSON → FeatureClass + CSV Join + Plot

Provide the required inputs:

Choose your GeoJSON file.

Choose your CSV file.

Pick an output workspace (folder or file geodatabase).

Enter an output feature class name.

Enter the join field used in both datasets.

Select a symbology display option.

Specify a PNG save location for the plot.

Run the tool.



After completion:

The feature class appears in your output workspace.

A joined, symbolized layer is added to your ArcGIS Pro map (if using Pro).

A PNG plot is saved in the location you selected.