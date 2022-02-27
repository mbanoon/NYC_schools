# Mohamed Banoon
# SI 649 W22 Individual Project

import pandas as pd
import geopandas as gpd
import altair as alt
import streamlit as st
import json

# title and some directions
st.title("Racial Composition of NYC Public Schools, 2015-16")
st.write("By Mohamed Banoon")
st.sidebar.write("Select method and race, then hover your mouse over the map to see detailed statistics.")

# read the NYC schools file
schools = pd.read_excel("NYC_schools.xlsx", dtype={'zip': str})
schools.drop(schools.columns[0], axis=1, inplace=True)

# make a school abbreviation column for the purpose of annotation
schools['abbv'] = schools.school.apply(lambda x: ' '.join(x.split()[:2]))

# calculater percentages
schools['White/Asian'] = schools['whas'] / schools['total']
schools['Minorities'] = schools['other'] / schools['total']
schools['White'] = schools['white'] / schools['total']
schools['Hispanic'] = schools['hispanic'] / schools['total']
schools['Black'] = schools['black_african'] / schools['total']
schools['Asian'] = schools['asian_pacific_islander'] / schools['total']
schools['Native American'] = schools['native_american_alaskan'] / schools['total']

# add a column to be able to merge with the school district map
schools['schoolDistrict'] = pd.to_numeric(schools['agency'].str[-2:])

# group schools by district and aggregate by sum, then calculate percentages again
districted = schools.groupby(['agency', 'schoolDistrict']).sum().reset_index()
districted['White/Asian'] = districted['whas'] / districted['total']
districted['Minorities'] = districted['other'] / districted['total']
districted['White'] = districted['white'] / districted['total']
districted['Hispanic'] = districted['hispanic'] / districted['total']
districted['Black'] = districted['black_african'] / districted['total']
districted['Asian'] = districted['asian_pacific_islander'] / districted['total']
districted['Native American'] = districted['native_american_alaskan'] / districted['total']

# group schools by zip code and aggregate by sum, then trun the whas% and other% columns into real percentages
zipped = schools.groupby(['zip']).sum().reset_index()
zipped['White/Asian'] = zipped['whas'] / zipped['total']
zipped['Minorities'] = zipped['other'] / zipped['total']
zipped['White'] = zipped['white'] / zipped['total']
zipped['Hispanic'] = zipped['hispanic'] / zipped['total']
zipped['Black'] = zipped['black_african'] / zipped['total']
zipped['Asian'] = zipped['asian_pacific_islander'] / zipped['total']
zipped['Native American'] = zipped['native_american_alaskan'] / zipped['total']

# read the district map json file and convert to gdf
with open('NYC_districts.json') as jsonfile:
    district_json = json.load(jsonfile)
district_gdf = gpd.GeoDataFrame.from_features((district_json))

# merge gdf with districts aggregated by sum and convert back to json
districted_merged = district_gdf.merge(districted, on='schoolDistrict', how='inner')
districted_choro_json = json.loads(districted_merged.to_json())
districted_choro_data = alt.Data(values=districted_choro_json['features'])

# read the zip code map json file and convert to gdf
with open('NYC_zips.json') as jsonfile:
    zip_json = json.load(jsonfile)
zip_gdf = gpd.GeoDataFrame.from_features((zip_json))

# merge gdf with zip codes aggregated by sum and convert back to json
zipped_merged = zip_gdf.merge(zipped, left_on='postalCode', right_on='zip', how='inner')
zipped_choro_json = json.loads(zipped_merged.to_json())
zipped_choro_data = alt.Data(values=zipped_choro_json['features'])

# make a selectbox for method
selectbox1 = st.sidebar.selectbox(label='Select Method', options=['By School District', 'By Zip Code'])

# make another selectbox for race
options = ['properties.White/Asian:Q', 'properties.Minorities:Q', 'properties.White:Q', 'properties.Hispanic:Q', 'properties.Black:Q', 'properties.Asian:Q', 'properties.Native American:Q']
selectbox2 = st.sidebar.selectbox('Select Race', options, format_func=lambda x: x[11:-2])

# add note about minorities
st.sidebar.write('Note that the "Minorities" categroy excludes Asians.')

# make the district choropleth
district_choro = alt.Chart(districted_choro_data).mark_geoshape().encode(
    tooltip=[alt.Tooltip('properties.schoolDistrict:N',
                         title='District No.'),
             alt.Tooltip(selectbox2,
                         title='Share of Selected Race',
                         format=',.2%')],
    color=alt.Color(selectbox2,
                    scale=alt.Scale(scheme='reds'),
                    legend=alt.Legend(title='Share of Selected Race',
                                      format=',.0%'))
).properties(
    title=alt.TitleParams('Data: NCES, BetaNYC',
                          baseline='bottom',
                          orient='bottom',
                          anchor='end',
                          fontWeight='bold',
                          dx=-150,
                          dy=-20,
                          fontSize=15),
    width=1200,
    height=1200
)

# make the zip code choropleth
zip_choro = alt.Chart(zipped_choro_data).mark_geoshape().encode(
    tooltip=[alt.Tooltip('properties.borough:N',
                         title='Borough'),
             alt.Tooltip('properties.zip:N',
                         title='Zip Code'),
             alt.Tooltip(selectbox2,
                         title='Share of Selected Race',
                         format=',.2%')],
    color=alt.Color(selectbox2, 
                    scale=alt.Scale(scheme='reds'),
                    legend=alt.Legend(title='Share of Selected Race',
                                      format=',.0%'))
).properties(
    title=alt.TitleParams('Data: NCES, BetaNYC',
                          baseline='bottom',
                          orient='bottom',
                          anchor='end',
                          fontWeight='bold',
                          dx=-150,
                          dy=-20,
                          fontSize=15),
    width=1200,
    height=1200
)

# make the point chart map that shows schools as dots
points = alt.Chart(schools).mark_point(filled=True).encode(
    longitude='long:Q',
    latitude='lat:Q',
    color=selectbox2[11:],
    tooltip=[alt.Tooltip('school:N'),
             alt.Tooltip(selectbox2[11:],
                         title='Share of Selected Race',
                         format=',.2%')]
).properties(
    title='Data: NCES, BetaNYC'
)

# make the map that annotates PS 8 and PS 307
school_text = alt.Chart(schools).mark_text(
    align='left',
    baseline='bottom',
    fontSize=10,
    dx=-13,
    dy=-2
).encode(
    longitude='long:Q',
    latitude='lat:Q',
    text='abbv:N',
    color=alt.value('yellow')
).transform_filter(
    (alt.datum.school == 'PS 8 ROBERT FULTON') | (alt.datum.school == 'PS 307 DANIEL HALE WILLIAMS')
)

# make the layered district map
district_map = (district_choro + points + school_text).configure(background='#A9A9A9')

# make the layered zip code map
zip_map = (zip_choro + points + school_text).configure(background='#A9A9A9')

# display maps
if selectbox1 == 'By School District':
    district_map
else:
    zip_map