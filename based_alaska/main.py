"""
Based Alaska - A PyGMT-based base mapping tool for geophysical studies in Alaska

Basic usage: 
    $ python main.py {CFG} 
    where CFG is name of any available config file within the configs/ directory
    without file extension. For example to plot the default figure, run:
    $ python main.py default
"""
import os
import sys
import numpy as np
import pygmt
import geopandas as gpd

from utils.read import (read_yaml, read_stations, read_list, read_earthquakes,
                        read_pb_plate_boundaries)


class BasedAlaska:
    """
    A class to control plotting functionalities and store config parameters.
    """
    def __init__(self, fid=None):
        """
        Must have a config file to initiate the based'ness

        :type fid: str
        :param fid: config file name
        """
        self.f = pygmt.Figure()
        
        if fid is None:
            fid = sys.argv[1]

        # Load in the base parameters from the master config file
        self.cfg = read_yaml(fid)

    def check(self):
        """
        Parameter check function, just makes sure that the parameter file is set
        up correctly so that the plotting functions, which are frankly not very
        smart, won't break unexpectedly.
        """
        # Check that file and format lists match

        # 

    def setup(self):
        """
        Setup the plot, which usually means frame, coastline or topography
        """
        print("setting up basemap")
        # Earth Relief (Topography) with a coastline outline
        if self.cfg.FLAGS.earth_relief:
            grid = pygmt.datasets.load_earth_relief(
                resolution=self.cfg.BASEMAP.earth_relief.resolution,
                region=self.cfg.BASEMAP.region
            )
            self.f.grdimage(grid=grid, projection=self.cfg.BASEMAP.projection,
                            cmap=self.cfg.BASEMAP.earth_relief.cmap
                            )
            self.f.coast(projection=self.cfg.BASEMAP.projection,
                         region=self.cfg.BASEMAP.region,
                         shorelines=self.cfg.PENS.shorelines,
                         frame=self.cfg.BASEMAP.frame,
                         resolution=self.cfg.BASEMAP.resolution,
                         area_thresh=self.cfg.BASEMAP.area_thresh,
                         borders=self.cfg.BASEMAP.borders,
                         **self.cfg.BASEMAP.kwargs
                         )
        # OR Just a coastline with solid color water and land
        else:
            self.f.coast(projection=self.cfg.BASEMAP.projection,
                         region=self.cfg.BASEMAP.region,
                         shorelines=self.cfg.PENS.shorelines,
                         frame=self.cfg.BASEMAP.frame,
                         land=self.cfg.COLORS.land,
                         water=self.cfg.COLORS.water,
                         lakes=self.cfg.COLORS.lakes,
                         area_thresh=self.cfg.BASEMAP.area_thresh,
                         resolution=self.cfg.BASEMAP.resolution,
                         **self.cfg.BASEMAP.kwargs
                         )
        # Map scale-bar
        if self.cfg.FLAGS.scale_bar:
            with pygmt.config(MAP_TICK_PEN_PRIMARY=self.cfg.PENS.scalebar):
                self.f.basemap(region=self.cfg.BASEMAP.region,
                               projection=self.cfg.BASEMAP.projection,
                               map_scale=self.cfg.BASEMAP.map_scale
                               )

    def inset(self):
        """
        Create a map inset to show a larger domain somewhere near the zoomed in
        version of this map
        """
        if self.cfg.FLAGS.map_inset:
            with self.f.inset(position=self.cfg.INSET.position,
                              margin=self.cfg.INSET.margin):
                # Draw a normal map on the inset map
                self.f.coast(projection=self.cfg.INSET.projection, 
                             region=self.cfg.INSET.region, 
                             frame=self.cfg.INSET.frame,
                             land=self.cfg.COLORS.inset_land,
                             water=self.cfg.COLORS.inset_water,
                             shorelines=self.cfg.PENS.inset_shorelines,
                             area_thresh=self.cfg.INSET.area_thresh
                             )
                # Plot a rectangle ("r") in the inset map to show the area of 
                # the main figure. "+s" means that the first two columns are the 
                # longitude and latitude of the bottom left corner of the 
                # rectangle, and the last two columns the longitude and latitude 
                # of the upper right corner.
                region = self.cfg.INSET.outline_region
                rectangle = [[region[0], region[2], region[1], region[3]]]
                self.f.plot(data=rectangle, 
                            style=self.cfg.INSET.outline_style,
                            pen=self.cfg.PENS.inset_outline, 
                            projection=self.cfg.INSET.projection,
                            )

                # Plot Bird 2003 Plate boundary model on the inset for reference
                if self.CFG.FLAGS.inset_plate_boundaries:
                    plate_boundaries = read_pb_plate_boundaries(
                        fid=self.CFG.FILES.plate_boundaries)
                    for segment in plate_boundaries:
                        x, y = segment.T
                        self.f.plot(x=x, y=y, 
                                    pen=self.cfg.PENS.inset_plate_boundaries,
                                    projection=self.cfg.INSET.projection
                                    )


    def stations(self):
        """
        Plot station markers either from a file or internal data
        """
        if not self.cfg.FLAGS.stations:
            return
        
        print(f"plotting station file")
        # Read stations from specified file
        if self.cfg.FILES.stations:
            stations = read_stations(self.cfg.FILES.stations,
                                     self.cfg.FORMATS.stations)
            if self.cfg.STATIONS.color_by == "network":
                # We will need to temporarily overwrite the color parameter
                # in kwargs
                _kwargs = self.cfg.STATIONS.plot_kwargs
                indices = np.array([], dtype=int)
                for network, color in self.cfg.STATIONS.network_colors.items():
                    _kwargs["fill"] = color
                    subset = np.where(stations.networks == network)[0]
                    print(
                        f"{len(subset)} stations in net {network}, {color}")
                    self.f.plot(x=stations.longitudes[subset],
                                y=stations.latitudes[subset], **_kwargs)
                    # Collect the plotted indices to get remainder
                    indices = np.concatenate((indices, subset))
                # Plot remaining stations that arent already plotted
                _remaining = np.delete(stations.latitudes, indices)
                if _remaining.any():
                    print(f"{len(_remaining)} stations with default color")
                    self.f.plot(x=np.delete(stations.longitudes, indices),
                                y=np.delete(stations.latitudes, indices),
                                **self.cfg.STATIONS.plot_kwargs)
            else:
                self.f.plot(x=stations.longitudes, y=stations.latitudes,
                            **self.cfg.STATIONS.plot_kwargs)
        # Potentially gather stations on-the-fly here
        # !!!

    def earthquakes(self, fid=None, fmt=None, mt=True, colorbar=True):
        """
        Plot beachball moment tensors or focal mechanisms
        """
        # Separate plotting parameters for earthquakes and moment tensors
        if mt:
            if not self.cfg.FLAGS.moment_tensors:
                return
            if fid is None:
                fid = self.cfg.FILES.moment_tensors
            if fmt is None:
                fmt = self.cfg.FORMATS.moment_tensors
        else:
            if not self.cfg.FLAGS.earthquakes:
                return
            if fid is None:
                fid = self.cfg.FILES.earthquakes
            if fmt is None:
                fmt = self.cfg.FORMATS.earthquakes

        lats, lons, depths, mt_dict = read_earthquakes(fid=fid, fmt=fmt, mt=mt)
        if mt: 
            _print_val = "moment tensors"
        else:
            _print_val = "earthquakes"
        print(f"{len(lats)} {_print_val} colored by "
              f"{self.cfg.EARTHQUAKES.color_by}")

        # Determine how to color the moment tensors
        if self.cfg.EARTHQUAKES.color_by == "depth":
            self._make_cmap(depths, cbar=colorbar)
        else:
            raise NotImplementedError(
                f"EARTHQUAKES.color_by = {self.cfg.EARTHQUAKES.color_by} "
                f"is not a valid parameter"
            )
        
        if mt:
            self.f.meca(spec=mt_dict, latitude=lats, longitude=lons, 
                        depth=depths, scale=self.cfg.MOMENT_TENSORS.scale,
                        C=self.cfg.FLAGS.colorbar,
                        L=self.cfg.PENS.moment_tensors,
                        **self.cfg.MOMENT_TENSORS.kwargs
                        )
        else:
            self.f.plot(x=lons, y=lats, color=depths, 
                        cmap=self.cfg.FLAGS.colorbar,
                        **self.cfg.EARTHQUAKES.plot_kwargs)

    def _plot_shapefile(self, fid, **kwargs):
        """
        Generic function to plot a Shapefile which has information about 
        roads, faults etc.
        """
        gdf = gpd.read_file(fid)
        idx_key = gdf.keys()[0]
        idxs = set(gdf[idx_key])
        for idx in idxs:
            df = gdf[gdf[idx_key] == idx]
            self.f.plot(df, **kwargs)

    def faults(self):
        """
        Plot faults from Shapefiles read in using GeoPandas
        """
        if self.cfg.FLAGS.faults:
            print(f"plotting {len(self.cfg.FILES.faults)} fault file(s)")
            for fid in self.cfg.FILES.faults:
                self._plot_shapefile(fid, **self.cfg.FAULTS)

    def roads(self):
        """Plot roads from Shapefiles read in using GeoPandas"""
        if self.cfg.FLAGS.roads:
            print(f"plotting {len(self.cfg.FILES.roads)} road file(s)")
            for fid in self.cfg.FILES.roads:
                self._plot_shapefile(fid, **self.cfg.ROADS)

    def _make_cmap(self, arr, cbar=True):
        """
        Make a colormap for use with colorbar
        """
        cmap_min = self.cfg.COLORMAP.cmap_min
        if cmap_min is None:
            cmap_min = min(arr)
        cmap_max = self.cfg.COLORMAP.cmap_max
        if cmap_max is None:
            cmap_max = max(arr)

        pygmt.makecpt(
            cmap=self.cfg.COLORMAP.cmap,
            series=[cmap_min, cmap_max, self.cfg.COLORMAP.cmap_discretization]
                      )

        if cbar and self.cfg.FLAGS.colorbar:
            self.f.colorbar(position=self.cfg.COLORMAP.colorbar.position, 
                            frame=self.cfg.COLORMAP.colorbar.frame)

    def cities(self):
        """
        Plot lists of cities. A marker will be plotted on the exact location
        and the name of the city will be annotated adjacent.
        """
        if not self.cfg.LISTS.CITIES:
            return
        cities = read_list(dict_data=self.cfg.LISTS.CITIES)
        self.f.plot(x=cities.x, y=cities.y, **self.cfg.CITIES.plot_kwargs)
        self.f.text(text=cities.names, x=cities.x_text, y=cities.y_text,
                    **self.cfg.CITIES.text_kwargs)

    def landmarks(self):
        """
        Plot landmarks such as geographic locations, plate labels, etc. Only
        text is annotated, it is meant to be large and easily noticeable.

        """
        if not self.cfg.LISTS.LANDMARKS:
            return
        landmarks = read_list(dict_data=self.cfg.LISTS.LANDMARKS)
        self.f.text(text=landmarks.names, x=landmarks.x, y=landmarks.y,
                    **self.cfg.LANDMARKS.text_kwargs)

    def structures(self):
        """
        Plot names of geologic structures like faults, basins, etc. These are
        only text and meant to be small and out of the way.
        """
        if not self.cfg.LISTS.STRUCTURES:
            return
        structures = read_list(dict_data=self.cfg.LISTS.STRUCTURES)
        self.f.text(text=structures.names, x=structures.x, y=structures.y,
                    **self.cfg.STRUCTURES.text_kwargs)

    def finalize(self):
        """
        Save the figure and show if required
        """
        if self.cfg.FLAGS.save_figure:
            if not os.path.exists(self.cfg.FILES.output):
                print(f"making output directory: {self.cfg.FILES.output}")
                os.mkdir(self.cfg.FILES.output)

            fid_out = os.path.join(self.cfg.FILES.output, self.cfg.FILES.fid_out)
            print(f"saving {fid_out}")
            self.f.savefig(fid_out,
                           transparent=self.cfg.COLORS.background_transparent)

        if self.cfg.FLAGS.show_figure:
            self.f.show(method="external")


if __name__ == "__main__":
    ba = BasedAlaska()
    ba.setup()
    ba.inset()
    ba.roads()
    ba.faults()
    ba.earthquakes(mt=False)
    if isinstance(ba.cfg.FILES.moment_tensors, list):
        for i, (fid, fmt) in enumerate(zip(ba.cfg.FILES.moment_tensors,
                                           ba.cfg.FORMATS.moment_tensors)):
            ba.earthquakes(fid, fmt, mt=True,
                           colorbar=bool(i+1==len(ba.cfg.FILES.moment_tensors))
                           )
    else:
        ba.earthquakes(mt=True)
    ba.stations()
    ba.cities()
    ba.landmarks()
    ba.structures()
    ba.finalize()

