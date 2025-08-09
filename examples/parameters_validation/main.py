from OMPython import ModelicaSystem
from pathlib import Path

def main(file=None):
	"""Run a simple parameters validation model."""
	model = ModelicaSystem(
		str(Path(__file__).parent/'model.mo'), # Path to file where modelica code is.
		'ParametersValidation', # Name of model from that file.
	)
	# Run the model with different parameters values and print the results:
	for positive_number in [-1,1,.1]:
		for negative_number in [-1,1,-.1]:
			model.setParameters(
				[
					f'positive_number={positive_number}',
					f'negative_number={negative_number}',
				],
			)
			print('--------------------------------------', file=file)
			print(f'model parameters: {model.getParameters()}', file=file)
			try:
				model.simulate() # Parameters values are validated here.
				print('No errors')
				continue
			except Exception as e:
				print(e, file=file)

def test_passing()->bool:
	"""Function to use for automatic testing. If returns `True` it means this example is working."""
	class PrintSilencer:
		def write(s:str):
			pass
	test_passing = False
	try:
		main(file=PrintSilencer())
		test_passing = True
	except Exception as e:
		test_passing = False
	return test_passing

if __name__ == '__main__':
	main()
