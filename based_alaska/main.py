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

from utils.read import read_yaml, read_stations, read_list, read_moment_tensors


class BasedAlaska:
    """
    A class to control plotting functionalities and store config parameters.
    It's based, yo.
    """
    def __init__(self, fid=None):
        """
        Must have a config file to initiate the based'ness

        :type fid: str
        :param fid: config file name
        """
        if fid is None:
            try:
                fid = sys.argv[1]
            except IndexError as e:
                fid = "master"
                print(f"No user config defined, setting config to {fid}")

        # Generate the full path to the config file, hardcoded dir. structure
        fid = os.path.join(os.getcwd(), "configs", fid) + ".yaml"

        self.cfg = read_yaml(fid)
        self.f = pygmt.Figure()

    def setup(self):
        """
        Setup the plot, which usually means frame, coastline or topography
        """
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
        Create a map inset to show a larger domain
        """
        if self.cfg.FLAGS.map_inset:
            with self.f.inset(position=self.cfg.INSET.position,
                              margin=self.cfg.INSET.margin):
                self.f.coast(region=self.cfg.INSET.region,
                             projection=self.cfg.INSET.projection,
                             land=self.cfg.COLORS.inset_land,
                             water=self.cfg.COLORS.inset_water,
                             shorelines=self.cfg.PENS.shorelines,
                             frame=self.cfg.INSET.frame,
                             resolution=self.cfg.INSET.resolution,
                             area_thresh=self.cfg.INSET.area_thresh
                             )
                # TO DO: Box the region here
                # !!!!

    def stations(self):
        """
        Plot station markers either from a file or internal data
        """
        if not self.cfg.FLAGS.stations:
            return

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
                    _kwargs["color"] = color
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

    def earthquakes(self):
        """
        Plot earthquakes not as beachballs, but just as markers
        """
        if not self.cfg.FLAGS.earthquakes:
            return

    def moment_tensors(self, file=None, fmt=None):
        """
        Plot beachball moment tensors or focal mechanisms
        """
        if not self.cfg.FLAGS.moment_tensors:
            return
        if file is None:
            file = self.cfg.FILES.moment_tensors
        if fmt is None:
            fmt = self.cfg.FORMATS.moment_tensors

        lats, lons, depths, mt_dict = read_moment_tensors(file, fmt)
        print(f"{len(lats)} moment tensors colored by "
              f"{self.cfg.MOMENT_TENSORS.color_by}")

        # Determine how to color the moment tensors
        if self.cfg.MOMENT_TENSORS.color_by == "depth":
            pygmt.makecpt(
                cmap=self.cfg.MOMENT_TENSORS.cmap,
                series=[min(depths), max(depths),
                        self.cfg.MOMENT_TENSORS.cmap_discretization]
                          )
        else:
            raise NotImplementedError(
                f"MOMENT_TENSOR.color_by = {self.cfg.MOMENT_TENSOR.color_by} "
                f"is not a valid parameter"
            )

        # self.f.meca(spec=file,
        #             scale=self.cfg.MOMENT_TENSORS.scale,
        #             convention=self.cfg.MOMENT_TENSORS.convention,
        #             C=self.cfg.FLAGS.mt_colorbar,
        #             L=self.cfg.PENS.moment_tensors,
        #             **self.cfg.MOMENT_TENSORS.kwargs
        #             )
        self.f.meca(spec=mt_dict, latitude=lats, longitude=lons, depth=depths,
                    scale=self.cfg.MOMENT_TENSORS.scale,
                    # convention=self.cfg.MOMENT_TENSORS.convention,
                    C=self.cfg.FLAGS.mt_colorbar,
                    L=self.cfg.PENS.moment_tensors,
                    **self.cfg.MOMENT_TENSORS.kwargs
                    )

        if self.cfg.FLAGS.mt_colorbar:
            self.f.colorbar(
                position=self.cfg.MOMENT_TENSORS.colorbar.position,
                frame=self.cfg.MOMENT_TENSORS.colorbar.frame
            )

    def cities(self):
        """
        Plot lists of cities
        """
        if not self.cfg.LISTS.CITIES:
            return
        cities = read_list(dict_data=self.cfg.LISTS.CITIES)
        self.f.plot(x=cities.x, y=cities.y, **self.cfg.CITIES.plot_kwargs)
        self.f.text(text=cities.names, x=cities.x_text, y=cities.y_text,
                    **self.cfg.CITIES.text_kwargs)

    def landmarks(self):
        """
        Plot landmarks such as geographic locations, plate labels, etc.
        """
        if not self.cfg.LISTS.LANDMARKS:
            return
        landmarks = read_list(dict_data=self.cfg.LISTS.LANDMARKS)
        self.f.text(text=landmarks.names, x=landmarks.x, y=landmarks.y,
                    **self.cfg.LANDMARKS.text_kwargs)

    def finalize(self):
        """
        Save the figure and show if required
        """
        if self.cfg.FLAGS.save_figure:
            if not os.path.exists(self.cfg.FILES.output):
                print(f"making output directory: {self.cfg.FILES.output}")
                os.mkdirs(self.cfg.FILES.output)

            self.f.savefig(
                os.path.join(self.cfg.FILES.output, self.cfg.FILES.fid_out),
                transparent=self.cfg.COLORS.background_transparent
            )

        if self.cfg.FLAGS.show_figure:
            self.f.show(method="external")


if __name__ == "__main__":
    ba = BasedAlaska()
    ba.setup()
    ba.inset()
    ba.stations()
    ba.earthquakes()
    if isinstance(ba.cfg.FILES.moment_tensors, list):
        for fid, fmt in zip(ba.cfg.FILES.moment_tensors,
                            ba.cfg.FORMATS.moment_tensors):
            ba.moment_tensors(fid, fmt)
    else:
        ba.moment_tensors()
    ba.cities()
    ba.landmarks()
    ba.finalize()

