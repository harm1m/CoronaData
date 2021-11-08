import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

st.set_page_config(layout="wide")

# logic
data = pd.read_csv('all_data.csv')
data['date'] = pd.to_datetime(data['date'], errors='coerce')

columnlist = data.columns.to_numpy()

data['Maatregelen'] = 0

#Header
header = st.container()
with header:
    st.title('Interactive COVID-19 data')

#Sidebar
start = st.sidebar.slider(label = 'Set start of analysis area', value = 0, max_value = 86)
st.sidebar.write(data.date[start])
end = st.sidebar.slider(label = 'Set end of analysis area', value = 84, max_value = 84)
st.sidebar.write(data.date[end])

data = data.loc[start:end]
#Sidebar -> Selecting y axis, first show options
chart_input = st.sidebar.radio(
    "Select y-axis",
    (columnlist[[2, 3, 4, 5, 6, 12, 13, 14]]))

for item in columnlist[[7, 8, 9, 10, 11]]:
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
with modelmaker:
    st.write("The equation for the model produced:")
    st.write(np.poly1d(model))
    if model.size == 3:
        st.write("The slope at the end of the exponential period")
        st.write(modelderivative(end))


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