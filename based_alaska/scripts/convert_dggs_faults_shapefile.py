"""
Alaska DGGS provides Alaska faults and folds in a digitized database, but
the pre-quaternary faults of Pflaker 1994 are provided in Albers Conical Equal
Area projection. This script will convert that file into WGS84 (lat/lon) so that
these can be plotted on a basemap

Reference Links:
    1) https://dggs.alaska.gov/pubs/id/23944
    2) https://dggs.alaska.gov/webpubs/metadata/MP150.faq.html
    3) https://dggs.alaska.gov/webpubs/data/mp141_quaternary-faults-folds.zip
    4) https://geoportal.dggs.dnr.alaska.gov/portal/apps/webappviewer/index.html\
            ?id=48d909b8b2f34e3b9fa12040a97f6e45
    5) https://gis.stackexchange.com/questions/307620/\
        projection-conversion-with-python-pyproj-canada-albers-equal-area-to-wgs
    6) https://www.spatialreference.org/ref/epsg/3338/proj4/
    7) https://shapely.readthedocs.io/en/stable/reference/shapely.LineString.html

Deprecated Proj String for AEA projection (see link 6):
    +proj=aea +lat_1=55 +lat_2=65 +lat_0=50 +lon_0=-154 +x_0=0 +y_0=0 \
    +datum=NAD83 +units=m +no_defs
"""
import os
import geopandas as gpd
import pyproj
import shapely

# Use Geopandas to read in the Shapefile. This input directory structure
# follows the exact structure from the .zip file in Ref. link 3
fid = ("dggs_quaternary_faults/mp150/shapefiles/"
       "mp150-prequaternary-faults-pflaker-1994.shp")
gdf = gpd.read_file(fid)

# Transform for projection: AEA-NAD83-AK -> WGS84
transformer = pyproj.Transformer.from_crs("EPSG:3338", "EPSG:4326")

# Loop through the DataFrame and convert coordinates one at a time
converted = []
for idx in range(len(gdf)):
    # Transform coordinates
    x, y = gdf.iloc[idx].geometry.xy
    x_conv, y_conv = transformer.transform(x, y)
    # Place converted coordinates in the correct input format
    coordinates = []
    for xc, yc in zip(x_conv, y_conv):
        coordinates.append([yc, xc])  # note lon,lat
    # Generate a Shapely LineString to hold coordinates
    lstr = shapely.LineString(coordinates)
    converted.append(lstr)

# Replaces converted series in the original DataFrame 
geometry_converted = gpd.GeoSeries(converted)
gdf.set_geometry(col=geometry_converted, inplace=True)

# Finally, write to a new ShapeFile
path_out = "dggs_quaternary_faults/mp150_converted/shapefiles"
if not os.path.exists(path_out):
    os.makedirs(path_out)
gdf.to_file(os.path.join(path_out, "mp150-pflaker-1994-converted.shp"))

