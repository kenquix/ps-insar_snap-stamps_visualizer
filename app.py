import streamlit as st
import scipy.io
import pandas as pd
import numpy as np
import altair as alt
from datetime import date, timedelta, datetime
import plotly.graph_objs as go

st.set_page_config(page_title='PS-InSAR StAMPS Visualizer') #, layout='wide')

@st.cache(ttl=60*60*1)
def read_data(fn, n=100):
	mat = scipy.io.loadmat(fn)
	lonlat = np.hsplit(mat['lonlat'], 2)
	df = pd.DataFrame(mat['ph_mm'], columns=mat['day'].flatten())
	df['lon'] = lonlat[0]
	df['lat'] = lonlat[1]
	df['ave'] = df.iloc[:,0:6].mean(axis=1).apply(lambda x: round(x, 2))
	df = df.reset_index().sample(n)
	df = pd.melt(df, id_vars=['lon', 'lat', 'ave', 'index'], 
		value_vars=[736673, 736841, 737165, 737921, 738185, 738293],
		var_name='Date')
	df.Date = [date(1,1,1) + timedelta(i) - timedelta (367) for i in df.Date]		
	df = df.rename(columns={'index':'ps', 'value': 'Displacement'})
	df['Displacement'] = df['Displacement'].apply(lambda x: round(x, 2))
	return df

def main():
	st.header('PS-InSAR SNAP - StAMPS Visualizer')
	st.markdown(f"""
		A simple web app to visualize the Persistent Scatterers (PS) identified using the [SNAP - StAMPS workflow]
		(https://forum.step.esa.int/t/snap-stamps-workflow-documentation/13985).
		You can **visualize your own data** by uploading the Matlab file *(e.g., 'ps_plot_ts_v-do.mat')*. 
		
		This is inspired by the [StAMPS visualizer based on R](https://forum.step.esa.int/t/stamps-visualizer-snap-stamps-workflow/9613). If you have suggestions on how to improve this, let me know. 
		""")

	st.sidebar.subheader('Customization Panel')
	n = st.slider('Select number of points to plot', min_value=10, max_value=1000)

	inputFile = st.sidebar.file_uploader('Upload a file', type=('mat'))

	if inputFile is None:
		df = read_data('ps_plot_ts_v-do.mat', n)
	else:
		df = read_data(inputFile, n)

	style_dict = {'Carto-Positron':'carto-positron', 'Openstreetmap':'open-street-map', 'Carto Dark':'carto-darkmatter', 
		'Stamen Terrain':'stamen-terrain', 'Stamen Toner':'stamen-toner', 'Stamen Watercolor':'stamen-watercolor'}

	style = st.sidebar.selectbox('Select map style', ['Carto-Positron', 'Openstreetmap', 'Carto Dark', 
		'Stamen Terrain', 'Stamen Toner', 'Stamen Watercolor']) 

	selectdate = st.sidebar.select_slider('Select Date', df.Date.unique().tolist())
	mapbox_df = df[df.Date.isin([selectdate])]

	multiselection = st.sidebar.multiselect('Select PS', df.ps.unique().tolist(), 
		default=df.ps.unique().tolist()[:2])

	filtered_df = df[df['ps'].isin(multiselection)]
	
	with st.beta_expander('Descriptive Statistics'):
		st.text(f'Displacement values (mm/yr) of selected points (n = {len(mapbox_df)})')
		a1, a2, a3 = st.beta_columns(3)
		n = st.slider('Select bin width', min_value=1, max_value=10)
		a1.info(f'Highest: {mapbox_df.ave.max():0.2f}')
		a2.info(f'Lowest: {mapbox_df.ave.min():0.2f}')
		a3.info(f'Average: {mapbox_df.ave.mean():0.2f}')

		altHist = alt.Chart(mapbox_df).mark_bar().encode(
			x=alt.X('ave:Q', bin=alt.Bin(step=n), title='Average Displacement (mm/yr)'),
			y='count()', 
			tooltip=[alt.Tooltip('count()', format=',.0f', title='Count')]
			)

		st.altair_chart(altHist, use_container_width=True)

	data = go.Scattermapbox(name='', lat=mapbox_df.lat, lon=mapbox_df.lon, 
		hovertemplate='%{text} mm/yr', 
		mode='markers',
		marker=dict(size=10, opacity=.8, color=mapbox_df.ave.values, colorscale='YlGnBu',
			colorbar=dict(thicknessmode='pixels', 
				title=dict(text='Displacement (mm/yr)', side='right'))), 
		text=mapbox_df.ave.values) # , selected=dict(marker=dict(color='rgb(255,0,0)', size=14, opacity=.8))
	
	layout = go.Layout(width=950, height=500, 
		mapbox = dict(center= dict(lat=(mapbox_df.lat.max() + mapbox_df.lat.min())/2, 
			lon=(mapbox_df.lon.max() + mapbox_df.lon.min())/2), 
		# accesstoken= token, 
		zoom=10.7,
		style=style_dict[style]), 
		margin=dict(l=0, r=0, t=0, b=0), autosize=True,
		clickmode='event+select')
	
	fig = go.FigureWidget(data=data, layout=layout)

	fig.add_trace(go.Scattermapbox(name='', 
		lat=filtered_df[filtered_df.Date.isin([selectdate])].lat, 
		lon=filtered_df[filtered_df.Date.isin([selectdate])].lon,
		text=filtered_df[filtered_df.Date.isin([selectdate])].ave.values, 
		mode='markers',
		hovertemplate='%{text} mm/yr (Selected)', 
		marker=dict(size=12, color='#B22222', opacity=.8)
		))

	fig.add_trace(go.Scattermapbox(name='', 
		lat=[mapbox_df.iloc[np.argmin(mapbox_df.ave)].lat],
		lon=[mapbox_df.iloc[np.argmin(mapbox_df.ave)].lon],
		mode='markers',
		hovertemplate=f'{mapbox_df.ave.min()} mm/yr (Lowest)', 
		marker=dict(size=12, color='#FF4500', opacity=.8)
		))

	fig.add_trace(go.Scattermapbox(name='', 
		lat=[mapbox_df.iloc[np.argmax(mapbox_df.ave)].lat],
		lon=[mapbox_df.iloc[np.argmax(mapbox_df.ave)].lon],
		mode='markers',
		hovertemplate=f'{mapbox_df.ave.max()} mm/yr (Highest)', 
		marker=dict(size=12, color='#FF4500', opacity=.8)
		))

	st.plotly_chart(fig, use_container_width=True)
	
	# safeguard for empty selection 
	if len(multiselection) == 0:
	    return 

	highlight = alt.selection_single(on='mouseover', fields=['Date'], nearest=True)
	
	def to_altair_datetime(dt):
	    dt = pd.to_datetime(dt) - timedelta(60)
	    return alt.DateTime(year=dt.year, month=dt.month, date=dt.day,
	                        hours=dt.hour, minutes=dt.minute, seconds=dt.second,
	                        milliseconds=0.001 * dt.microsecond)
	
	domain = [to_altair_datetime(df.Date.unique().min() - timedelta(60)), 
			to_altair_datetime(df.Date.unique().max() + timedelta(120))]

	altC = alt.Chart(filtered_df).mark_line(point=True).encode(
		x=alt.X('Date:T', scale=alt.Scale(domain=domain, clamp=True)),
		y=alt.Y('Displacement:Q', title='Displacement (mm)', 
			scale=alt.Scale(domain=[filtered_df.Displacement.min()-5, filtered_df.Displacement.max()+5], 
				clamp=True)), 
		color=alt.Color('ps:N', legend=alt.Legend(title="PS ID")),
		tooltip=[alt.Tooltip('Date:T'), 
				alt.Tooltip('Displacement:Q', format=',.2f', title='Disp')]
				).add_selection(highlight)

	st.altair_chart(altC, use_container_width=True)

	st.sidebar.info("""
		Created by: K. Quisado [Github](https://github.com/kenquix/ps-insar_visualizer)
		""")

if __name__ == '__main__':
	main()