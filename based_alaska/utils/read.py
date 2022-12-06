"""
Function for reading the Yaml config file
"""
import os
import sys
import numpy as np
import pandas as pd
from obspy import read_events
import yaml

class Dict(dict):
    """
    Small updated dictionary class which allows getting and setting keys as
    attributes. Makes it cleaner to access the dictionary
    """
    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, key):
        return self[key]


def read_yaml(fid):
    """
    Read the config yaml file and convert it to a Dict object
    Note only the first two nested dictionaries are converted to a Dict objects
    """
    with open(fid, "r") as f:
        attrs = yaml.load(f, Loader=yaml.Loader)

    for key, value in attrs.items():
        attrs[key] = Dict(value)
        for key2, value2 in attrs[key].items():
            if isinstance(value2, dict):
                attrs[key][key2] = Dict(value2)

    return Dict(attrs)


def read_stations(fid, fmt):
    """
    A generic read stations file that is capable of reading a variety of
    input formats but always returns the same format expected by the main
    plotting script.

    :type fid: str
    :param fid: file identifier
    :type fmt: str
    :param fmt: format
    :rtype: dict
    :return: a dictionary of station information that can be accessed by the
        plotting script
    """
    assert(os.path.exists(fid)), f"station file {fid} does not exist"

    stations_dict = Dict(networks=[], stations=[], latitudes=[], longitudes=[])
    
    # Read in SPECFEM3D STATIONS file format 
    if fmt.upper() == "SPECFEM":
        data = np.loadtxt(fid, dtype=str)
        stations_dict.stations = data[:, 0]
        stations_dict.networks = data[:, 1]
        stations_dict.latitudes = data[:, 2].astype(float)
        stations_dict.longitudes = data[:, 3].astype(float)
    else:
        sys.exit(f"Unexpected format {fmt} for stations file")

    return stations_dict


def read_earthquakes(fid, fmt, mt=True):
    """
    Read moment tensor information from disk

    :rtype: list, list, list, Pandas.DataFrame
    :return: lists and dataframe with earthquake information. 
        If mt is False, then the dataframe will be empty
    """
    mt_dict = Dict(mrr=[], mtt=[], mff=[], mrt=[], mrf=[], mtf=[], exponent=[])

    # Downloaded from GCMT in PSMECA format
    if fmt.upper() == "GCMT":
        data = np.loadtxt(fid, dtype=str)
        lons = data[:, 0].astype(float)
        lats = data[:, 1].astype(float)
        depths = data[:, 2].astype(float)
        if mt:
            mt_dict.mrr = data[:, 3].astype(float)
            mt_dict.mtt = data[:, 4].astype(float)
            mt_dict.mff = data[:, 5].astype(float)
            mt_dict.mrt = data[:, 6].astype(float)
            mt_dict.mrf = data[:, 7].astype(float)
            mt_dict.mtf = data[:, 8].astype(float)
            mt_dict.exponent = data[:, 9].astype(float)
    # Downloaded from data center in QUAKML (.xml) format
    elif fmt.upper() == "QUAKEML":
        lats, lons, depths = [], [], []
        cat = read_events(fid)
        for event in cat:
            lats.append(event.preferred_origin().latitude)
            lons.append(event.preferred_origin().longitude)
            depths.append(event.preferred_origin().depth * 1E-3)  # m -> km
            if mt:
                try:
                    fm = Dict(
                        event.preferred_focal_mechanism().moment_tensor.tensor
                    )
                except AttributeError:
                    continue
                mt_dict.mrr.append(fm.m_rr)
                mt_dict.mtt.append(fm.m_tt)
                mt_dict.mff.append(fm.m_pp)
                mt_dict.mrt.append(fm.m_rt)
                mt_dict.mrf.append(fm.m_rp)
                mt_dict.mtf.append(fm.m_tp)
                mt_dict.exponent.append(7)

    # PyGMT.meca() plays nicer with Pandas Data Frames so convert before return
    mt_dict = pd.DataFrame(mt_dict)

    return lats, lons, depths, mt_dict


def read_list(fid=None, dict_data=None, fmt=None):
    """
    Read a list of points to plot, e.g., cities, landmarks, plate names
    If fmt==None, will expect to be parsing an internal list in par file
    """
    
    list_dict = Dict(names=[], x=[], y=[], x_text=[], y_text=[])

    if (dict_data is not None) and (fmt is None):
        list_dict.names = list(dict_data.keys())
        coords = dict_data.values()
        for coord in list(coords):
            list_dict.x.append(float(coord.split(",")[0]))
            list_dict.y.append(float(coord.split(",")[1]))
            # If text position not given, take from marker position
            try:
                list_dict.x_text.append(float(coord.split(",")[2]))
            except (IndexError, ValueError):
                list_dict.x_text.append(float(coord.split(",")[0]))
            try:
                list_dict.y_text.append(float(coord.split(",")[3]))
            except (IndexError, ValueError):
                list_dict.y_text.append(float(coord.split(",")[1]))
    else:
        a=1/0

    return list_dict
    


