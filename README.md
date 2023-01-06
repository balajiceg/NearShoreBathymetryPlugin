Please send me an email at balaji.9th@gmail.com if you run into issues.
# Plugin for estimating Bathymetry using Multisepectral Satellite Data
This plugin is used to estimate the near shore bathymetry.It uses the Log Ratio Transformation method. This tool uses a bottom albedo-independent Bathymetry algorithm developed by Stumpf and Holderied (2003). The bottom albedo-independent nature of the algorithm means that sea floor covered with dark sea grass or bright sand is shown to be at the same depth when they are at the same depth.This bathymetry is resonable only between depths of 2 to 20m. This tool is similar to the Relative Water Depth tool in ENVI.

Data required for the tool are:
* Blue Band,Green Band -for computing the relative depths.
* OPTIONAL: Red band, NIR band, SWIR band - for creating mask to extract water body.
* Ground truth Shape file: a shape file with point features containing the actual depth information. 
* MetaDataFile(MLT) OPTIONAL: for converting DN value to TOA.

(A sample dataset is provided within the plugin repository. Please note that in the actual depth data in the ground truth is just for sample and are not the orginal values.)
