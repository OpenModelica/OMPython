#ifndef oc_latch__H
#define oc_latch__H
#include "meta/meta_modelica.h"
#include "util/modelica.h"
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>

#include "simulation/simulation_runtime.h"
#ifdef __cplusplus
extern "C" {
#endif


DLLExport
modelica_real omc_Modelica_Blocks_Tables_Internal_getNextTimeEvent(threadData_t *threadData, modelica_complex _tableID, modelica_real _timeIn);
DLLExport
modelica_metatype boxptr_Modelica_Blocks_Tables_Internal_getNextTimeEvent(threadData_t *threadData, modelica_metatype _tableID, modelica_metatype _timeIn);
static const MMC_DEFSTRUCTLIT(boxvar_lit_Modelica_Blocks_Tables_Internal_getNextTimeEvent,2,0) {(void*) boxptr_Modelica_Blocks_Tables_Internal_getNextTimeEvent,0}};
#define boxvar_Modelica_Blocks_Tables_Internal_getNextTimeEvent MMC_REFSTRUCTLIT(boxvar_lit_Modelica_Blocks_Tables_Internal_getNextTimeEvent)

extern double ModelicaStandardTables_CombiTimeTable_nextTimeEvent(void * /*_tableID*/, double /*_timeIn*/);


DLLExport
modelica_real omc_Modelica_Blocks_Tables_Internal_getTimeTableTmax(threadData_t *threadData, modelica_complex _tableID);
DLLExport
modelica_metatype boxptr_Modelica_Blocks_Tables_Internal_getTimeTableTmax(threadData_t *threadData, modelica_metatype _tableID);
static const MMC_DEFSTRUCTLIT(boxvar_lit_Modelica_Blocks_Tables_Internal_getTimeTableTmax,2,0) {(void*) boxptr_Modelica_Blocks_Tables_Internal_getTimeTableTmax,0}};
#define boxvar_Modelica_Blocks_Tables_Internal_getTimeTableTmax MMC_REFSTRUCTLIT(boxvar_lit_Modelica_Blocks_Tables_Internal_getTimeTableTmax)

extern double ModelicaStandardTables_CombiTimeTable_maximumTime(void * /*_tableID*/);


DLLExport
modelica_real omc_Modelica_Blocks_Tables_Internal_getTimeTableTmin(threadData_t *threadData, modelica_complex _tableID);
DLLExport
modelica_metatype boxptr_Modelica_Blocks_Tables_Internal_getTimeTableTmin(threadData_t *threadData, modelica_metatype _tableID);
static const MMC_DEFSTRUCTLIT(boxvar_lit_Modelica_Blocks_Tables_Internal_getTimeTableTmin,2,0) {(void*) boxptr_Modelica_Blocks_Tables_Internal_getTimeTableTmin,0}};
#define boxvar_Modelica_Blocks_Tables_Internal_getTimeTableTmin MMC_REFSTRUCTLIT(boxvar_lit_Modelica_Blocks_Tables_Internal_getTimeTableTmin)

extern double ModelicaStandardTables_CombiTimeTable_minimumTime(void * /*_tableID*/);


DLLExport
modelica_real omc_Modelica_Blocks_Tables_Internal_getTimeTableValueNoDer(threadData_t *threadData, modelica_complex _tableID, modelica_integer _icol, modelica_real _timeIn, modelica_real _nextTimeEvent, modelica_real _pre_nextTimeEvent);
DLLExport
modelica_metatype boxptr_Modelica_Blocks_Tables_Internal_getTimeTableValueNoDer(threadData_t *threadData, modelica_metatype _tableID, modelica_metatype _icol, modelica_metatype _timeIn, modelica_metatype _nextTimeEvent, modelica_metatype _pre_nextTimeEvent);
static const MMC_DEFSTRUCTLIT(boxvar_lit_Modelica_Blocks_Tables_Internal_getTimeTableValueNoDer,2,0) {(void*) boxptr_Modelica_Blocks_Tables_Internal_getTimeTableValueNoDer,0}};
#define boxvar_Modelica_Blocks_Tables_Internal_getTimeTableValueNoDer MMC_REFSTRUCTLIT(boxvar_lit_Modelica_Blocks_Tables_Internal_getTimeTableValueNoDer)

extern double ModelicaStandardTables_CombiTimeTable_getValue(void * /*_tableID*/, int /*_icol*/, double /*_timeIn*/, double /*_nextTimeEvent*/, double /*_pre_nextTimeEvent*/);


DLLExport
modelica_complex omc_Modelica_Blocks_Types_ExternalCombiTimeTable_constructor(threadData_t *threadData, modelica_string _tableName, modelica_string _fileName, real_array _table, modelica_real _startTime, integer_array _columns, modelica_integer _smoothness, modelica_integer _extrapolation, modelica_real _shiftTime, modelica_integer _timeEvents, modelica_boolean _verboseRead);
DLLExport
modelica_metatype boxptr_Modelica_Blocks_Types_ExternalCombiTimeTable_constructor(threadData_t *threadData, modelica_metatype _tableName, modelica_metatype _fileName, modelica_metatype _table, modelica_metatype _startTime, modelica_metatype _columns, modelica_metatype _smoothness, modelica_metatype _extrapolation, modelica_metatype _shiftTime, modelica_metatype _timeEvents, modelica_metatype _verboseRead);
static const MMC_DEFSTRUCTLIT(boxvar_lit_Modelica_Blocks_Types_ExternalCombiTimeTable_constructor,2,0) {(void*) boxptr_Modelica_Blocks_Types_ExternalCombiTimeTable_constructor,0}};
#define boxvar_Modelica_Blocks_Types_ExternalCombiTimeTable_constructor MMC_REFSTRUCTLIT(boxvar_lit_Modelica_Blocks_Types_ExternalCombiTimeTable_constructor)

extern void * ModelicaStandardTables_CombiTimeTable_init2(const char* /*_fileName*/, const char* /*_tableName*/, const double* /*_table*/, size_t, size_t, double /*_startTime*/, const int* /*_columns*/, size_t, int /*_smoothness*/, int /*_extrapolation*/, double /*_shiftTime*/, int /*_timeEvents*/, int /*_verboseRead*/);


DLLExport
void omc_Modelica_Blocks_Types_ExternalCombiTimeTable_destructor(threadData_t *threadData, modelica_complex _externalCombiTimeTable);
DLLExport
void boxptr_Modelica_Blocks_Types_ExternalCombiTimeTable_destructor(threadData_t *threadData, modelica_metatype _externalCombiTimeTable);
static const MMC_DEFSTRUCTLIT(boxvar_lit_Modelica_Blocks_Types_ExternalCombiTimeTable_destructor,2,0) {(void*) boxptr_Modelica_Blocks_Types_ExternalCombiTimeTable_destructor,0}};
#define boxvar_Modelica_Blocks_Types_ExternalCombiTimeTable_destructor MMC_REFSTRUCTLIT(boxvar_lit_Modelica_Blocks_Types_ExternalCombiTimeTable_destructor)

extern void ModelicaStandardTables_CombiTimeTable_close(void * /*_externalCombiTimeTable*/);
#include "oc_latch_model.h"


#ifdef __cplusplus
}
#endif
#endif

