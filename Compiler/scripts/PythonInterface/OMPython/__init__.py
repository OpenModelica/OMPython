# -*- coding: cp1252 -*-
"""
  This file is part of OpenModelica.
 
  Copyright (c) 1998-CurrentYear, Open Source Modelica Consortium (OSMC),
  c/o Linköpings universitet, Department of Computer and Information Science,
  SE-58183 Linköping, Sweden.
 
  All rights reserved.
 
  THIS PROGRAM IS PROVIDED UNDER THE TERMS OF GPL VERSION 3 LICENSE OR 
  THIS OSMC PUBLIC LICENSE (OSMC-PL) VERSION 1.2. 
  ANY USE, REPRODUCTION OR DISTRIBUTION OF THIS PROGRAM CONSTITUTES RECIPIENT'S ACCEPTANCE
  OF THE OSMC PUBLIC LICENSE OR THE GPL VERSION 3, ACCORDING TO RECIPIENTS CHOICE. 
 
  The OpenModelica software and the Open Source Modelica
  Consortium (OSMC) Public License (OSMC-PL) are obtained
  from OSMC, either from the above address,
  from the URLs: http://www.ida.liu.se/projects/OpenModelica or  
  http://www.openmodelica.org, and in the OpenModelica distribution. 
  GNU version 3 is obtained from: http://www.gnu.org/copyleft/gpl.html.
 
  This program is distributed WITHOUT ANY WARRANTY; without
  even the implied warranty of  MERCHANTABILITY or FITNESS
  FOR A PARTICULAR PURPOSE, EXCEPT AS EXPRESSLY SET FORTH
  IN THE BY RECIPIENT SELECTED SUBSIDIARY LICENSE CONDITIONS OF OSMC-PL.
 
  See the full OSMC Public License conditions for more details.

  Author : Anand Kalaiarasi Ganeson, ganan642@student.liu.se, 2012-03-14
  Version: 1.0 (Beta)
"""
 
import sys
import os
import time

if sys.platform == 'win32':
  omhome = os.environ['OPENMODELICAHOME']
  # add OPENMODELICAHOME\lib to PYTHONPATH so python can load omniORB libraries
  sys.path.append(os.path.join(omhome, 'share', 'omc', 'scripts', 'PythonInterface', 'stubs'))
  sys.path.append(os.path.join(omhome, 'lib'))
  # add OPENMODELICAHOME\bin to path so python can find the omniORB binaries
  pathVar = os.getenv('PATH')
  pathVar += ';'
  pathVar += os.path.join(omhome, 'bin')
  os.putenv('PATH', pathVar)
else:
  import OMConfig
  omhome = OMConfig.DEFAULT_OPENMODELICAHOME
  # add OPENMODELICAHOME\lib to PYTHONPATH so python can load omniORB libraries
  sys.path.append(os.path.join(OMConfig.DEFAULT_OPENMODELICAHOME, 'share', 'omc', 'scripts', 'PythonInterface', 'stubs'))

from subprocess import Popen, PIPE
from collections import OrderedDict
from datetime import datetime
from omniORB import CORBA

# import the skeletons for the global module
import _GlobalIDL

# import the parse module
import OMParser

# Randomize the IOR file name
random_string = str(datetime.now())
random_string = ''.join(e for e in random_string if e.isalnum())

# Run the server
ompath = os.path.join(omhome, 'bin', 'omc') + " +d=interactiveCorba" + " +c=" + random_string
server = Popen(ompath, shell=True, stdout=PIPE).stdout

# Locating and using the IOR
import tempfile
temp = tempfile.gettempdir()
if sys.platform == 'win32':
  ior_file = "openmodelica.objid." + random_string
else:
  currentUser = os.environ['USER']
  if currentUser == '':
    currentUser = "nobody"
  ior_file = "openmodelica." + currentUser + ".objid." + random_string
ior_file = os.path.join(temp, ior_file)
omc_corba_uri= "file:///" + ior_file

# Wait for the server to start
ticks = 0
while False == os.path.isfile(ior_file):
  if ticks == 5:
    break
  ticks += 1
  time.sleep(1.0)

#initialize the ORB with maximum size for the ORB set
sys.argv.append("-ORBgiopMaxMsgSize")
sys.argv.append("2147483647")
orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)

# See if the omc server is running
if os.path.isfile(ior_file):
  print "OMC Server is up and running at " + omc_corba_uri + "\n"
else:
  print "OMC Server is down. Please start it! Exiting...\n"
  sys.exit(2)

# Read the IOR file
objid_file=open(ior_file)
ior = objid_file.readline()
objid_file.close()

# Find the root POA
poa = orb.resolve_initial_references("RootPOA")

# Convert the IOR into an object reference
obj = orb.string_to_object(ior)

# Narrow the reference to the OmcCommunication object
omc = obj._narrow(_GlobalIDL.OmcCommunication)

# Check if we are using the right object
if omc is None:
        print "Object reference is not valid"
        sys.exit(1)

# Invoke the sendExpression operation to send text commands to the server
def send_command(command):
        if command == "quit()":
                omc.sendExpression("quit()")
                print "OMC has been Shutdown\n"
                sys.exit(1)
        else:
                result = omc.sendExpression(command)
                if result[0] == "\"":
                        return result
                else:
                        ############## Temporary Bug Fix #####################################################################################################
                        if "(R_actual = R*(1 + alpha*(T_heatPort - T_ref))" in result:
                                result = result.replace("(R_actual = R*(1 + alpha*(T_heatPort - T_ref))","(R_actual = R*(1 + alpha*(T_heatPort - T_ref)))")
                        ####################################################################################################################################
                        answer = OMParser.check_for_values(result)
                        OMParser.result = {}                       # Clearing the previous results
                        return answer
        
def run():
        omc_running = True
        while omc_running:
                command = raw_input("\n>>")
                if command == "quit()":
                        omc.sendExpression("quit()")
                        print "OMC has been Shutdown\n"
                        omc_running = False
                        sys.exit(1)
                else:
                        result = omc.sendExpression(command)
                        if result[0] == "\"":
                                print result
                        else:
                                ############## Temporary Bug Fix #####################################################################################################
                                if "(R_actual = R*(1 + alpha*(T_heatPort - T_ref))" in result:
                                        result = result.replace("(R_actual = R*(1 + alpha*(T_heatPort - T_ref))","(R_actual = R*(1 + alpha*(T_heatPort - T_ref)))")
                                ####################################################################################################################################
                                answer = OMParser.check_for_values(result)
                                OMParser.result = {}                       # Clearing the previous results
                                print answer

if __name__ == "__main__":
        run()
