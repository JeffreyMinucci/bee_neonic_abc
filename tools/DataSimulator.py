from VarroaPy.VarroaPy.RunVarroaPop import VarroaPop
from itertools import product
import numpy as np
import os
import pandas as pd


#Start date for sims = CCA3, 06/20/2014
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..','data'))
INITIAL_DF = os.path.join(DATA_DIR, 'initial_conditions.csv')
DATES = ['4', '5', '6', '7']
DATES_STR = ['07/16/2014', '08/08/2014','09/10/2014', '10/15/2014']
DATES_STR_HIGH = ['07/16/2014', '08/08/2014','09/10/2014', '10/21/2014'] #high had a late CCA7
TREATMENTS = ['0', '10', '20', '40', '80', '160']
REPS = [24, 12, 12, 12, 12, 12]
#REPS = [3,3,3,3,3,3] #for testing
RESPONSE_VARS = [('Adults', ['Adult Drones', 'Adult Workers', 'Foragers']),('Pupae',['Capped Drone Brood', 'Capped Worker Brood']),
                 ('Larvae', ['Drone Larvae', 'Worker Larvae']),  ('Eggs', ['Drone Eggs', 'Worker Eggs'])]
RESPONSE_FILTER = ['Adults_mean', 'Adults_sd'] #For now use only these responses!

def simulate(pars):
    """
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
    :return a dictionary of summary stats
    """
    #print(DATA_DIR)
    #print(INITIAL_DF)
    static_pars = {}
    for name, value in pars.items():
        if not name.endswith(('_mean','_sd')):
            static_pars[name] = value
    static_pars['NecPolFileEnable'] = 'true'
    weather_path = os.path.join(DATA_DIR,'15055_grid_35.875_lat.wea')# os.path.abspath(os.path.join('data', '15055_grid_35.875_lat.wea'))
    #all_responses = pd.DataFrame(index = rows, columns = cols)
    all_responses = pd.DataFrame()
    for index, trt in enumerate(TREATMENTS):
        trt_responses_mean = np.empty((len(DATES), len(RESPONSE_VARS)))
        trt_responses_sd = np.empty((len(DATES), len(RESPONSE_VARS)))
        trt_pars = static_pars.copy()
        exposure_filename = 'clo_feeding_' + trt + '.csv'
        exposure_path = os.path.join(DATA_DIR, exposure_filename)#os.path.abspath(os.path.join('data', exposure_filename))
        trt_pars['NecPolFileName'] = exposure_path
        reps = REPS[index]
        rep_responses = np.empty(([len(DATES),len(RESPONSE_VARS),reps])) #survey dates (rows) x output vars (cols) x reps (z axis)
        for rep in range(0,reps):
            vp_pars = generate_start(trt_pars.copy(), trt)
            #generate random gaussian parameters
            vp_pars['ICQueenStrength'] = 0
            vp_pars['ICForagerLifespan'] = 0
            while not (1 <=vp_pars['ICQueenStrength'] <= 5):
                vp_pars['ICQueenStrength'] = np.random.normal(loc = float(pars['ICQueenStrength_mean']), scale = float(pars['ICQueenStrength_sd']))
            while not (4 <= vp_pars['ICForagerLifespan'] <= 16):
                vp_pars['ICForagerLifespan'] = np.random.normal(loc = float(pars['ICForagerLifespan_mean']), scale = float(pars['ICForagerLifespan_sd']))
            vp = VarroaPop(parameters = vp_pars, weather_file = weather_path, verbose=False, unique=True, keep_files=False, logs=False)
            vp.run_model()
            if trt == "160":
                dates = DATES_STR_HIGH
            else:
                dates = DATES_STR
            rep_responses[:,:,rep] = filter_rep_responses(vp.get_output(), dates_str= dates)
        mean_cols = [var[0]+"_mean" for var in RESPONSE_VARS]
        sd_cols = [var[0]+"_sd" for var in RESPONSE_VARS]
        trt_responses_mean = pd.DataFrame(np.mean(rep_responses,axis=2), columns = mean_cols)
        trt_responses_sd = pd.DataFrame(np.std(rep_responses,axis=2, ddof=1), columns = sd_cols) # Note: uses sample sd, not population sd
        trt_responses = pd.concat([trt_responses_mean, trt_responses_sd], axis = 1)
        #print("Treatment {} responses: {}".format(trt,trt_responses))
        start_row = len(DATES)*index
        end_row = start_row + len(DATES)
        #all_responses.loc[start_row:end_row,:] = trt_responses
        all_responses = all_responses.append(trt_responses, ignore_index=True)

    #Generate labels for rows and columns
    rows = ['_'.join(x) for x in product(TREATMENTS, DATES)]
    #print('Row labels: {}'.format(rows))
    response_cols = [x[0] for x in RESPONSE_VARS]
    cols = ['_'.join([x,y]) for y in ['mean', 'sd'] for x in response_cols]
    #print('Col labels: {}'.format(cols))

    all_responses['Index'] = pd.Series(rows) #Add our row labels
    all_responses.set_index("Index", inplace=True) #Set row labels to be the index
    #print('Final result: {}'.format(all_responses))
    filtered_resp = all_responses.loc[:,RESPONSE_FILTER] #Keep only the summary stats that we are using
    #print('Filtered result: {}'.format(filtered_resp))
    output_dict = {}
    for row in filtered_resp.index:
        for col in filtered_resp.columns:
            label = "_".join([row,col])
            output_dict[label] = filtered_resp.loc[row,col]
    #print('Output dictionary: {}'.format(output_dict))
    return output_dict


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


def generate_start(pars, trt):
    df = pd.read_csv(INITIAL_DF)
    df['treatment'] = df['treatment'].astype('str', copy=True)
    df.set_index('treatment', inplace=True)
    #print("Initial conditions: {}".format(df))
    vars = ['adult', 'pupae', 'larvae', 'eggs', 'pollen', 'honey'] #numbers to generate
    vals = []
    for var in vars:
        vals.append(np.random.normal(loc = df.loc[trt,var+'_mean'], scale = df.loc[trt,var+'_sd'])) #TODO prevent negative numbers!
    pars['ICWorkerAdults'] = vals[0]
    pars['ICDroneAdults'] = 0
    pars['ICWorkerBrood'] = vals[1]
    pars['ICDroneBrood'] = 0
    pars['ICWorkerLarvae'] = vals[2]
    pars['ICDroneLarvae'] = 0
    pars['ICWorkerEggs'] = vals[3]
    pars['ICDroneEggs'] = 0
    pars['InitColPollen'] = 20000 #just doing a reasonable estimate for now
    pars['InitColNectar'] = 20000 #just doing a reasonable estimate for now
    print(pars)
    return pars


