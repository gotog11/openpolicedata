from numbers import Number
import numpy as np
import pandas as pd
import re
try:
    from .utils import camel_case_split
except:
    from utils import camel_case_split


class DataMapping:
    def __init__(self, orig_column_name=None, new_column_name = None, data_maps=None, orig_column=None):
        self.orig_column_name = orig_column_name
        self.new_column_name = new_column_name
        self.data_maps = data_maps
        self.orig_value_counts = orig_column.value_counts().head() if orig_column is not None else None

    def __repr__(self, ) -> str:
        return ',\n'.join("%s: %s" % item for item in vars(self).items())
    
    def __eq__(self, other): 
        if not isinstance(other, DataMapping):
            return False
        
        tf_data_maps = self.data_maps == other.data_maps
        if not tf_data_maps:
            if (self.data_maps is None and other.data_maps is not None) or \
                (self.data_maps is not None and other.data_maps is None):
                return False
            if len(self.data_maps)==len(other.data_maps):
                for k in self.data_maps.keys():
                    if k not in other.data_maps and \
                        not (pd.isna(k) and any([pd.isna(x) for x in other.data_maps.keys()])):
                        return False
                    if pd.isnull(k):
                        kother = np.nan
                    else:
                        kother = k
                    if self.data_maps[k] != other.data_maps[kother]:
                        return False
                
                tf_data_maps = True
            elif set(self.data_maps.keys()).symmetric_difference(set(other.data_maps.keys())) == {np.nan}:
                # Adding nan to data maps later
                if (np.nan in other.data_maps and other.data_maps[np.nan]=="UNSPECIFIED") or \
                    (np.nan in self.data_maps and self.data_maps[np.nan]=="UNSPECIFIED"):
                    tf_data_maps = True


        tf_vals = self.orig_value_counts is None and other.orig_value_counts is None
        if not tf_vals:
            tf_vals = self.orig_value_counts.equals(other.orig_value_counts)
            if not tf_vals and other.orig_value_counts.index.dtype=="int64" and all([x.isdigit() for x in self.orig_value_counts.index if isinstance(x,str)]):
                # Found a case where indices were numeric strings but read back in as numbers
                other.orig_value_counts.index = [str(x) for x in other.orig_value_counts.index]
                tf_vals = self.orig_value_counts.equals(other.orig_value_counts)
            if not tf_vals and len(self.orig_value_counts)==len(other.orig_value_counts) and \
                all(self.orig_value_counts.values == other.orig_value_counts.values):
                tf_vals = True
                for x,y in zip(self.orig_value_counts.index, other.orig_value_counts.index):
                    # Difference of trailing 0 is OK
                    if x!=y:
                        if isinstance(x,str) and isinstance(y,str) and (x=="0"+y or y=="0"+x):
                            continue
                        elif isinstance(x,str) and x.isdigit() and isinstance(y,Number) and float(x)==y:
                            continue
                        elif isinstance(y,str) and x.isdigit() and isinstance(x,Number) and float(y)==x:
                            continue
                        tf_vals = False
                        
        tf = self.orig_column_name == other.orig_column_name and \
            self.new_column_name == other.new_column_name and \
            tf_data_maps and tf_vals

        return tf


def check_column(col_name, col_types):
    if isinstance(col_types, str):
        col_types = [col_types]

    for col_type in col_types:
        col_type = col_type.lower()

        # Check for unambiguous column names
        if col_name.lower()==col_type:
            return True

        # Check if column name is a descriptive term + race
        # sus has been used as shorthand for suspect
        # ofc has been used as shorthand for officer
        desc_terms = ["citizen","subject","suspect", "sus", "civilian", "complainant", "person", "cit",
                      "offender", "officer", "ofc", "deputy", "off"]

        if any([col_name.lower()==x+col_type or col_name.lower()==col_type+x for x in desc_terms]):
            return True
        
        words = set(re.split(r"[^A-Za-z]+", col_name.lower()))
        if any([{x,col_type}.issubset(words) for x in desc_terms]):
            return True

        words = set(camel_case_split(col_name))
        if any([{x,col_type}.issubset(words) for x in desc_terms]):
            return True
    
    return False
    