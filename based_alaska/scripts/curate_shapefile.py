"""
Shapefiles representing geographic objects like faults are sometimes much
larger than then region we are mapping, which really slows down mapmaking.
This function takes Shapefiles (in WGS84) and kicks out any objects/lines that
don't fit within a User-defined bounding box
"""
import geopandas as gpd


# User-defined parameters
lon_min = -168.
lon_max = -140.
lat_min = 64.5
lat_max = 72.

# fid = ("dggs_quaternary_faults/mp150_converted/shapefiles/"
#        "mp150-pflaker-1994-converted.shp")
# fid = "/Users/chow/Work/data/dggs_quaternary_faults/mp141/shapefiles/mp141-qflt-line-alaska.shp"
fid = "/Users/chow/Work/data/mapping/ak_dot_roads/Routes.shp"
fid_out = "/Users/chow/Work/data/mapping/ak_dot_roads/nak_roads.shp"

# Start curation
gdf = gpd.read_file(fid)
drop = []
for idx in range(len(gdf)):
    try:
        lons, lats = gdf.iloc[idx].geometry.xy
    except NotImplementedError:
        drop.append(idx)
        continue
    for lon, lat in zip(lons, lats):
        if (lon >= lon_min and lon <= lon_max) and \
                (lat >= lat_min and lat <= lat_max):
            break 
    else:
        drop.append(idx)

print(f"{len(gdf)} dropping {len(drop)} rows")
gdf.drop(index=drop, inplace=True)
gdf.to_file(fid_out)



