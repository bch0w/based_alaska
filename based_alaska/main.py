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

from utils.read import read_yaml

if __name__ == "__main__":
    cfg_fid = sys.argv[1] or "default"

    # Determine if config parameter passed in actually matches
    assert(os.path.exists(f"./configs/{cfg_id}")), \
            (f"config {cfg_id} does not exist, check configs directory for "
             f"available choices")

    # Load in the config file to control the behavior of plotting functions
    cfg = read_yaml(cfg_fid)

    # Start baking
    f = pygmt.Figure()

    f.coast(projection=cfg.BASEMAP.projection, region=cfg.BASEMAP.region,
            shorelines=cfg.PENS.shorelines, frame=cfg.BASEMAP.frame,
            land=cfg.COLOR.land, water=cfg.COLOR.water, lakes=cfg.COLOR.lakes,
            area_thresh=cfg.BASEMAP.area_thresh, 
            resolution=cfg.BASEMAP.resolution, **cfg.BASEMAP.kwargs)

    if cfg.FLAGS.scale_bar:
        with pygmt.config(MAP_TICK_PEN_PRIMARY=cfg.PENS.scalebar):
            f.basemap(region=cfg.BASEMAP.region, 
                      projection=cfg.BASEMAP.projection,
                      map_scale=cfg.BASEMAP.map_scale)

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
               L=cfg.PENS.moment_tensors, **cfg.MOMENT_TENSORS.kwargs)

    if cfg.FLAGS.inset:
        with f.inset(position=cfg.INSET.position, margin=cfg.INSET.margin):
            f.coast(region=cfg.INSET.region, projection=cfg.INSET.projection,
                    land=cfg.COLORS.inset_land, water=cfg.COLORS.inset_water,
                    shorelines=cfg.PENS.shorelines, frame=cfg.INSET.frame,
                    resolution=cfg.INSET.resolution, 
                    area_thresh=cfg.INSET.area_thresh)

            # Box the region here
    
    # Finalizations 
    if cfg.FLAGS.save_figure:
        if not os.path.exists(cfg.FILES.output):
            print(f"making output directory: {cfg.FILES.output}")
            os.mkdirs(cfg.FILES.output)

        f.savefig(os.path.join(cfg.FILES.ouput, cfg.FILES.fid_out), 
                  transparent=cfg.COLORS.background_transparent)

    if cfg.FLAGS.show_figure:
        f.show(method="external")










