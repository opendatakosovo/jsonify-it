#!/usr/local/bin/python3.1
import pandas as pd
import argparse
import json
from flask import Flask, jsonify, request

# Example URLs: 
# http://localhost:5050/data?file_name=procurement_data&file_type=csv&group_by=2&root_node=Procurement%20Data&sum_field=value&avg_field=overun_%&limit=10
# http://localhost:5050/data?file_name=procurement_data&file_type=csv&group_by=2&Data&limit=10&filter_col=Year%filter_val=2014
# http://localhost:5050/data?file_name=procurement_data&file_type=csv&Data&limit=100&colnames=Fund%20Source,Municipality,Year

#-------------------------------------------
# Routes
#-------------------------------------------
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    intro = "<h1>Welcome to the CSV data API!</h1>"
    intro = intro + "<p>The URL structure for accessing the data is as follows:<br>"
    intro = intro + "/file_name/file_type/group_by/colnames/filter_col/filter_val/limit<br>"
    intro = intro + "Only the file_name, file_type and group_by fields are mandatory.<br>All other fields can be set to 'blank'.</p>"
    return intro

@app.route('/data', methods=['GET'])
def data():
    try:
        file_name = request.args.get('file_name')
        file_type = request.args.get('file_type')
        group_by = int(request.args.get('group_by', 0))
        colnames = request.args.get('colnames', None)
        filter_col = request.args.get('filter_col', None)
        filter_val = request.args.get('filter_val', None)
        limit = request.args.get('limit', None)
        root_node = request.args.get('root_node', "Data")
        name_field = request.args.get('name_field', "name")
        child_field = request.args.get('child_field', "children")
        sum_field = request.args.get('sum_field', None)
        avg_field = request.args.get('avg_field', None)
    
        # Initialize field names
        current_level = 1
     
        filepath = "data/" + file_name + "." + file_type
    
        # Load in csv Dataset
        if file_type == "csv":
            data = pd.read_csv(filepath, header=0, delimiter=",", quoting=1, index_col=0)

        if filter_col is not None and filter_val is not None:
            data = data.loc[data.loc[ : , filter_col].astype(str) == str(filter_val), : ]
        
        if limit is not None:
            data = data[ :int(limit)]

        if avg_field is not None:
            root_avg = data.loc[ : , avg_field].mean()

            # Check if column names were passed and use if able
        if colnames is None:
            total_levels = group_by
            col_names = None
        else: 
            col_names = colnames.split(',')
            total_levels = len(col_names)
    
        # Handle no nesting scenario
        if total_levels == 0:
            array = {name_field: root_node
                    , child_field : data.to_dict(orient = "records")}
        else:
            #Initialize Array
            array = {name_field: root_node
                    , child_field : []
                    }   

            # Begin Recursion
            array = inner_loop(data = data
                , array = array
                , current_level = current_level
                , total_levels  = total_levels
                , nest_cols = col_names
                , name = name_field
                , children = child_field
                , sum_value = sum_field
                , avg_value = avg_field
            )
        
        return jsonify(**array)
        
    except:
        return "<h2>Error</h2><p>Data could not be returned. Please check query and try again.</p>"

#-------------------------------------------
# Recursive Function
#-------------------------------------------
def inner_loop(data, array, current_level, total_levels, nest_cols, name, children, sum_value, avg_value, count_field = True):
    
    #Extract column name
    if nest_cols == None:
        colname = list(data.columns.values)[(current_level - 1)]
    else:
        colname = nest_cols[current_level - 1]   
    
    # Extract Levels for Current Column
    levels = data[colname].drop_duplicates().values.tolist()
    
    #Loop through levels
    i = 0
    for level in levels:
        
        # Create empty children subarray
        array[children].insert(i, {})
        array[children][i][children] = {}
        
        # If further nesting required
        if current_level < total_levels:
            new_level = current_level + 1
            subdata = data.loc[data.loc[ : , colname] == level, : ]
            new_array = {children : []}
            subarray = inner_loop(subdata, new_array, new_level, total_levels, nest_cols, name, children, sum_value, avg_value, count_field)
            array[children][i] = subarray
            
        # Else if all nesting completed
        elif current_level == total_levels:
            other_values = data.loc[data.loc[ : , colname] == level, : ].to_dict(orient = "records")
            array[children][i][children] = other_values
        
        # Add Meta Values for current Level
        array[children][i][name] = level
        if sum_value != None:
            array[children][i][sum_value] = data.loc[data.loc[ : , colname] == level, sum_value].sum()
        if avg_value != None:
            array[children][i][avg_value] = data.loc[data.loc[ : , colname] == level, avg_value].mean()
        if count_field:
            array[children][i]["count"] = len(data.loc[data.loc[ : , colname] == level, ].index)
        
        i += 1
    
    return array


#-------------------------------------------
# Run the App
#-------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5050)
