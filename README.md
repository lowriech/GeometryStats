# GeometryStats
This QGIS plugin takes an input line layer, and outputs descriptive statistics on the quality of its geometry.  This includes:

Two shapefiles:
a point shapefile of all the angles, and a line shapefile of all the edges

Two histograms:
showing the distribution of angles and edge lengths

Two stats documents:
showing percentile values, averages, and other descriptive statistics


Inputs should be converted first to a line layer if they are polygon.  Additionally, if you want the edge output to have meaningful units then the data should be reprojected to a meter CRS.  This won't really affect the shape of the histogram, but will make comparisons between data sets less meaningful.  

DEPENDENCIES:
You will need to install pandas, a Data Science library, to use this tool.  In terminal, paste the following:
  sudo pip install pandas

