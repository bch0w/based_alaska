"""
Function for reading the Yaml config file
"""
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

       

    


