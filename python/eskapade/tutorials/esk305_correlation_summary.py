# **********************************************************************************
# * Project: Eskapade - A python-based package for data analysis                   *
# * Macro  : esk305_correlation_summary                                            *
# * Created: 2017/04/04                                                            *
# * Description:                                                                   *
# *      Macro to demonstrate generating correlation heatmaps                      *
# *                                                                                *
# *                                                                                *
# * Authors:                                                                       *
# *      KPMG Big Data Team                                                        *
# *                                                                                *
# * Redistribution and use in source and binary forms, with or without             *
# * modification, are permitted according to the terms listed in the file          *
# * LICENSE.                                                                       *
# **********************************************************************************

import logging

from eskapade import ConfigObject, resources
from eskapade import analysis, visualization
from eskapade import process_manager

log = logging.getLogger('macro.esk305_correlation_summary')

log.debug('Now parsing configuration file esk305_correlation_summary')

#########################################################################################
# --- minimal analysis information

settings = process_manager.service(ConfigObject)
settings['analysisName'] = 'esk305_correlation_summary'
settings['version'] = 0

#########################################################################################
# --- Analysis values, settings, helper functions, configuration flags.

settings['input_path'] = resources.fixture('correlated_data.sv.gz')
settings['reader'] = 'csv'
settings['separator'] = ' '
settings['correlations'] = ['pearson', 'kendall', 'spearman', 'correlation_ratio']

#########################################################################################
# --- now set up the chains and links based on configuration flags

# create chains
process_manager.add_chain('Data')
process_manager.add_chain('Summary')

# load data
reader = analysis.ReadToDf(name='reader',
                           path=settings['input_path'],
                           sep=settings['separator'],
                           key='input_data',
                           reader=settings['reader'])

process_manager.get_chain('Data').add_link(reader)

# make visualizations of correlations
corr_link = visualization.CorrelationSummary(name='correlation_summary',
                                             read_key='input_data',
                                             store_key='correlations',
                                             methods=settings['correlations'])

process_manager.get_chain('Summary').add_link(corr_link)

#########################################################################################

log.debug('Done parsing configuration file esk305_correlation_summary')