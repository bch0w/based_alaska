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

from utils.read import read_yaml, read_stations, read_list


class BasedAlaska:
    """
    A class to control plotting functionalities and store config parameters.
    It's based, yo.
    """
    def __init__(self, fid=None):
        """
        Must have a config file to initiate the based'ness
        """
        if fid is None:
            try:
                fid = sys.argv[1]
            except IndexError as e:
                fid = "master"
                print(f"No user config defined, setting config to {fid}")

        # Generate the full path to the config file, hardcoded dir. structure
        fid = os.path.join(os.getcwd(), "configs", cfg_fid) + ".yaml"

        self.cfg = read_yaml(fid)

    def setup(self):
        """
        Setup the plot, which usually means frame, coastline or topography
        """

if __name__ == "__main__":
    try:
        cfg_fid = sys.argv[1]
    except IndexError:
        cfg_fid = "master"
        print(f"No user config defined, setting config to {cfg_fid}")
        
    cfg_fid = os.path.join(os.getcwd(), "configs", cfg_fid) + ".yaml"

    # Determine if config parameter passed in actually matches
    assert os.path.exists(cfg_fid), \
            (f"config {cfg_fid} does not exist, check configs directory for "
             f"available choices")

    # Load in the config file to control the behavior of plotting functions
    cfg = read_yaml(cfg_fid)

    # Start baking
    f = pygmt.Figure()

    # Earth Relief (Topography) with a coastline outline
    if cfg.FLAGS.earth_relief:
        grid = pygmt.datasets.load_earth_relief(
                    resolution=cfg.BASEMAP.earth_relief.resolution,
                    region=cfg.BASEMAP.region
                    )
        f.grdimage(grid=grid, projection=cfg.BASEMAP.projection,
                   cmap=cfg.BASEMAP.earth_relief.cmap)
        f.coast(projection=cfg.BASEMAP.projection, region=cfg.BASEMAP.region,
                shorelines=cfg.PENS.shorelines, frame=cfg.BASEMAP.frame,
                resolution=cfg.BASEMAP.resolution, 
                area_thresh=cfg.BASEMAP.area_thresh,
                **cfg.BASEMAP.kwargs)
    # OR Just a coastline with solid color water and land
    else:
        f.coast(projection=cfg.BASEMAP.projection, region=cfg.BASEMAP.region,
                shorelines=cfg.PENS.shorelines, frame=cfg.BASEMAP.frame,
                land=cfg.COLORS.land, water=cfg.COLORS.water, 
                lakes=cfg.COLORS.lakes, area_thresh=cfg.BASEMAP.area_thresh, 
                resolution=cfg.BASEMAP.resolution, **cfg.BASEMAP.kwargs)

    # Add a scale bar for distance measurement
    if cfg.FLAGS.scale_bar:
        with pygmt.config(MAP_TICK_PEN_PRIMARY=cfg.PENS.scalebar):
            f.basemap(region=cfg.BASEMAP.region, 
                      projection=cfg.BASEMAP.projection,
                      map_scale=cfg.BASEMAP.map_scale)

    # Stations Markers, can color by different parameters
    if cfg.FLAGS.stations:
        # Read stations from specified file
        if cfg.FILES.stations:
            stations = read_stations(cfg.FILES.stations, cfg.FORMATS.stations)
            if cfg.STATIONS.color_by == "network":
                # We will need to temporarily overwrite the color parameter in 
                # kwargs
                _kwargs = cfg.STATIONS.plot_kwargs
                indices = np.array([], dtype=int)
                for network, color in cfg.STATIONS.network_colors.items():
                    _kwargs["color"] = color
                    subset = np.where(stations.networks==network)[0]
                    print(f"{len(subset)} stations in net {network}, {color}")
                    f.plot(x=stations.longitudes[subset], 
                           y=stations.latitudes[subset], **_kwargs)
                    # Collect the plotted indices to get remainder
                    indices = np.concatenate((indices, subset))
                # Plot remaining stations that arent already plotted
                _remaining = np.delete(stations.latitudes, indices)
                if _remaining.any():
                    print(f"{len(_remaining)} stations with default color")
                    f.plot(x=np.delete(stations.longitudes, indices),
                           y=np.delete(stations.latitudes, indices), 
                           **cfg.STATIONS.plot_kwargs)
            else:
                f.plot(x=stations.longitudes, y=stations.latitudes,  
                       **cfg.STATIONS.plot_kwargs)
        # Potentially gather stations on-the-fly here
        # !!!

    # Earthquake moment tensors
    if cfg.FLAGS.moment_tensors and cfg.FILES.moment_tensors:
        # Determine how to color the moment tensors
        if cfg.MOMENT_TENSORS.color_by == "depth":
            depths = np.loadtxt(cfg.FILES.moment_tensors, usecols=2, 
                                dtype=float)
            pygmt.makecpt(cmap=cfg.MOMENT_TENSORS.cmap, 
                          series=[min(depths), max(depths), 
                                  cfg.MOMENT_TENSORS.cmap_discretization]
                          )
        else:
            raise NotImplementedError(
                    f"MOMENT_TENSOR.color_by = {cfg.MOMENT_TENSOR.color_by} "
                    f"is not a valid parameter"
                    )

        f.meca(cfg.FILES.moment_tensors, scale=cfg.MOMENT_TENSORS.scale,
               convention=cfg.MOMENT_TENSORS.convention, 
               C=cfg.FLAGS.mt_colorbar,
               L=cfg.PENS.moment_tensors, **cfg.MOMENT_TENSORS.kwargs)

        if cfg.FLAGS.mt_colorbar:
            f.colorbar(position=cfg.MOMENT_TENSORS.colorbar.position,
                       frame=cfg.MOMENT_TENSORS.colorbar.frame)

    # Map inset with wider map view
    if cfg.FLAGS.map_inset:
        with f.inset(position=cfg.INSET.position, margin=cfg.INSET.margin):
            f.coast(region=cfg.INSET.region, projection=cfg.INSET.projection,
                    land=cfg.COLORS.inset_land, water=cfg.COLORS.inset_water,
                    shorelines=cfg.PENS.shorelines, frame=cfg.INSET.frame,
                    resolution=cfg.INSET.resolution, 
                    area_thresh=cfg.INSET.area_thresh)
            # TO DO: Box the region here
            # !!!!

    # Plot lists of cities, landmarks etc.
    if cfg.LISTS.CITIES:
        cities = read_list(dict_data=cfg.LISTS.CITIES)
        f.plot(x=cities.x, y=cities.y, **cfg.CITIES.plot_kwargs)
        f.text(text=cities.names, x=cities.x_text, y=cities.y_text, 
               **cfg.CITIES.text_kwargs)

    if cfg.LISTS.LANDMARKS:
        landmarks = read_list(dict_data=cfg.LISTS.LANDMARKS)
        f.text(text=landmarks.names, x=landmarks.x, y=landmarks.y,
               **cfg.LANDMARKS.text_kwargs)
    
    
    # Finalizations 
    if cfg.FLAGS.save_figure:
        if not os.path.exists(cfg.FILES.output):
            print(f"making output directory: {cfg.FILES.output}")
            os.mkdirs(cfg.FILES.output)

        f.savefig(os.path.join(cfg.FILES.output, cfg.FILES.fid_out), 
                  transparent=cfg.COLORS.background_transparent)

    if cfg.FLAGS.show_figure:
        f.show(method="external")










