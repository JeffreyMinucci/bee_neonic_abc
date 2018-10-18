from VarroaPy.VarroaPy.RunVarroaPop import VarroaPop
import numpy as np
import os


DATES = [3, 4, 5, 6, 7]
TREATMENTS = ['0', '10', '20', '40', '80', '160']
REPS = [24, 12, 12, 12, 12, 12]


def simulate(pars):
    '''
    Simulate data from the colony study using a set of VarroaPop parameters

    :param pars: Dictionary of parameters to vary.
                ICQueenStrength_mean
                ICQueenStrength_sd
                ICForagerLifespan_mean
                ICForagerLifespan_sd
                AIAdultLD50
                AIAdultSlope
                AILarvaLD50
                AILarvaSlope

    '''

    static_pars = {}
    for name, value in pars:
        if not name.endswith(('_mean','_sd')):
            static_pars[name] = value
    static_pars['NecPolFileEnable'] = 'true'

    for index, trt in enumerate(TREATMENTS):
        trt_pars = static_pars.copy()
        exposure_filename = 'clo_' + trt
        exposure_path = os.path.abspath(os.path.join('data', exposure_filename))
        trt_pars['NecPolFileName'] = exposure_path
        reps = REPS[index]
        for rep in range(0,reps):
            vp_pars = trt_pars.copy()
            #generate random gaussian parameters
            vp_pars['ICQueenStrength'] = 0
            vp_pars['ICForagerLifespan'] = 0
            while not (vp_pars['ICQueenStrength'] >= 1 and vp_pars['ICQueenStrength'] <= 5):
                vp_pars['ICQueenStrength'] = np.random.normal(loc = pars['ICQueenStrength_mean'], scale = pars['ICQueenStrength_sd'])
            while not (vp_pars['ICQueenStrength'] >= 4 and vp_pars['ICQueenStrength'] <= 16):
                vp_pars['ICForagerLifespan'] = np.random.normal(loc = pars['ICForagerLifespan_mean'], scale = pars['ICForagerLifespan_sd'])
            vp = VarroaPop(vp_pars, verbose=False, unique=True)
            vp.run_model()
            output = vp.get_output()


