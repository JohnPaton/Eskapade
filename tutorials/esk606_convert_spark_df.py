# ********************************************************************************
# * Project: Eskapade - A python-based package for data analysis                 *
# * Macro  : esk606_convert_spark_df                                             *
# * Created: 2017/06/08                                                          *
# * Description:                                                                 *
# *     Tutorial macro for converting Spark data frames into a different         *
# *     data type and apply transformation functions on the resulting data       *
# *                                                                              *
# * Redistribution and use in source and binary forms, with or without           *
# * modification, are permitted according to the terms listed in the file        *
# * LICENSE.                                                                     *
# ********************************************************************************

import logging
log = logging.getLogger('macro.esk606_convert_spark_df')

import pyspark

from eskapade import ConfigObject, DataStore, ProcessManager
from analytics_engine.spark_analysis import SparkManager
from analytics_engine import spark_analysis

log.debug('Now parsing configuration file esk606_convert_spark_df')


##########################################################################
# --- minimal analysis information

proc_mgr = ProcessManager()

settings = proc_mgr.service(ConfigObject)
settings['analysisName'] = 'esk606_convert_spark_df'
settings['version'] = 0


##########################################################################
# --- start Spark session

spark = proc_mgr.service(SparkManager).create_session(eskapade_settings=settings)


##########################################################################
# --- input data

ds = proc_mgr.service(DataStore)
rows = [(it, 'foo{:d}'.format(it), (it + 1) / 2.) for it in range(100)]
ds['df'] = spark.createDataFrame(rows, schema=['index', 'foo', 'bar'])
schema = ds['df'].schema


##########################################################################
# --- now set up the chains and links based on configuration flags

# define function to set number of partitions
def set_num_parts(df, max_num_parts):
    if df.rdd.getNumPartitions() > max_num_parts:
        df = df.repartition(max_num_parts)
    return df

# define function to select rows from list


def filter_list(list_data, min_index):
    return list(filter(lambda r: r[0] >= min_index, list_data))

# define function to select rows in a Pandas data frame


def filter_pd(pd_data, min_index):
    return pd_data[pd_data['index'] >= min_index]


# post-conversion process functions
process_methods = {'df': ['filter', set_num_parts],
                   'rdd': [pyspark.rdd.PipelinedRDD.filter, 'coalesce'],
                   'list': [filter_list],
                   'pd': [filter_pd]}
process_meth_args = {'df': {'filter': ('index > 19',)},
                     'rdd': {pyspark.rdd.PipelinedRDD.filter: (lambda r: r[0] > 19,), 'coalesce': (2,)},
                     'list': {},
                     'pd': {}}
process_meth_kwargs = {'df': {set_num_parts: dict(max_num_parts=2)},
                       'rdd': {},
                       'list': {filter_list: dict(min_index=20)},
                       'pd': {filter_pd: dict(min_index=20)}}

# create chain and data-frame-creator links
chain = proc_mgr.add_chain('Create')
for out_format in process_methods:
    # create data-frame-conversion link
    lnk = spark_analysis.SparkDfConverter(name='df_to_{}_converter'.format(out_format),
                                          read_key='df',
                                          store_key='{}_output'.format(out_format),
                                          schema_key='{}_schema'.format(out_format),
                                          output_format=out_format,
                                          preserve_col_names=False,
                                          process_methods=process_methods[out_format],
                                          process_meth_args=process_meth_args[out_format],
                                          process_meth_kwargs=process_meth_kwargs[out_format])

    # add link to chain
    chain.add_link(lnk)


##########################################################################

log.debug('Done parsing configuration file esk606_convert_spark_df')
