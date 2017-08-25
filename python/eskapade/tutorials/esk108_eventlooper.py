# **********************************************************************************
# * Project: Eskapade - A python-based package for data analysis                   *
# * Macro  : esk108_eventlooper                                                         
# * Created: 2017/02/20                                                            *
# * Description:                                                                   *
# *      Macro to illustrate how input lines can be read in,
# *      processed, and reprinted. E.g. for use in map reduce application.
# *      Used as input for: esk108_map and esk108_reduce 
# *      
# * Authors:                                                                       *
# *      KPMG Big Data team, Amstelveen, The Netherlands
# *                                                                                *
# * Redistribution and use in source and binary forms, with or without             *
# * modification, are permitted according to the terms listed in the file          *
# * LICENSE.                                                                       *
# **********************************************************************************

import tempfile

from eskapade import ConfigObject
from eskapade import core_ops
from eskapade import process_manager

#########################################################################################
# --- minimal analysis information
settings = process_manager.service(ConfigObject)
settings['analysisName'] = 'esk108_eventlooper'
settings['version'] = 0

#########################################################################################
# --- Analysis values, settings, helper functions, configuration flags.

settings['do_map'] = False if not 'do_map' in settings else settings['do_map']
settings['do_reduce'] = False if not 'do_reduce' in settings else settings['do_reduce']

settings['TESTING'] = False if not 'TESTING' in settings else settings['TESTING']

# --- create dummy example dataset, which is used below
if settings['TESTING']:
    tmp = b"""# dataset from: 
# https://rajmak.wordpress.com/2013/04/27/clustering-text-map-reduce-in-python/
Converse All Star PC2 - Boys' Toddler
HI Nike Sport Girls Golf Dress
Brooks Nightlife Infiniti 1/2 Zip - Women's
HI Nike Solid Girls Golf Shorts
Nike Therma-FIT K.O. (MLB Rays)
adidas adiPURE IV TRX FG - Men's
Nike College All-Purpose Seasonal Graphic (Oklahoma) Womens T-Shirt
adidas Adipure 11PRO TRX FG - Women's
HI Nike Team (NFL Giants) BCA Womens T-Shirt
adidas Sprintstar 4 - Men's
HI Nike Attitude (NFL Titans) BCA Womens T-Shirt
HI Nike Polo Girls Golf Dress
Nike Therma-FIT K.O. (MLB Twins)
adidas Sprintstar 3 - Women's
Under Armour Performance Team Polo - Mens - For All Sports - Clothing - Purple/White
Converse All Star Ox - Girls' Toddler
HI Nike College All-Purpose Seasonal Graphic (Washington) Womens T-Shirt
Under Armour Performance Team Polo - Mens - For All Sports - Clothing - Red/White
Nike Therma-FIT K.O. (MLB Phillies)
Brooks Nightlife Infiniti 1/2 Zip Jacket - Mens
"""
    f = tempfile.NamedTemporaryFile(delete=False)
    f.write(tmp)
    f.close()
    # file is not immediately deleted because we used delete=False
    # used below with f.name


def to_lower(x):
    return x.lower()


def first_word(x):
    return x.split()[0]


#########################################################################################
# --- now set up the chains and links based on configuration flags

# This chain does 'mapping'. (macro B does 'reduction'.) 

# --- mapper: chain with event looper
#     this eventlooper link serves as a mapper.
#     in this example the lines are converted to lower chars, and the first word is selected.
if settings['do_map']:
    ch = process_manager.add_chain("Mapper")
    looper = core_ops.EventLooper(name='listener')
    looper.skip_line_beginning_with = ['#']
    looper.line_processor_set = [first_word, to_lower]
    if settings['TESTING']:
        looper.filename = f.name
    ch.add_link(looper)

# --- reducer: chain with event looper
#     this eventlooper link serves as a reducer
#     in this example the lines are grouped together into unique sets.
if settings['do_reduce']:
    ch = process_manager.add_chain("Reducer")
    looper = core_ops.EventLooper(name='grouper')
    # reducer selects all unique lines
    looper.sort = True
    looper.unique = True
    looper.storeKey = 'products'
    if settings['TESTING']:
        looper.filename = f.name
    ch.add_link(looper)

    # ... do other operations to lines here 

    # print lines
    link = core_ops.LinePrinter()
    link.readKey = looper.storeKey
    ch.add_link(link)