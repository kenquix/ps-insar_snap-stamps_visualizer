# PS-InSAR SNAP-StAMPS Workflow Visualizer

A simple web app to visualize the Persistent Scatterers (PS) identified using the [SNAP - StAMPS workflow](https://forum.step.esa.int/t/snap-stamps-workflow-documentation/13985). You can **visualize your own data** by uploading the Matlab file *(e.g., 'ps_plot_ts_v-do.mat')*. 

This is inspired by the [StAMPS visualizer based on R](https://forum.step.esa.int/t/stamps-visualizer-snap-stamps-workflow/9613). If you have suggestions on how to improve this, let me know. 

Access the web app on [Heroku](https://snap-stamps-visualizer-app.herokuapp.com/) or [Streamlit Share](https://share.streamlit.io/kenquix/ps-insar_snap-stamps_visualizer/main/app.py)

You can run this locally by installing [Anaconda](https://www.anaconda.com/products/individual#download-section). After installing Anaconda, open the **Anaconda command prompt** to create a new virtual environment and install the required libraries.

    conda create -n snap-stamps-viz
    conda activate snap-stamps-viz
    conda install --file requirements.txt
    
 After installing the required libraries, you can run the app in the terminal.
    
    streamlit run app.py
 

