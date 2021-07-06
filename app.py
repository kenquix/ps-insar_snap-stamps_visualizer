import streamlit as st
import scipy.io
import pandas as pd
import numpy as np
import altair as alt
from datetime import date, timedelta, datetime
import plotly.graph_objs as go

st.set_page_config(page_title='PS-InSAR StAMPS Visualizer', initial_sidebar_state='expanded') #, layout='wide')

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
		value_vars=df.columns[1:-3].tolist(),
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

	style_dict = {'Carto-Positron':'carto-positron', 'Openstreetmap':'open-street-map', 'Carto Dark':'carto-darkmatter', 
		'Stamen Terrain':'stamen-terrain', 'Stamen Toner':'stamen-toner', 'Stamen Watercolor':'stamen-watercolor'}

	style = st.sidebar.selectbox('Select map style', ['Carto-Positron', 'Openstreetmap', 'Carto Dark', 
		'Stamen Terrain', 'Stamen Toner', 'Stamen Watercolor'], index=2) 

	colorscale = st.sidebar.selectbox('Select color scale', ['Greys','YlGnBu','Greens','YlOrRd','Bluered','RdBu','Reds','Blues','Picnic',
		'Rainbow','Portland','Jet','Hot','Blackbody','Earth','Electric','Viridis','Cividis'], index=4)

	msize = st.sidebar.slider('Select marker size', min_value=2, max_value=15, value=5, step=1)
	with st.beta_expander('Control Panel', expanded=True):
		inputFile = st.file_uploader('Upload a file', type=('mat'))

		a1, a2 = st.beta_columns((5,3))
		b1, b2 = st.beta_columns((2))

		nmax = a2.number_input('Configure number of points to plot', min_value=100, max_value=50000, value=10000)
		n = a1.slider('Select number of points to plot', min_value=100, max_value=nmax, value=5000)
		
		if inputFile is None:
			df = read_data('ps_plot_ts_v-do.mat', n)
		else:
			df = read_data(inputFile, n)
		
		selectdate = b1.select_slider('Select Date', df.Date.unique().tolist(), value=df.Date.unique().tolist()[3])
		mapbox_df = df[df.Date.isin([selectdate])]

		multiselection = b2.multiselect('Select PS by ID', sorted(df.ps.unique().tolist()), 
			default=df.ps.unique().tolist()[:2])

	filtered_df = df[df['ps'].isin(multiselection)]

	with st.beta_expander('Descriptive Statistics'):
		st.markdown(f'Displacement values (mm) of selected points on **{selectdate}** (n = {len(mapbox_df)})')
		c1, c2, c3 = st.beta_columns(3)
		n = st.slider('Select bin width', min_value=1, max_value=10, value=1)
		c1.info(f'Highest: {mapbox_df.Displacement.max():0.2f}')
		c2.info(f'Lowest: {mapbox_df.Displacement.min():0.2f}')
		c3.info(f'Average: {mapbox_df.Displacement.mean():0.2f}')

		altHist = alt.Chart(mapbox_df).mark_bar().encode(
			x=alt.X('Displacement:Q', bin=alt.Bin(step=n), title='Displacement (mm)'),
			y='count()',
			color=alt.Color('count()', legend=None), # scale=alt.Scale(scheme='Pastel2')
			tooltip=[alt.Tooltip('count()', format=',.0f', title='Count')])

		st.altair_chart(altHist, use_container_width=True)
	
	st.markdown(f"""The map below shows the displacement (in mm) of Persistent Scatterers **{selectdate}**.   
			Number of selected PS: **{len(multiselection)}** (<font color="#6DD929">green markers</font>)
			""", unsafe_allow_html=True)

	data = go.Scattermapbox(name='', lat=mapbox_df.lat, lon=mapbox_df.lon, 
		mode='markers',
		marker=dict(size=msize, opacity=.8, color=mapbox_df.Displacement.values, colorscale=colorscale,
			colorbar=dict(thicknessmode='pixels', 
				title=dict(text='Displacement (mm)', side='right'))), 
		) # , selected=dict(marker=dict(color='rgb(255,0,0)', size=msize, opacity=.8))

	layout = go.Layout(width=950, height=500, 
		mapbox = dict(center= dict(lat=(mapbox_df.lat.max() + mapbox_df.lat.min())/2, 
			lon=(mapbox_df.lon.max() + mapbox_df.lon.min())/2), 
		# accesstoken= token, 
		zoom=10.7,
		style=style_dict[style]), 
		margin=dict(l=0, r=0, t=0, b=0), autosize=True,
		clickmode='event+select')
	
	fig = go.FigureWidget(data=data, layout=layout)
	
	hover_text = np.stack((mapbox_df.ps.values, mapbox_df.Displacement.values), axis=1)

	fig.update_traces(customdata=hover_text,
						hovertemplate='<b>PS ID</b>: %{customdata[0]}' +\
							'<br><b>Displacement</b>: %{customdata[1]} mm</br>')

	filters = filtered_df[filtered_df.Date.isin([selectdate])]
	fig.add_trace(go.Scattermapbox(name='', 
		lat=filters.lat, 
		lon=filters.lon,
		text=filters.ps, 
		mode='markers',
		hovertemplate='<b>PS ID</b>: %{text} (Selected)', 
		marker=dict(size=msize+5, color='#57FF76')
		))

	st.plotly_chart(fig, use_container_width=True)
	
	# safeguard for empty selection 
	if len(multiselection) == 0:
	    return 
	st.markdown('---')
	highlight = alt.selection_single(on='mouseover', fields=['Date'], nearest=True)
	
	def to_altair_datetime(dt):
	    dt = pd.to_datetime(dt) - timedelta(60)
	    return alt.DateTime(year=dt.year, month=dt.month, date=dt.day,
	                        hours=dt.hour, minutes=dt.minute, seconds=dt.second,
	                        milliseconds=0.001 * dt.microsecond)
	
	domain = [to_altair_datetime(df.Date.unique().min() - timedelta(60)), 
			to_altair_datetime(df.Date.unique().max() + timedelta(120))]

	st.markdown(f"""<center>Time series plot for the selected PS (count: {len(multiselection)})</center>
			""", unsafe_allow_html=True)

	altC = alt.Chart(filtered_df).properties(height=400).mark_line(point=True).encode(
		x=alt.X('Date:T', scale=alt.Scale(domain=domain, clamp=True)),
		y=alt.Y('Displacement:Q', title='Displacement (mm)', 
			scale=alt.Scale(domain=[filtered_df.Displacement.min()-5, filtered_df.Displacement.max()+5], 
				clamp=True)), 
		color=alt.Color('ps:N', legend=alt.Legend(title="PS ID", orient='bottom')),
		tooltip=[alt.Tooltip('Date:T'), 
				alt.Tooltip('Displacement:Q', format=',.2f', title='Disp')]
				).add_selection(highlight)

	st.altair_chart(altC, use_container_width=True)

	st.sidebar.info("""
		Created by: K. Quisado [Github](https://github.com/kenquix/ps-insar_visualizer)
		""")

if __name__ == '__main__':
	main()