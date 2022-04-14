# Makefile generated by OpenModelica
# Platform: win64

# Simulations use -O3 by default
CC=clang
CXX=clang++
LINK=clang++ -shared -Xlinker --export-all-symbols
EXEEXT=.exe
DLLEXT=.dll
CFLAGS_BASED_ON_INIT_FILE=
# define OMC_CFLAGS_OPTIMIZATION env variable to your desired optimization level to override this
OMC_CFLAGS_OPTIMIZATION=-Os
DEBUG_FLAGS=$(OMC_CFLAGS_OPTIMIZATION)
CFLAGS=$(CFLAGS_BASED_ON_INIT_FILE) $(DEBUG_FLAGS) -Wno-parentheses-equality -falign-functions -mstackrealign -msse2 -mfpmath=sse ${MODELICAUSERCFLAGS}   
CPPFLAGS= -I"C:/OpenModelica/include/omc/c" -I"C:/OpenModelica/include/omc" -I. -DOPENMODELICA_XML_FROM_FILE_AT_RUNTIME -DOMC_MODEL_PREFIX=oc_latch -DOMC_NUM_MIXED_SYSTEMS=0 -DOMC_NUM_LINEAR_SYSTEMS=4 -DOMC_NUM_NONLINEAR_SYSTEMS=0 -DOMC_NDELAY_EXPRESSIONS=0 -DOMC_NVAR_STRING=0
# define OMC_LDFLAGS_LINK_TYPE env variable to "static" to override this
OMC_LDFLAGS_LINK_TYPE=dynamic
RUNTIME_LIBS= -Wl,-B$(OMC_LDFLAGS_LINK_TYPE) -lSimulationRuntimeC -Wl,-Bdynamic  -Wl,-B$(OMC_LDFLAGS_LINK_TYPE) -lomcgc -lregex -ltre -lintl -liconv -lexpat -static-libgcc -luuid -loleaut32 -lole32 -limagehlp -lws2_32 -llis -lsundials_nvecserial -lsundials_sunmatrixdense -lsundials_sunmatrixsparse -lsundials_sunlinsoldense -lsundials_sunlinsolklu -lsundials_sunlinsollapackdense -lsundials_sunlinsolspbcgs -lsundials_sunlinsolspfgmr -lsundials_sunlinsolspgmr -lsundials_sunlinsolsptfqmr -lsundials_sunnonlinsolnewton -lsundials_cvode -lsundials_cvodes -lsundials_idas -lsundials_kinsol -lumfpack -lklu -lcolamd -lbtf -lamd -lsuitesparseconfig -lipopt -lcoinmumps -lpthread -lm  -lgfortran -lquadmath -lmingw32 -lgcc_eh -lmoldname -lmingwex  -luser32 -lkernel32 -ladvapi32 -lshell32 -lopenblas -lcminpack -Wl,-Bdynamic -lwsock32  -Wl,-B$(OMC_LDFLAGS_LINK_TYPE)  -lstdc++ -Wl,-Bdynamic 
LDFLAGS=-L"C:/OpenModelica/lib//omc" -L"C:/OpenModelica/lib" -Wl,--stack,16777216,-rpath,"C:/OpenModelica/lib//omc" -L"C:/OpenModelica/bin" -Wl,-rpath,"C:/OpenModelica/lib"  -fopenmp -Wl,-Bstatic -lregex -ltre -lintl -liconv -lexpat -lomcgc -lpthread -loleaut32 -limagehlp -lhdf5 -lz -lszip -Wl,-Bdynamic $(RUNTIME_LIBS) 
DIREXTRA=-L"C:/Users/Trista Arinomo/Desktop"
MAINFILE=oc_latch.c
MAINOBJ=oc_latch.o
CFILES=oc_latch_functions.c oc_latch_records.c \
oc_latch_01exo.c oc_latch_02nls.c oc_latch_03lsy.c oc_latch_04set.c oc_latch_05evt.c oc_latch_06inz.c oc_latch_07dly.c \
oc_latch_08bnd.c oc_latch_09alg.c oc_latch_10asr.c oc_latch_11mix.c oc_latch_12jac.c oc_latch_13opt.c oc_latch_14lnz.c \
oc_latch_15syn.c oc_latch_16dae.c oc_latch_17inl.c oc_latch_18spd.c 

OFILES=$(CFILES:.c=.o)
GENERATEDFILES=$(MAINFILE) oc_latch.makefile oc_latch_literals.h oc_latch_functions.h $(CFILES)

.PHONY: omc_main_target clean bundle

# This is to make sure that oc_latch_*.c are always compiled.
.PHONY: $(CFILES)

omc_main_target: $(MAINOBJ) oc_latch_functions.h oc_latch_literals.h $(OFILES)
	$(CC) -I. -o oc_latch$(EXEEXT) $(MAINOBJ) $(OFILES) $(CPPFLAGS) $(DIREXTRA)  "-LC:/OpenModelica/bin/" "-LC:/OpenModelica/lib//omc" "-LC:/OpenModelica/lib/" "-LC:/Users/Trista Arinomo/AppData/Roaming/.openmodelica/binaries/Modelica" "-LC:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Resources/Library/mingw64" "-LC:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Resources/Library/win64" "-LC:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Resources/Library" -lModelicaStandardTables -lModelicaIO -lModelicaMatIO -lzlib $(CFLAGS) $(CPPFLAGS) $(LDFLAGS)
clean:
	@rm -f oc_latch_records.o $(MAINOBJ)

bundle:
	@tar -cvf oc_latch_Files.tar $(GENERATEDFILES)