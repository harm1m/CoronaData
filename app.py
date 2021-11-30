import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import requests as rq
import json

st.set_page_config(layout="wide")

# data = pd.read_csv('all_data.csv')

if st.sidebar.button(label = 'getdata'):

    import getdata
    st.session_state['data'] = getdata.data_all
    

# logic
data = st.session_state['data']

data['date'] = pd.to_datetime(data['date'], errors='coerce')

columnlist = data.columns.to_numpy()

data['Maatregelen'] = 0

#Header
header = st.container()
with header:
    st.title('Interactive COVID-19 data')

#Sidebar
maxvalueforslider = len(st.session_state['data']) - 1

start = st.sidebar.slider(label = 'Set start of analysis area', value = 0, max_value = maxvalueforslider)
st.sidebar.write(data.date[start])
end = st.sidebar.slider(label = 'Set end of analysis area', value = maxvalueforslider, max_value = maxvalueforslider)
st.sidebar.write(data.date[end])


data = data.loc[start:end]
#Sidebar -> Selecting y axis, first show options
chart_input = st.sidebar.radio(
    "Select y-axis",
    (columnlist[[1, 2, 3, 4, 5, 11, 12, 13]]))

for item in columnlist[[6, 7, 8, 9, 10]]:
    if st.sidebar.checkbox(str(item)):
        data['Maatregelen'] = data['Maatregelen'] + data[item].astype(int)

#Sidebar -> Selecting y axis, put selected option into parameter
for item in data.columns:
    if chart_input == item:
        YaxisColname = data[item].name
        Yaxis = data[item]

#expandable modelmaker
modelmaker = st.expander(label = 'Model Creator')
with modelmaker:
    degreeOfFit = st.slider('Degree of the fitting polynomial', value = 1, max_value = 5)

model = np.polyfit(np.array(data.index), np.array(Yaxis), degreeOfFit)
predictor = np.poly1d(model)
modelXvalues = np.array(data.index)
modelYvalues = predictor(modelXvalues)

modelderivative = predictor.deriv()
growthfactor = (Yaxis[end]/Yaxis[start])**(1/(end-start))
with modelmaker:
    st.write("The equation for the model produced:")
    st.write(np.poly1d(model))
    st.write("Growth factor")
    # growth factor = endvalue/startvalue^(1/time)
    
    st.write(growthfactor)

if 'phaseholder' not in st.session_state:
        st.session_state['phaseholder'] = pd.DataFrame(columns = ['phase', 'start', 'end', 'growthfactor', 'growthfactor_difference'])

if 'phasecounter' not in st.session_state:
        st.session_state['phasecounter'] = 0

phasecalculator = st.expander(label = 'Phase calculator')
with phasecalculator:
    if st.button(label = 'Add current phase'):
        st.session_state['phasecounter'] = st.session_state['phasecounter'] + 1
        st.session_state['phaseholder'].loc[len(st.session_state['phaseholder'].index)] = [st.session_state['phasecounter'], start, end, growthfactor, 0]
        st.session_state['phaseholder']['growthfactor_difference'] = st.session_state['phaseholder']['growthfactor'].diff()
    if st.button(label = 'Empty table'):
        st.session_state['phaseholder'] = pd.DataFrame(columns = ['phase', 'start', 'end', 'growthfactor', 'growthfactor_difference'])
        st.session_state['phasecounter'] = 0
    st.write(st.session_state['phaseholder'])

    muliplier_low = 0.85
    muliplier_high = 1.15

    st.write("select 5 consecutive phases before uploading to API")
    if st.button(label = 'Upload phases to API'):

        rel_gf_0 = st.session_state['phaseholder'].loc[0, 'growthfactor']
        rel_gf_1 = st.session_state['phaseholder'].loc[1, 'growthfactor_difference']
        rel_gf_2 = st.session_state['phaseholder'].loc[2, 'growthfactor_difference']
        rel_gf_3 = st.session_state['phaseholder'].loc[3, 'growthfactor_difference']
        rel_gf_4 = st.session_state['phaseholder'].loc[4, 'growthfactor_difference']
        rel_gf_5 = st.session_state['phaseholder'].loc[5, 'growthfactor_difference']

        body = {
            "parameters": {
                "gf-phase-0-low": rel_gf_0*muliplier_low,
                "gf-phase-0-high": rel_gf_0*muliplier_high,
                "gf-phase-1-low": rel_gf_1*muliplier_low,
                "gf-phase-1-high": rel_gf_1*muliplier_high,
                "gf-phase-2-low": rel_gf_2*muliplier_low,
                "gf-phase-2-high": rel_gf_2*muliplier_high,
                "gf-phase-3-low": rel_gf_3*muliplier_low,
                "gf-phase-3-high": rel_gf_3*muliplier_high,
                "gf-phase-4-low": rel_gf_4*muliplier_low,
                "gf-phase-4-high": rel_gf_4*muliplier_high,
                "gf-phase-5-low": rel_gf_5*muliplier_low,
                "gf-phase-5-high": rel_gf_5*muliplier_high
            }
        }

        puturl = "https://api.code-ninja.online/update/project/618158a84340e7dfbf25ec81/"

        response = rq.put(
            puturl,
            data=json.dumps(body),
            headers={"Content-Type": "application/json"}
        )

#chart
x = data.date
y = Yaxis
color = data['Maatregelen']

fig = px.scatter(x = x, y = y, color = color,
    labels=dict(x='date', y= YaxisColname, color='Amount of Government measures'),
    width=1300, height=600
    )

xval = np.array(range(1,101))
yval = np.array(range(1, 10000, 100))

with modelmaker:
    if st.checkbox("show model"):
        fig.add_trace(go.Line(x = data.date, y = modelYvalues))

st.plotly_chart(fig, use_container_width=True)