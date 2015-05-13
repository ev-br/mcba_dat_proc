import os
import numpy as np
import dateutil

import mcba.db as db
from mcba.helpers import pairwise
from mcba.models.impurity import gamma, initial_q, k_F

"""Common bits and pieces for postprocessing scripts."""


def list_dbs(path, pred = lambda x: True):
    """List the DBs with filenames such that pred(fname) is True."""
    filez = []
    for filename in os.listdir(path):
        if "sqlite" in filename:
            if pred(filename):
                fname = os.path.join(path, filename)
                filez.append(fname)
    return filez


######################## results table ########################################
def load_results(fname):
    """Get the simulation results from the DB into a numpy record array.
    Scale the momenta by $k_F$.
    """
    handle, = db.get_handles(fname)
    par, res = db.get_param(handle), db.get_results(handle)

    dt = np.dtype([('N', 'int32'), ("L", "float64"), ("gamma", "float64"),
                   ("q", 'float64'), ("P1", 'float64'), ('P2', 'float64'),
                   ('overlap', 'float64')])
    arr = np.empty(1, dtype = dt)

    arr["N"], arr["gamma"], arr["L"] = par.N, gamma(par), par.L
    arr["q"] = initial_q(par)/k_F(par)
    arr["overlap"] = res["sum FSfq2"]

    arr["P1"] = res["sum P"] / k_F(par)
    arr["P2"] = arr["P1"] + (1.-arr["overlap"])*initial_q(par)/k_F(par)
    
    from mcba.models.impurity._db import get_model_name
    model_name = get_model_name(handle)
    if model_name == "SinglePair":
        arr["P2"]  = arr["P1"]

    return par, arr



def group_by(data, name, f=lambda x: x, decimals=8):
    """Given a record array, `data`, produce a dict of arrays (dtype-preserving),
    grouped by the value of an attribute, `name`. 
    If a callable is specified, then the resulting dict keys are data[f(name)], 
    otherwise just data[name].
    Optional decimals argument is forwarded to numpy.unique.
    NB: not shureproof in terms of floating-point operations. 
    """
    values = np.unique(data[f(name)].round(decimals=8))

    res = {}
    for value in values:
        xxx = [ d for d in data if np.allclose(d[f(name)], value, 
                atol=10**(-decimals), rtol=0) ]
        res[value] = np.array(xxx, dtype = data.dtype)
    return res



def filter_pred(filez, pred):
    """For all the DBs in filez, return the results where pred(par, data) is True."""
    data = []
    for fname in filez:
        par, arr = load_results(fname)
        if pred(par, arr):
            data += [arr]
            #print arr
    if data:
        data = np.concatenate(data) 
    return data



########################### log table ########################################

def load_conv_log(fname):
    # TODO: cleanup

    def gettime(date,time):
        dstr = " ".join([date, time])
        dd = dateutil.parser.parse(dstr)
        return dd

    handle,  = db.get_handles(fname)
    with handle:
        par, res = db.get_param(handle), db.get_results(handle)

        dtp = np.dtype( [('dT','float64'), ('Ns','int32'), ('sumr','float64'), ('P','float64')])
        data = np.empty(1,dtype = dtp)
        dT = 0
        for e,e2 in pairwise( handle.execute("""SELECT * FROM mcrun_log;""") ):
            print e, e2, "\n"
            dt = (gettime(e2[2], e2[3]) - gettime(e[2], e[3])).seconds
            if e[4] is not None: #is probably a restart, skip it
                dT += dt
                lst = e[4].split()
                Ns, sumr, P = lst[1], lst[3], lst[5]
                arr = np.empty(1, dtype=dtp)
                arr["dT"], arr["Ns"], arr["sumr"], arr["P"] = dT/60., int(Ns), float(sumr), float(P)
                data = np.concatenate((data, arr))
        data = np.delete(data, 0)
    print data

    return par, data





if __name__ == "__main__":
    import doctest
    doctest.testmod()
