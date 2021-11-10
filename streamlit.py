from numpy.lib.type_check import asfarray
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import requests

st.set_page_config(layout="wide")

# data = pd.read_csv('all_data.csv')

if st.sidebar.button(label = 'getdata'):

    url1 = 'https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/country_data/Netherlands.csv'
    data_vaccinatie_original = pd.read_csv(url1, sep = ',', error_bad_lines=False)

    url2 = "https://data.rivm.nl/covid-19/COVID-19_aantallen_gemeente_cumulatief.json"
    data_aantallen_original = pd.read_json(url2)

    url3 = "Maatregelen.csv"
    maatregelen_original = pd.read_csv(url3)

    # stap 2: mergen data bronnen

    maatregelen = maatregelen_original.copy()
    data_aantallen = data_aantallen_original.copy()
    data_vaccinatie = data_vaccinatie_original.copy()

    #data_aantallen wordt gegrouped per datum, alle regios worden bij elkaar opgeteld
    data_aantallen = data_aantallen.groupby(['Date_of_report'])['Total_reported', 'Deceased', 'Hospital_admission'].sum().reset_index()

    #datum wordt een standaard format, namelijk "dag-maand-jaar"
    data_aantallen['Date_of_report'] =  pd.to_datetime(data_aantallen['Date_of_report'])
    data_aantallen['Date_of_report'] = data_aantallen['Date_of_report'].dt.strftime('%d-%m-%Y')
    data_vaccinatie['date'] =  pd.to_datetime(data_vaccinatie['date'])
    data_vaccinatie['date'] = data_vaccinatie['date'].dt.strftime('%d-%m-%Y')
    data_aantallen.rename(columns = {'Date_of_report':'date'}, inplace = True)

    #merge data_vaccinatie en data_aantallen
    data_all = data_aantallen.merge(data_vaccinatie, how='outer')
    #Verwijder nutteloze colommen
    data_all.drop(['total_vaccinations', 'location', 'source_url', 'vaccine', 'total_boosters'], axis=1, inplace=True)

    #Voeg maatregelen toe aan data_all + uniforme datum
    maatregelen['Datum'] =  pd.to_datetime(maatregelen['Datum'])
    maatregelen['Datum'] = maatregelen['Datum'].dt.strftime('%d-%m-%Y')
    maatregelen.rename(columns = {'Datum':'date'}, inplace = True)
    #merge met all_data
    data_all = data_all.merge(maatregelen, how='outer')

    #maatregelen naar true false values 
    data_all.iloc[:,6:] = data_all.iloc[:,6:].notnull().astype(bool)

    #turn daily data into weekly data
    for i in range(len(data_aantallen)):
        if i%7 != 2:
            data_all = data_all.drop(i)

    #drop laatste twee columns
    data_all = data_all.reset_index(drop=True)

    #Set the nan values in vaccine data to 0.0

    data_all['people_fully_vaccinated'] = data_all['people_fully_vaccinated'].fillna(0.0)
    data_all['people_vaccinated'] = data_all['people_vaccinated'].fillna(0.0)

    data_all = data_all.drop([85, 86, 87, 88])

    #Add daily columns instead of total
    data_all['Total_reported_daily'] = data_all['Total_reported'].diff()
    data_all['Deceased_daily'] = data_all['Deceased'].diff()
    data_all['Hospital_admission_daily'] = data_all['Hospital_admission'].diff()
    data_all['date'] = pd.to_datetime(data_all['date'])
    data_all['date'] = data_all['date'].dt.strftime('%d-%m-%Y')

    st.session_state['data'] = data_all
    

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

start = st.sidebar.slider(label = 'Set start of analysis area', value = 0, max_value = len(data))
st.sidebar.write(data.date[start])
end = st.sidebar.slider(label = 'Set end of analysis area', value = 95, max_value = 95)
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