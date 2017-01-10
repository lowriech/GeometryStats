# GeometryStats
This QGIS plugin takes an input line layer, and outputs descriptive statistics on the quality of its geometry.  This includes
1) a point shapefile of all the angles in the layer of interest
2) a histogram showing the distribution of angles in the layer of interest
3) a document showing the average angle, various percentiles, and counting the 0, 90, and 180 degree angles

This repository also includes the initial code to run descriptive statistics on the edge lengths, although it is not currently implemented (1/9/2017).  

Inputs should be converted first to a line layer if they are polygon, and reprojected to a meter CRS (although this is not entirely necessary for small areas).

DEPENDENCIES:
-- pandas
-- tabulate
