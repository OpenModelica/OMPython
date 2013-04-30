2012-03-19 [ganan642@student.liu.se]
--------------------------------------------

- Python 2.7 is required. Download python from http://www.python.org/download/.

- Add python to your PATH.

- Start command prompt/terminal and execute command "python setup.py install". This will add OMPython to the python 3rd party libraries.

- Now OMPython can be used as a library within any Python code that imports the "OMPython" module.

- Use OMPython.run() to test the OpenModelica-Python API Interface with OpenModelica commands.

- Use OMPython.execute("any-OpenModelica-command") to retreive results.

For dictionary results:

	- After the result is available, use OMPython.get	(result_dict,'dotted.notationed.dict.names') to easily 	traverse through the nested dictionaries and retrieve 	specific results.	

	- After the result is available, use OMPython.set	(result_dict,'dotted.notationed.dict.names.new_dict', 	new_dict_value) to easily create a new dictionary(Key 	with 	a value assigned to it inside the nested 	dictionaries.

---------------------------------------------
Adeel, adeel.asghar@liu.se.
Anand, ganan642@student.liu.se