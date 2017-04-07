# **********************************************************************************
# * Project: Eskapade - A python-based package for data analysis                   *
# * Class  : RecordFactorizer                                                      *
# * Created: 2016/11/08                                                            *
# * Description:                                                                   *
# *      Algorithm to perform the factorization of an input column
# *      of an input dataframe.
# *      E.g. a columnn x with values 'apple', 'tree', 'pear', 'apple', 'pear'
# *      is tranformed into columns x with values 0, 1, 2, 0, 2, etc.
# *                                                                                *
# * Authors:                                                                       *
# *      KPMG Big Data team, Amstelveen, The Netherlands                           *
# *                                                                                *
# * Redistribution and use in source and binary forms, with or without             *
# * modification, are permitted according to the terms listed in the file          *
# * LICENSE.                                                                       *
# **********************************************************************************

import pandas as pd
from pandas import DataFrame
import copy

from eskapade import ProcessManager, Link, StatusCode, DataStore


class RecordFactorizer(Link):
    """Factorize data-frame columns

    Perform factorization of input column of an input dataframe.  E.g. a
    columnn x with values 'apple', 'tree', 'pear', 'apple', 'pear' is
    tranformed into columns x with values 0, 1, 2, 0, 2, etc.
    Resulting dataset stored as new dataset.
    Alternatively, map transformed columns back to orginal format.
    """

    def __init__(self, **kwargs):
        """Initialize RecordFactorizer instance

        Store and do basic check on the attributes of link RecordFactorizer

        :param str read_key: key to read dataframe from the data store. Dataframe of records that is to be transformed.
        :param list columns: list of columns that are to be factorized
        :param bool inplace: replace original columns. Default is False. Overwrites store_key to read_key.
        :param bool convert_all_categories: if true, convert all catergory observables. Default is false.
        :param bool convert_all_booleans: if true, convert all boolean observables. Default is false.
        :param dict map_to_original: dictiorary or key to dictionary to map back factorized columns to original.
                                     map_to_original is a dict of dicts, one dict for each column.
        :param str store_key: store key of output dataFrame. Default is read_key + '_fact'. (optional)
        :param str sk_map_to_original: store key of dictiorary to map factorized columns to original.
                                       Default is 'key' + '_' + store_key + '_to_original'. (optional)
        :param str sk_map_to_factorized: store key of dictiorary to map original to factorized columns.
                                         Default is 'key' + '_' + read_key + '_to_factorized'. (optional)
        """

        Link.__init__(self, kwargs.pop('name', 'RecordFactorizer'))

        # process and register all relevant kwargs. kwargs are added as attributes of the link.
        # second arg is default value for an attribute. key is popped from kwargs.
        self._process_kwargs(kwargs,
                             read_key='',
                             columns=[],
                             convert_all_categories=False,
                             convert_all_booleans=False,
                             store_key='',
                             sk_map_to_original='',
                             sk_map_to_factorized='',
                             map_to_original={},
                             inplace=False)

        # check residual kwargs. exit if any present
        self.check_extra_kwargs(kwargs)

        # map to factorized filled during execution
        self._mtf = {}
        # map to original, dict set below
        self._mto = {}

    def initialize(self):
        """Initialize RecordFactorizer

        Initialize and (further) check the assigned attributes of
        the RecordFactorizer
        """

        self.check_arg_types(read_key=str, store_key=str, sk_map_to_original=str, sk_map_to_factorized=str)
        self.check_arg_types(recurse=True, allow_none=True, columns=str)
        self.check_arg_vals('read_key')

        if self.inplace:
            self.store_key = self.read_key
            self.log().info('store_key has been set to read_key "%s"', self.store_key)

        if not self.store_key:
            self.store_key = self.read_key + '_fact'
            self.log().info('store_key has been set to "%s"', self.store_key)
        if not self.sk_map_to_original:
            self.sk_map_to_original = 'map_' + self.store_key + '_to_original'
            self.log().info('storage key <sk_map_to_original> has been set to "%s"', self.sk_map_to_original)
        if not self.sk_map_to_factorized:
            self.sk_map_to_factorized = 'map_' + self.read_key + '_to_factorized'
            self.log().info('storage key <sk_map_to_factorized> has been set to "%s"', self.sk_map_to_factorized)

        if not self.map_to_original:
            assert isinstance(self.map_to_original,str) or isinstance(self.map_to_original,dict), \
                'map_to_original needs to be a dict or string (to fetch a dict from the datastore)'

        return StatusCode.Success

    def execute(self):
        """Execute RecordFactorizer

        Perform factorization input columns 'columns' of input dataframe.
        Resulting dataset stored as new dataset.
        Alternatively, map transformed columns back to orginal format.
        """

        ds = ProcessManager().service(DataStore)

        # basic checks on contensts of the data frame
        if self.read_key not in ds:
            raise KeyError('Key "%s" not in DataStore' % self.read_key)
        df = ds[self.read_key]
        if not isinstance(df, DataFrame):
            raise TypeError('retrieved object not of type pandas DataFrame')
        if len(df.index) == 0:
            raise AssertionError('dataframe "%s" is empty' % self.read_key)
        for c in self.columns:
            if c not in df.columns:
                raise AssertionError('column "%s" not present in input data frame' % c)
        # convert booleans and categorical observables?
        for c in df.columns:
            if c in self.columns:
                continue
            dt = df[c].dtype
            if issubclass(dt.type,pd.types.dtypes.CategoricalDtypeType) and self.convert_all_categories:
                self.columns.append(c)
            elif dt == 'bool' and self.convert_all_booleans:
                self.columns.append(c)                
        # retrieve map_to_original from ds
        if self.map_to_original:
            if isinstance(self.map_to_original,str):
                assert len(self.map_to_original), 'map_to_original needs to be a filled string.'
                assert self.map_to_original in ds, 'map_to_original key <%s> not found in datastore.'
                self._mto = ds[self.map_to_original]
            elif isinstance(self.map_to_original,dict):
                self._mto = self.map_to_original
            assert isinstance(self._mto,dict), 'map_to_original needs to be a dict'
            
        # 1. do factorization for all specified columns
        if not self.map_to_original:
            df_fact = df if self.inplace else pd.DataFrame(index=df.index)
            for c in self.columns:
                self.log().debug('Factorizing column <%s> of dataframe <%s>' % (c, self.read_key))
                labels, unique = df[c].factorize()
                df_fact[c] = labels
                self._mto[c] = dict((i,v) for i,v in enumerate(unique))
                self._mtf[c] = dict((v,i) for i,v in enumerate(unique))
            # store the mapping here
            ds[self.sk_map_to_original] = self._mto
            ds[self.sk_map_to_factorized] = self._mtf
        # 2. do the mapping back to original format
        else:
            # pandas replace() will not do transformations that are identical, including int 0/1 to bool.
            # skip those column tranformations
            mto = copy.copy(self._mto)
            for c, c_mto in self._mto.items():
                k = list(c_mto.keys())
                v = list(c_mto.values())
                if set(k) & set(v):
                    # true in case of indentical transformation
                    self.log().info('Identical transformation for column <%s>. Skipping column.' % c)
                    del mto[c]
            # refactorizing
            self.log().debug('Refactorizing columns %s of dataframe <%s>' % \
                             (list(mto.keys()), self.read_key))
            df_fact = df.replace(mto, inplace=self.inplace)
            if self.inplace:
                df_fact = df

        # storage
        ds[self.store_key] = df_fact

        return StatusCode.Success
