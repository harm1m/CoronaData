#Importeer libraries, pandas is nodig voor bewerkingen dataframes
import pandas as pd
#math wordt gebruikt om nan values (lege values) te vinden in 't dataframe
import math
#voor API interactie
import requests

#Ophalen databronnen
url1 = 'https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/country_data/Netherlands.csv'
data_vaccinatie_original = pd.read_csv(url1, sep = ',', error_bad_lines=False)

url2 = "https://data.rivm.nl/covid-19/COVID-19_aantallen_gemeente_cumulatief.json"
data_aantallen_original = pd.read_json(url2)

#databron hieronder is gemaakt door Job Bude
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

data_all.loc[0:50, 'people_fully_vaccinated'] = data_all.loc[0:50, 'people_fully_vaccinated'].fillna(0.0)
data_all.loc[0:50, 'people_vaccinated'] = data_all.loc[0:50, 'people_vaccinated'].fillna(0.0)

#Add daily increase columns
data_all['Total_reported_daily'] = data_all['Total_reported'].diff()
data_all['Deceased_daily'] = data_all['Deceased'].diff()
data_all['Hospital_admission_daily'] = data_all['Hospital_admission'].diff()

#zet correcte datetime voor 'date' column
data_all['date'] = pd.to_datetime(data_all['date'])
data_all['date'] = data_all['date'].dt.strftime('%d-%m-%Y')

#gooi rijen weg met 'na' 
data_all = data_all.dropna(subset = ["Total_reported"]) 