"""
The master config file defines all the available parameters that can be fed
into the main plotting script. It is reasonable to assume that sub-configs that
are not updated for a while may fall behind the master config file and no longer
work as expected. 

This function will 
1) check a sub config against the master
2) determine what parameters (if any) are missing from the sub config file
3) recommend suggested values for parameters, and/or auto-fill a new sub-config
    file so that it works as intended with the main plotting script
"""
