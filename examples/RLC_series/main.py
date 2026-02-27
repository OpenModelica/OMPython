from OMPython import ModelicaSystem
from pathlib import Path
import pandas
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy

def simulate(path_to_output_folder:Path):
	model = ModelicaSystem(
		str(Path(__file__).parent/'RLC_series.mo'), # Path to file where modelica code is.
		'RLC_series', # Name of model from that file.
	)

	model.setParameters(['V_source=1','R=.4','C=1','L=1'])

	path_to_results_file = path_to_output_folder/'data.csv'
	model.setSimulationOptions(['outputFormat=csv', 'stopTime=111'])
	model.simulate(resultfile=str(path_to_results_file))

	print(f'Simulation finished, results available in {path_to_results_file}. ')

	# Get the parameters used in the simulation and compute some analytical values:
	R = float(model.getParameters()['R'])
	L = float(model.getParameters()['L'])
	C = float(model.getParameters()['C'])
	omega_0 = 1/(L*C)**.5
	alpha = R/2/L
	print(f'R={R:.2e}, L={L:.2e}, C={C:.2e}')
	print(f'omega_0 = {omega_0:.2e} rad/s')
	print(f'Oscillation period = {((omega_0**2 - alpha**2)**.5/2/numpy.pi)**-1:.2e} s')
	print(f'Decay time = {1/alpha:.2e} s')

def plot(path_to_output_folder:Path):
	data = pandas.read_csv(path_to_output_folder/'data.csv').set_index('time')
	fig = make_subplots(
		cols = 1,
		rows = len(data.columns),
		shared_xaxes = True,
		vertical_spacing = .02,
	)
	for i,col in enumerate(data):
		fig.add_trace(
			go.Scatter(
				x = data.index,
				y = data[col],
			),
			row = i+1,
			col = 1,
		)
		fig.update_yaxes(
			title_text = col,
			row = i+1,
			col = 1,
		)
	fig.update_xaxes(title_text=data.index.name, row=i+1, col=1)
	fig.update(layout_showlegend=False)
	path_to_plot = path_to_output_folder/'results.html'
	fig.write_html(path_to_plot)
	print(f'Plots available in {path_to_plot}. ')

def main():
	# Create a directory in which to put the simulation results and plots:
	path_to_output_folder = Path(__file__).parent/'simulation_results'
	path_to_output_folder.mkdir(exist_ok=True)
	# Run the simulation:
	simulate(path_to_output_folder=path_to_output_folder)
	# Plot the results:
	plot(path_to_output_folder=path_to_output_folder)

if __name__ == '__main__':
	main()
