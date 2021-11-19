"""
Conversion functions that can be called on-the-fly to get data in the correct
format for plotting
"""


def catalog_to_mt_meca(cat):
    """
    Convert an ObsPy catalog to a dict object that can be fed into 
    pygmt.Figure.meca using the 'mt' format
    """
    latitude, longitude, depth = [], [], []
    
    # Define which components to grab
    choices = {"mt": ["mrr", "mtt", "mff", "mrt", "mrf", "mtf"],
               "aki": ["strike", "dip", "magnitude"],
               "gcmt": ["strike1", "dip1", "rake1", "strike2", "dip2", "rake2",
                        "mantissa", "exponent"],
               }
    
    # one liner dict creation from choice list


    for event in cat:
        latitude.append(event.preferred_origin().latitude)
        longitude.append(event.preferred_origin().longitude)
        depth.append(event.preferred_origin().depth)

        if spec == "mt":
            mt = event.preferred_focal_mechanism().moment_tensor.tensor
            meca_dict["m_rr"].append(mt.m_rr)
            meca_dict["m_tt"].append(mt.m_tt)
            meca_dict["m_ff"].append(mt.m_pp)
            meca_dict["m_rt"].append(mt.m_rt)
            meca_dict["m_rf"].append(mt.m_rp)
            meca_dict["m_tf"].append(mt.m_tp)

    return latitude, longitude, depth, meca_dict

        


    




    

