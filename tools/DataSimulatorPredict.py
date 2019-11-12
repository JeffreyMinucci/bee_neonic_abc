from VarroaPy.VarroaPy.RunVarroaPop import VarroaPop
from itertools import product
import numpy as np
import os
import pandas as pd
import datetime

#DEBUG options
LOGS = False

#Start date for sims = CCA3, 06/20/2014
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..','data'))
INITIAL_DF = os.path.join(DATA_DIR, 'bee_counts/initial_conditions.csv')
START_DATE = '06/20/2014'
END_DATE = '10/22/2014'
VRP_FILE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        '..','varroapop_sessions', 'feeding_study.vrp'))

DATES = ['4', '5', '6', '7']
DATES_STR = ['07/16/2014', '08/08/2014','09/10/2014', '10/15/2014']
DATES_STR_HIGH = ['07/16/2014', '08/08/2014','09/10/2014', '10/21/2014']  # high had a late CCA7
TREATMENTS = ['0','50', '55', '60', '65', '70']
REPS = [12, 12, 12, 12, 12, 12]
#REPS = [3,3,3,3,3,3]  # for testing
#REPS = [1,1,1,1,1,1]  # for testing
RESPONSE_VARS = [('Adults', ['Adult Drones', 'Adult Workers']),('Pupae',['Capped Drone Brood', 'Capped Worker Brood']),
                 ('Larvae', ['Drone Larvae', 'Worker Larvae']),  ('Eggs', ['Drone Eggs', 'Worker Eggs'])]
RESPONSE_FILTER = ['Adults_mean', 'Adults_sd', 'Eggs_mean', 'Eggs_sd']  # For now use only these responses!



def filter_rep_responses(output, dates_str):
    """
    From raw VarroaPop output, filter out the dates and response variables that we need for our summary stats.
    :param output: dataframe of VarroaPop raw outputs
    :param dates_str: Dates of the desired observations
    :return: a dataframe with raw response vars in the columns and dates in the rows
    """

    output.set_index('Date',inplace=True)
    #print('REP output: {}'.format(output))
    #print([output.loc[dates_str, cols[1]].sum(axis=1) for cols in RESPONSE_VARS])
    responses = [output.loc[dates_str, cols[1]].sum(axis=1) for cols in RESPONSE_VARS]
    #print(responses)
    col_names = [x[0] for x in RESPONSE_VARS]
    response_df = pd.DataFrame.from_items(zip(col_names,responses))
    #print("REP filtered responses: {}".format(response_df))
    return response_df


def generate_start(paras, trt):
    df = pd.read_csv(INITIAL_DF)
    df['treatment'] = df['treatment'].astype('str', copy=True)
    df.set_index('treatment', inplace=True)
    #print("Initial conditions: {}".format(df))
    vars = ['adults', 'pupae', 'larvae', 'eggs', 'pollen', 'honey'] #numbers to generate
    vals = [-1,-1,-1,-1,-1,-1]
    for i, var in enumerate(vars):
        while vals[i] < 0:
            vals[i] = np.random.normal(loc = df.loc["0",var+'_mean'], scale = df.loc["0",var+'_sd'])
    paras['ICWorkerAdults'] = vals[0] / 0.7  # increase to account for unseen foragers in VP
    paras['ICDroneAdults'] = 0
    paras['ICWorkerBrood'] = vals[1]
    paras['ICDroneBrood'] = 0
    paras['ICWorkerLarvae'] = vals[2]
    paras['ICDroneLarvae'] = 0
    paras['ICWorkerEggs'] = vals[3]
    paras['ICDroneEggs'] = 0
    paras['InitColPollen'] = vals[4] * 0.425  # based off 0.293 cm3 cell volume and 1.45 g/cm3 pollen density
    paras['InitColNectar'] = vals[5] * 0.331  # based off 0.293 cm3 cell volume and 1.13 g/cm3 nectar density
    return paras



def simulate_all_dates_p(pars, save = False, logs = False):
    """

    :param pars: Dictionary of parameters to vary.
                ICQueenStrength_mean
                ICQueenStrength_sd
                ICForagerLifespan_mean
                ICForagerLifespan_sd
                AIAdultLD50
                AIAdultSlope
                AILarvaLD50
                AILarvaSlope
    :return a 3d array of varroapop summary stats(treatment x day x adult/pupae/larvae/eggs)
    """
    start = datetime.datetime.strptime(START_DATE, "%m/%d/%Y")
    end = datetime.datetime.strptime(DATES_STR_HIGH[3], "%m/%d/%Y")
    all_dates = [(start + datetime.timedelta(days=x)).strftime("%m/%d/%Y") for x in range(0, (end - start).days)]
    parameters = pars.copy() #copy our inputs so that we don't ever modify them (pyabc needs these)
    static_pars = {'SimStart': START_DATE, 'SimEnd': END_DATE, 'IPollenTrips': 8, 'INectarTrips': 17,
                   'AIHalfLife': 25, 'RQEnableReQueen': 'false'}
    for name, value in parameters.items():
        if not name.endswith(('_mean','_sd')):
            static_pars[name] = value
    static_pars['NecPolFileEnable'] = 'true'
    weather_path = os.path.join(DATA_DIR,'weather/15055_grid_35.875_lat.wea')
    #all_responses = pd.DataFrame(index = rows, columns = cols)
    all_responses = pd.DataFrame()
    for index, trt in enumerate(TREATMENTS):
        trt_responses_mean = np.empty((len(DATES), len(RESPONSE_VARS)))
        trt_responses_sd = np.empty((len(DATES), len(RESPONSE_VARS)))
        trt_pars = static_pars.copy()
        exposure_filename = 'predict_' + trt + '.csv'
        exposure_path = os.path.join(DATA_DIR, 'food_concentrations', exposure_filename)
        trt_pars['NecPolFileName'] = exposure_path
        reps = REPS[index]
        rep_responses = np.empty(([len(all_dates),len(RESPONSE_VARS),reps])) #survey dates (rows) x output vars (cols) x reps (z axis)
        for rep in range(0,reps):
            vp_pars = generate_start(trt_pars.copy(), trt)
            #generate random gaussian parameters
            vp_pars['ICQueenStrength'] = 0
            vp_pars['ICForagerLifespan'] = 0
            while not (1 <=vp_pars['ICQueenStrength'] <= 5):
                vp_pars['ICQueenStrength'] = np.random.normal(loc = float(parameters['ICQueenStrength_mean']), scale = float(parameters['ICQueenStrength_sd']))
            while not (4 <= vp_pars['ICForagerLifespan'] <= 16):
                vp_pars['ICForagerLifespan'] = np.random.normal(loc = float(parameters['ICForagerLifespan_mean']), scale = float(parameters['ICForagerLifespan_sd']))
            vp = VarroaPop(parameters = vp_pars, weather_file = weather_path, vrp_file = VRP_FILE,
                           verbose=False, unique=True, keep_files=save, logs=logs)
            vp.run_model()
            rep_responses[:,:,rep] = filter_rep_responses(vp.get_output(), dates_str= all_dates)
        mean_cols = [var[0]+"_mean" for var in RESPONSE_VARS]
        sd_cols = [var[0]+"_sd" for var in RESPONSE_VARS]
        trt_responses_mean = pd.DataFrame(np.mean(rep_responses,axis=2), columns = mean_cols)
        trt_responses_sd = pd.DataFrame(np.std(rep_responses,axis=2, ddof=1), columns = sd_cols)  # Note: uses sample sd, not population sd
        trt_responses = pd.concat([trt_responses_mean, trt_responses_sd], axis = 1)
        #print("Treatment {} responses: {}".format(trt,trt_responses))
        start_row = len(DATES)*index
        end_row = start_row + len(DATES)
        #all_responses.loc[start_row:end_row,:] = trt_responses
        all_responses = all_responses.append(trt_responses, ignore_index=True)

    #Generate labels for rows and columns
    rows = ['_'.join(x) for x in product(TREATMENTS, all_dates)]
    response_cols = [x[0] for x in RESPONSE_VARS]
    cols = ['_'.join([x,y]) for y in ['mean', 'sd'] for x in response_cols]

    all_responses['Index'] = pd.Series(rows)  # Add our row labels
    all_responses.set_index("Index", inplace=True)  # Set row labels to be the index
    #print('Final result: {}'.format(all_responses))
    #filtered_resp = all_responses.loc[:,'Adults_mean']  # Keep only the mean number of adults
    n_dates = len(all_dates)
    return_dfs = {}
    for response in RESPONSE_VARS:
        filtered_resp = all_responses.loc[:,response[0]+"_mean"]
        #print('Filtered resp: {}'.format(filtered_resp))
        wide = np.empty([6,n_dates])  # 6 treatments, n_dates days,
        for i in range(6):
            wide[i,:] = filtered_resp.iloc[i*n_dates:(i+1)*n_dates]
        wide_df = pd.DataFrame(wide, index = ['0','50', '55', '60', '65', '70'],
                        columns = all_dates)
        return_dfs[response[0]] = wide_df
    # add all individuals sum
    all_ind_mean = all_responses.loc[:,all_responses.columns.str.contains('_mean')].sum(axis=1)
    wide = np.empty([6, n_dates])  # 6 treatments, n_dates days,
    for i in range(6):
        wide[i, :] = all_ind_mean.iloc[i * n_dates:(i + 1) * n_dates]
    wide_df = pd.DataFrame(wide, index=['0','50', '55', '60', '65', '70'],
                           columns=all_dates)
    return_dfs["All"] = wide_df
    return return_dfs
