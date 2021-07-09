import streamlit as st
import scipy.io
import pandas as pd
import numpy as np
import altair as alt
from datetime import date, timedelta, datetime
import plotly.graph_objs as go

st.set_page_config(page_title='PS-InSAR StAMPS Visualizer', initial_sidebar_state='expanded') #, layout='wide')

@st.cache()
def read_data(fn, n=100):
	fn = sorted(fn)
	mat = scipy.io.loadmat(fn[0])
	mat1 = scipy.io.loadmat(fn[1])
	lonlat = np.hsplit(mat['lonlat'], 2)
	df = pd.DataFrame(mat['ph_mm'], columns=mat['day'].flatten())
	df['lon'] = lonlat[0]
	df['lat'] = lonlat[1]
	df['ave'] = mat1['ph_disp'].flatten()
	df['ave'] = df['ave'].apply(lambda x: round(x, 2))
	df = df.reset_index().sample(n)
	df = pd.melt(df, id_vars=['lon', 'lat', 'ave', 'index'], var_name='Date')
	df.Date = [date(1,1,1) + timedelta(i) - timedelta(367) for i in df.Date]		
	df = df.rename(columns={'index':'ps', 'value': 'Displacement'})
	df['Displacement'] = df['Displacement'].apply(lambda x: round(x, 2))

	slave_days = mat['day'].flatten()
	master_day = mat['master_day'].flatten()
	days = np.sort(np.append(slave_days, master_day))
	bperp = mat['bperp'].flatten()
	bperp_df = pd.DataFrame({'Date': days, 'Bperp': bperp})
	bperp_df['Day'] = bperp_df.Date.apply(lambda x: 'Slave' if x != int(master_day[0]) else 'Master')
	bperp_df['Temporal'] = bperp_df.Date.apply(lambda x: x - int(master_day[0]))
	bperp_df.Date = [date(1,1,1) + timedelta(i) - timedelta(367) for i in bperp_df.Date]	
	return df, bperp_df, slave_days, master_day

def main():
	st.header('PS-InSAR SNAP - StAMPS Workflow Visualizer')
	st.markdown(f"""
		<p align="justify">A simple web app to visualize the Persistent Scatterers (PS) identified using the
		<a href=https://forum.step.esa.int/t/snap-stamps-workflow-documentation/13985>SNAP - StAMPS workflow </a>. You can <strong>visualize your own data</strong> by uploading the
		Matlab file <strong>(i.e., <font color="#2D8632">'ps_plot_ts_v-do.mat', ps_plot_v-do.mat</font>)</strong> outputs from the SNAP-StAMPS workflow.</p>
		
		<p align="justify">This is inspired by the <a href=https://forum.step.esa.int/t/stamps-visualizer-snap-stamps-workflow/9613>StAMPS visualizer based on R</a>. If you have 
		suggestions on how to improve this, just let me know.</p>
		""", unsafe_allow_html=True)

	with st.beta_expander('Data Points Control Panel', expanded=True):
		inputFile = st.file_uploader('Upload two (2) files (ps_plot_ts_v-do.mat, \
		ps_plot_v-do.mat)', type=('mat'), accept_multiple_files=True, help='Make sure to upload the right files (ps_plot_ts_v-do.mat, ps_plot_v-do.mat) to avoid errors.')
		
		a1, a2 = st.beta_columns((5,3))
		b1, b2 = st.beta_columns((2))

		nmax = a2.number_input('Max points for slider', min_value=10000, max_value=50000, value=10000, help='Adjust the maximum number of points that can be plotted. Range: 10,000-50,000. Default: 10,000')
		n = a1.slider('Select number of points to plot', min_value=100, max_value=nmax, value=5000, help='Defines the number of points to be plotted. Default: 5,000')
		
		if len(inputFile) == 0:
			df, bperp_df, slave_days, master_day = read_data(['ps_plot_ts_v-do.mat', 'ps_plot_v-do.mat'], n)
		else:
			try:
				inputFile = [inputFile[i].name for i in range(2)]
				df, bperp_df, slave_days, master_day = read_data(inputFile, n)
			except:
				st.error('Error: Make sure to upload the correct files: ps_plot_ts_v-do.mat, ps_plot_v-do.mat')
				return

		selectdate = b1.select_slider('Select Date', df.Date.unique().tolist(), value=df.Date.unique().tolist()[3], help='Defines the date to be considered in the plot of PS')
		mapbox_df = df[df.Date.isin([selectdate])]

		multiselection = b2.multiselect('Select PS by ID', sorted(df.ps.unique().tolist()), 
			default=df.ps.unique().tolist()[:5], help="Let user select the PS points by ID. Default: 5 PS points (choosen randomly)")

	filtered_df = df[df['ps'].isin(multiselection)]

	md = date(1,1,1) + timedelta(int(master_day[0])) - timedelta(367)
	with st.beta_expander('Metadata'):
		a1, a2 = st.beta_columns((2))
		a1.info(f'Master Date: {md}')
		a2.info(f'Number of slave images: {len(slave_days)}')
		bperp_chart = alt.Chart(bperp_df).mark_circle(size=72).encode(
			x=alt.X('Temporal:Q', title='Temporal Baseline (days)'), 
			y=alt.Y('Bperp:Q', title='Perpendicular Baseline (m)'), 
			color=alt.Color('Day:N', legend=alt.Legend(title=None, orient='top-right')),
			tooltip=[alt.Tooltip('Day:N', title='Type'),
						alt.Tooltip('Date:T'), 
						alt.Tooltip('Bperp:Q', format='.2f'), 
						alt.Tooltip('Temporal:Q')]
			)

		st.altair_chart(bperp_chart, use_container_width=True)

	st.markdown(f"""<p align="justify">The map below shows the displacement (in mm) of Persistent Scatterers <strong>{selectdate}</strong>.   
			Number of selected PS: <strong>{len(multiselection)}</strong> (<font color="#6DD929">green markers</font>).
			Use the map customization panel to change the appearance of the plots. You can change the color map, 
			base map and size of the markers.</p>
			""", unsafe_allow_html=True)

	with st.beta_expander('Map Customization Panel'):
		m1, m2, m3 = st.beta_columns(3)
		style_dict = {'Carto-Positron':'carto-positron', 'Openstreetmap':'open-street-map', 'Carto Dark':'carto-darkmatter', 
			'Stamen Terrain':'stamen-terrain', 'Stamen Toner':'stamen-toner', 'Stamen Watercolor':'stamen-watercolor'}

		style = m1.selectbox('Select map style', ['Carto-Positron', 'Openstreetmap', 'Carto Dark', 
			'Stamen Terrain', 'Stamen Toner', 'Stamen Watercolor'], index=2) 

		colorscale = m2.selectbox('Select color scale', ['Greys','YlGnBu','Greens','YlOrRd','Bluered','RdBu','Reds','Blues','Picnic',
			'Rainbow','Portland','Jet','Hot','Blackbody','Earth','Electric','Viridis','Cividis'], index=15)

		msize = m3.slider('Select marker size', min_value=2, max_value=15, value=5, step=1)

	mean_los = st.checkbox('Click to plot mean LOS Displacement')

	if mean_los:
		colr = mapbox_df.ave.values
		txt = 'Mean '
		txt1 = '/yr'
	else:
		colr = mapbox_df.Displacement.values
		txt = ''
		txt1 = ''

	data = go.Scattermapbox(name='', lat=mapbox_df.lat, lon=mapbox_df.lon, 
		mode='markers',
		marker=dict(size=msize, opacity=.8, color=colr, colorscale=colorscale, cmid=0,
			colorbar=dict(thicknessmode='pixels', 
				title=dict(text=f'{txt}LOS Displacement (mm{txt1})', side='right'))), 
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
	hover_text = np.stack((mapbox_df.ps.values, 
							colr, 
							mapbox_df.Date.values), axis=1)

	fig.update_traces(customdata=hover_text,
						hovertemplate='<br><b>PS ID</b>: %{customdata[0]}</br>' +\
							'<b>Displacement</b>: %{customdata[1]} mm'+ f'{txt1}')

	filters = filtered_df[filtered_df.Date.isin([selectdate])]
	fig.add_trace(go.Scattermapbox(name='', 
		lat=filters.lat, 
		lon=filters.lon,
		text=filters.ps, 
		mode='markers',
		hovertemplate='<b>PS ID</b>: %{text} (Selected)', 
		marker=dict(size=msize+5, color='#51ED5A')
		))

	st.plotly_chart(fig, use_container_width=True)
	
	# safeguard for empty selection 
	if len(multiselection) == 0:
	    return 
	st.markdown('---')
	filters.reset_index(inplace=True, drop=True)
	filters = filters.rename(columns={'ps': 'PS ID', 'lon':'Longitude', 'lat':'Latitude', 
						'ave': 'Average Disp'})
	filters = filters[['PS ID', 'Latitude', 'Longitude', 'Average Disp']]
	st.markdown(f'<center>Additional information on the selected points (count = {len(multiselection)})</center>', unsafe_allow_html=True)
	st.table(filters)

	highlight = alt.selection_single(on='mouseover', fields=['Date'], nearest=True)
	
	def to_altair_datetime(dt):
	    dt = pd.to_datetime(dt) - timedelta(60)
	    return alt.DateTime(year=dt.year, month=dt.month, date=dt.day,
	                        hours=dt.hour, minutes=dt.minute, seconds=dt.second,
	                        milliseconds=0.001 * dt.microsecond)
	
	domain = [to_altair_datetime(df.Date.unique().min() - timedelta(60)), 
			to_altair_datetime(df.Date.unique().max() + timedelta(120))]

	st.markdown(f"""<center>Time series plot of the selected PS (count: {len(multiselection)})</center>
			""", unsafe_allow_html=True)

	altC = alt.Chart(filtered_df).properties(height=400).mark_line(point=True).encode(
		x=alt.X('Date:T', scale=alt.Scale(domain=domain, clamp=True)),
		y=alt.Y('Displacement:Q', title='Displacement (mm)', 
			scale=alt.Scale(domain=[filtered_df.Displacement.min()-5, filtered_df.Displacement.max()+5], 
				clamp=True)), 
		color=alt.Color('ps:N', legend=alt.Legend(title="PS ID", orient='bottom')),
		tooltip=[alt.Tooltip('Date:T'), 
				alt.Tooltip('Displacement:Q', format=',.2f', title='Disp')]
				).add_selection(highlight).interactive(bind_y=False)
	
	st.altair_chart(altC, use_container_width=True)

	st.markdown(f'Descriptive statistics for displacement values (mm) of selected PS on **{selectdate}** (n = {len(mapbox_df)})')
	c1, c2, c3 = st.beta_columns(3)
	n = st.slider('Select bin width', min_value=1, max_value=10, value=1, help='Adjusts the width of bins. Default: 1 unit')
	c1.info(f'Highest: {mapbox_df.Displacement.max():0.2f}')
	c2.info(f'Lowest: {mapbox_df.Displacement.min():0.2f}')
	c3.info(f'Average: {mapbox_df.Displacement.mean():0.2f}')

	altHist = alt.Chart(mapbox_df).mark_bar().encode(
		x=alt.X('Displacement:Q', bin=alt.Bin(step=n), title='Displacement (mm)'),
		y='count()',
		color=alt.Color('count()', legend=alt.Legend(title='Count', orient='top-left'), scale=alt.Scale(scheme='Redblue')), # )
		tooltip=[alt.Tooltip('count()', format=',.0f', title='Count', bin={'binned':True, 'step':int(f'{n}')})]).interactive(bind_y=False)
	st.markdown(f'<center>Distribution of PS displacements (bins = {n})</center>', unsafe_allow_html=True)
	st.altair_chart(altHist, use_container_width=True)
	st.info("""
		Created by: **K. Quisado** [GitHub](https://github.com/kenquix/ps-insar_visualizer) as part of course project on Microwave RS under the MS
		Geomatics Engineering (Remote Sensing) Program, University of the Philippines - Diliman
		""")

if __name__ == '__main__':
	main()
