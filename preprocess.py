#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 14:50:04 2020

@author: vyvo
"""
import re
import pandas as pd 
import numpy as np
import pycountry as pcy

import ast

pd.set_option('display.max_columns',100)
pd.set_option('display.max_rows',500)


#1. read dataset
data = pd.read_csv('datafull.csv')


#2.Remove records where description = 0 & set other '0' as null values  
data = data[data.description!='0'].reset_index()

for col in ['exp_level','job_func','industry','job_type']: 
    data[col] = data[col].map(lambda x: np.nan if x=='0' else x)
        
#3. LOCATION: get Country & Area

#extract Country from Link 
data['iso'] = data['link'].str.extract(r'https://([a-z]+)')
data['iso'] = data['iso'].map(lambda x: 'us' if x=='www' else x)

def to_country(x):
    if x == 'us':
        return 'United States'
    elif x == 'uk':
        return 'United Kingdom'
    else: 
        return (pcy.countries.get(alpha_2=x.upper()).name)

data['Country'] = data['iso'].apply(to_country)

#extract Area (State / City)  from Location 

nrow = data.shape[0]
loc = data['location'].str.split(', ') #split into list

for i in range(nrow): 
    #print(loc[i])
    if data['Country'][i] in loc[i] and len(loc[i])>1:
        loc[i].remove(data['Country'][i]) #remove 'Country' from the value

us_state = {
    'CA':'California','OR':'Oregon','GA':'Georgia','NY':'New York','MA':'Massachusetts',
    'PA':'Pennsylvania','AZ':'Arizona','TX':'Texas', 'IL':'Illinois','MN':'Minnesota'
    }
#normalize values of area 
def to_area(x): 
    if len(x) == 2:
        return us_state[x]
    elif 'Metropolitan' in x: 
        p = re.compile(r'(.*) Metropolitan') 
        return p.findall(x)[0]
    else: 
        return x
  
loc = loc.map(lambda x: x[-1])   
data['Area'] = loc.apply(to_area)


#4. EXP LEVEL/ JOB FUNC / INDUSTRY / JOB TYPE

#convert to List & get unique values for JOB FUNC / INDUSTRY 

data['job_func'] = data['job_func'].map(lambda x: ast.literal_eval(x) if x is not np.nan else x)
data['industry'] = data['industry'].map(lambda x: ast.literal_eval(x) if x is not np.nan else x)

fucins = {}
for i in range(nrow):
    try:
        country = data['Country'][i]
        if country in fucins.keys():        
            fl = list(filter(lambda x: x not in fucins[country],data['job_func'][i]))
            il = list(filter(lambda x: x not in fucins[country],data['industry'][i]))
            fl.extend(il)
            fucins[data['Country'][i]].extend(fl)
        else: 
            fucins[country] = []
    except: 
        pass            

# extract file to be translated 

foreign = ['China','Japan','France','Germany','Italy','Netherlands','Spain','Sweden','Switzerland']
for country in foreign: 
    df = data[data.Country == country]
    text = []
    for raw in [df['exp_level'].unique(),df['job_type'].unique(),fucins[country]]:
        text.extend(raw)
    filename = country+'.xlsx'
    get_file(text,filename,country)            
    

# get translated results 

original = {}
for country in foreign: 
    path = '/Users/vyvo/raw text/'+country+'.xlsx'
    file = pd.read_excel(path)
    original[country] = file[0]
    
trans = pd.read_excel('translated.xlsx')
 
#form dictionary of 'original:translated'
dictionary = {}

for country in foreign: 
    trs = trans[country].dropna()
    if len(trs) != len(original[country]):
        print('Unmatched length for',country)
        pass 
    else: 
        for i in range(len(trs)):
            dictionary[original[country][i]] = trs[i]

#normalize values in dictionary 

     
# translate 
for col in ['exp_level','job_type','job_func','industry']:
    new = col+'_v2'
    if col in ['exp_level','job_type']:         
        data[new] = data[col].map(lambda x: translate(x) if x in dictionary.keys() else x)
    else: 
        data[new] = data[col].map(lambda x: [translate(i) for i in x] if isinstance(x,list) else x)
         
test = data.dropna()
idx = test[test.non_English==1].index
