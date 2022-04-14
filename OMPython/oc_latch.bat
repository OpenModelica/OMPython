@echo off
set PATH=C:/OpenModelica/bin/;C:/OpenModelica/lib//omc;C:/OpenModelica/lib/;C:/Users/Trista Arinomo/AppData/Roaming/.openmodelica/binaries/Modelica;C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Resources/Library/mingw64;C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Resources/Library/win64;C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Resources/Library;;C:/OpenModelica/bin/;%PATH%;
set ERRORLEVEL=
call "%CD%/oc_latch.exe" %*
set RESULT=%ERRORLEVEL%

exit /b %RESULT%
