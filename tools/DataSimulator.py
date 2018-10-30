from VarroaPy.VarroaPy.RunVarroaPop import VarroaPop
import numpy as np
import os


DATES = [3, 4, 5, 6, 7]
DATES_STR = ['06/20/2014', '07/16/2014', '08/08/2014','09/10/2014', '10/15/2014']
DATES_STR_HIGH = ['06/20/2014', '07/16/2014', '08/08/2014','09/10/2014', '10/21/2014'] #high had a late CCA7
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
    weather_path = os.path.abspath(os.path.join('data', '15055_grid_35.875_lat.wea'))

    for index, trt in enumerate(TREATMENTS):
        trt_pars = static_pars.copy()
        exposure_filename = 'clo_feeding_' + trt + '.csv'
        exposure_path = os.path.abspath(os.path.join('data', exposure_filename))
        trt_pars['NecPolFileName'] = exposure_path
        reps = REPS[index]
        rep_responses = np.empty([len(DATES),30,reps]) #survey dates (rows) x output vars (cols) x reps (z axis)
        for rep in range(0,reps):
            vp_pars = trt_pars.copy()
            #generate random gaussian parameters
            vp_pars['ICQueenStrength'] = 0
            vp_pars['ICForagerLifespan'] = 0
            while not (vp_pars['ICQueenStrength'] >= 1 and vp_pars['ICQueenStrength'] <= 5):
                vp_pars['ICQueenStrength'] = np.random.normal(loc = pars['ICQueenStrength_mean'], scale = pars['ICQueenStrength_sd'])
            while not (vp_pars['ICQueenStrength'] >= 4 and vp_pars['ICQueenStrength'] <= 16):
                vp_pars['ICForagerLifespan'] = np.random.normal(loc = pars['ICForagerLifespan_mean'], scale = pars['ICForagerLifespan_sd'])
            vp = VarroaPop(parameters = vp_pars, weather_file = weather_path, verbose=False, unique=True)
            vp.run_model()
            if trt == "160":
                dates = DATES_STR_HIGH
            else:
                dates = DATES_STR
            rep_responses[:,:,rep] = filter_rep_responses(vp.filter_output(), dates_str= dates)



def filter_rep_responses(output, dates_str):
    




