import sys
import os
import numpy as np
from itertools import product
from argparse import ArgumentParser

from mcba.models.impurity import Par, SingleImpurity, initial_q, gamma
from mcba.walker import Walker
from mcba.helpers import copydict
from mcba.walker_factory import WalkerFactory


def main(action_args):

    mc_dict = {"num_sweeps"      : np.Inf,
              "steps_per_sweep" : 100,
              "therm_sweeps"    : 0,
              "checkp_sweeps"   : 100,
              "printout_sweeps" : 100,
              "seed"            : 42,
              "verbose_logg"    : True,
              "threshold"       : 0.96, 
              "store_roots"     : False,
            }

    V = 2.5
    N0 = 135
    mqs = [1, 2, 3, 4, 5]
    N_f = [1]
    #mqs = [8, 9, 11, 12, 14, 15]

    base_path="../data/meff"
    tasks = []
    for f in N_f:
        N = N0 * f
        for mq in mqs:
            par = Par(N=N, L=3*N, V=V, m_q=mq*f)
            db_fname = os.path.join(base_path, 
                                    "N{0}V2.5mq{1}.sqlite".format(par.N, par.m_q))
            dct = {"model": SingleImpurity(par), 
                   "db_fname": db_fname}
            tasks.append( copydict(mc_dict, dct) )

    if action_args.dry_run:
        for task in tasks:
            p = task['model'].par
            print task, p
            print 'GAMMA: ', gamma(p), 'q = ', initial_q(p), '\n'
        print len(tasks)   
    else:
        factory = WalkerFactory(tasks, 5, freq=1, verbose=True)
        factory.start()

#######################
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--dry_run", action='store_true')
    args = parser.parse_args(sys.argv[1:])
    main(args)

