/* Linear Systems */
#include "oc_latch_model.h"
#include "oc_latch_12jac.h"
#if defined(__cplusplus)
extern "C" {
#endif

/* linear systems */

/*
equation index: 115
type: SIMPLE_ASSIGN
R1.v = R1.R_actual * R2.i
*/
void oc_latch_eqFunction_115(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,115};
  (data->localData[0]->realVars[2]/* R1.v variable */)  = ((data->localData[0]->realVars[1]/* R1.R_actual variable */) ) * ((data->localData[0]->realVars[5]/* R2.i variable */) );
  TRACE_POP
}
/*
equation index: 116
type: SIMPLE_ASSIGN
R2.v = R2.R_actual * R2.i
*/
void oc_latch_eqFunction_116(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,116};
  (data->localData[0]->realVars[6]/* R2.v variable */)  = ((data->localData[0]->realVars[4]/* R2.R_actual variable */) ) * ((data->localData[0]->realVars[5]/* R2.i variable */) );
  TRACE_POP
}

void residualFunc121(void** dataIn, const double* xloc, double* res, const int* iflag)
{
  TRACE_PUSH
  DATA *data = (DATA*) ((void**)dataIn[0]);
  threadData_t *threadData = (threadData_t*) ((void**)dataIn[1]);
  const int equationIndexes[2] = {1,121};
  ANALYTIC_JACOBIAN* jacobian = NULL;
  (data->localData[0]->realVars[5]/* R2.i variable */)  = xloc[0];
  /* local constraints */
  oc_latch_eqFunction_115(data, threadData);

  /* local constraints */
  oc_latch_eqFunction_116(data, threadData);
  res[0] = (data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */)  + (-(data->localData[0]->realVars[6]/* R2.v variable */) ) - (data->localData[0]->realVars[2]/* R1.v variable */) ;
  TRACE_POP
}
OMC_DISABLE_OPT
void initializeStaticLSData121(void *inData, threadData_t *threadData, void *systemData)
{
  DATA* data = (DATA*) inData;
  LINEAR_SYSTEM_DATA* linearSystemData = (LINEAR_SYSTEM_DATA*) systemData;
  int i=0;
  /* static ls data for R2.i */
  linearSystemData->nominal[i] = data->modelData->realVarsData[5].attribute /* R2.i */.nominal;
  linearSystemData->min[i]     = data->modelData->realVarsData[5].attribute /* R2.i */.min;
  linearSystemData->max[i++]   = data->modelData->realVarsData[5].attribute /* R2.i */.max;
}


/*
equation index: 92
type: SIMPLE_ASSIGN
resistor3.i = resistor2.v / resistor2.R_actual
*/
void oc_latch_eqFunction_92(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,92};
  (data->localData[0]->realVars[52]/* resistor3.i variable */)  = DIVISION_SIM((data->localData[0]->realVars[49]/* resistor2.v variable */) ,(data->localData[0]->realVars[48]/* resistor2.R_actual variable */) ,"resistor2.R_actual",equationIndexes);
  TRACE_POP
}
/*
equation index: 93
type: SIMPLE_ASSIGN
resistor3.v = resistor3.R_actual * resistor3.i
*/
void oc_latch_eqFunction_93(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,93};
  (data->localData[0]->realVars[53]/* resistor3.v variable */)  = ((data->localData[0]->realVars[51]/* resistor3.R_actual variable */) ) * ((data->localData[0]->realVars[52]/* resistor3.i variable */) );
  TRACE_POP
}

void residualFunc98(void** dataIn, const double* xloc, double* res, const int* iflag)
{
  TRACE_PUSH
  DATA *data = (DATA*) ((void**)dataIn[0]);
  threadData_t *threadData = (threadData_t*) ((void**)dataIn[1]);
  const int equationIndexes[2] = {1,98};
  ANALYTIC_JACOBIAN* jacobian = NULL;
  (data->localData[0]->realVars[49]/* resistor2.v variable */)  = xloc[0];
  /* local constraints */
  oc_latch_eqFunction_92(data, threadData);

  /* local constraints */
  oc_latch_eqFunction_93(data, threadData);
  res[0] = (data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */)  + (-(data->localData[0]->realVars[53]/* resistor3.v variable */) ) - (data->localData[0]->realVars[49]/* resistor2.v variable */) ;
  TRACE_POP
}
OMC_DISABLE_OPT
void initializeStaticLSData98(void *inData, threadData_t *threadData, void *systemData)
{
  DATA* data = (DATA*) inData;
  LINEAR_SYSTEM_DATA* linearSystemData = (LINEAR_SYSTEM_DATA*) systemData;
  int i=0;
  /* static ls data for resistor2.v */
  linearSystemData->nominal[i] = data->modelData->realVarsData[49].attribute /* resistor2.v */.nominal;
  linearSystemData->min[i]     = data->modelData->realVarsData[49].attribute /* resistor2.v */.min;
  linearSystemData->max[i++]   = data->modelData->realVarsData[49].attribute /* resistor2.v */.max;
}


/*
equation index: 27
type: SIMPLE_ASSIGN
resistor3.i = resistor3.v / resistor3.R_actual
*/
void oc_latch_eqFunction_27(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,27};
  (data->localData[0]->realVars[52]/* resistor3.i variable */)  = DIVISION_SIM((data->localData[0]->realVars[53]/* resistor3.v variable */) ,(data->localData[0]->realVars[51]/* resistor3.R_actual variable */) ,"resistor3.R_actual",equationIndexes);
  TRACE_POP
}
/*
equation index: 28
type: SIMPLE_ASSIGN
resistor2.v = resistor2.R_actual * resistor3.i
*/
void oc_latch_eqFunction_28(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,28};
  (data->localData[0]->realVars[49]/* resistor2.v variable */)  = ((data->localData[0]->realVars[48]/* resistor2.R_actual variable */) ) * ((data->localData[0]->realVars[52]/* resistor3.i variable */) );
  TRACE_POP
}

void residualFunc33(void** dataIn, const double* xloc, double* res, const int* iflag)
{
  TRACE_PUSH
  DATA *data = (DATA*) ((void**)dataIn[0]);
  threadData_t *threadData = (threadData_t*) ((void**)dataIn[1]);
  const int equationIndexes[2] = {1,33};
  ANALYTIC_JACOBIAN* jacobian = NULL;
  (data->localData[0]->realVars[53]/* resistor3.v variable */)  = xloc[0];
  /* local constraints */
  oc_latch_eqFunction_27(data, threadData);

  /* local constraints */
  oc_latch_eqFunction_28(data, threadData);
  res[0] = (data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */)  + (-(data->localData[0]->realVars[53]/* resistor3.v variable */) ) - (data->localData[0]->realVars[49]/* resistor2.v variable */) ;
  TRACE_POP
}
OMC_DISABLE_OPT
void initializeStaticLSData33(void *inData, threadData_t *threadData, void *systemData)
{
  DATA* data = (DATA*) inData;
  LINEAR_SYSTEM_DATA* linearSystemData = (LINEAR_SYSTEM_DATA*) systemData;
  int i=0;
  /* static ls data for resistor3.v */
  linearSystemData->nominal[i] = data->modelData->realVarsData[53].attribute /* resistor3.v */.nominal;
  linearSystemData->min[i]     = data->modelData->realVarsData[53].attribute /* resistor3.v */.min;
  linearSystemData->max[i++]   = data->modelData->realVarsData[53].attribute /* resistor3.v */.max;
}


/*
equation index: 17
type: SIMPLE_ASSIGN
R2.i = R2.v / R2.R_actual
*/
void oc_latch_eqFunction_17(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,17};
  (data->localData[0]->realVars[5]/* R2.i variable */)  = DIVISION_SIM((data->localData[0]->realVars[6]/* R2.v variable */) ,(data->localData[0]->realVars[4]/* R2.R_actual variable */) ,"R2.R_actual",equationIndexes);
  TRACE_POP
}
/*
equation index: 18
type: SIMPLE_ASSIGN
R1.v = R1.R_actual * R2.i
*/
void oc_latch_eqFunction_18(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,18};
  (data->localData[0]->realVars[2]/* R1.v variable */)  = ((data->localData[0]->realVars[1]/* R1.R_actual variable */) ) * ((data->localData[0]->realVars[5]/* R2.i variable */) );
  TRACE_POP
}

void residualFunc23(void** dataIn, const double* xloc, double* res, const int* iflag)
{
  TRACE_PUSH
  DATA *data = (DATA*) ((void**)dataIn[0]);
  threadData_t *threadData = (threadData_t*) ((void**)dataIn[1]);
  const int equationIndexes[2] = {1,23};
  ANALYTIC_JACOBIAN* jacobian = NULL;
  (data->localData[0]->realVars[6]/* R2.v variable */)  = xloc[0];
  /* local constraints */
  oc_latch_eqFunction_17(data, threadData);

  /* local constraints */
  oc_latch_eqFunction_18(data, threadData);
  res[0] = (data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */)  + (-(data->localData[0]->realVars[6]/* R2.v variable */) ) - (data->localData[0]->realVars[2]/* R1.v variable */) ;
  TRACE_POP
}
OMC_DISABLE_OPT
void initializeStaticLSData23(void *inData, threadData_t *threadData, void *systemData)
{
  DATA* data = (DATA*) inData;
  LINEAR_SYSTEM_DATA* linearSystemData = (LINEAR_SYSTEM_DATA*) systemData;
  int i=0;
  /* static ls data for R2.v */
  linearSystemData->nominal[i] = data->modelData->realVarsData[6].attribute /* R2.v */.nominal;
  linearSystemData->min[i]     = data->modelData->realVarsData[6].attribute /* R2.v */.min;
  linearSystemData->max[i++]   = data->modelData->realVarsData[6].attribute /* R2.v */.max;
}

/* Prototypes for the strict sets (Dynamic Tearing) */

/* Global constraints for the casual sets */
/* function initialize linear systems */
void oc_latch_initialLinearSystem(int nLinearSystems, LINEAR_SYSTEM_DATA* linearSystemData)
{
  /* linear systems */
  assertStreamPrint(NULL, nLinearSystems > 3, "Internal Error: indexlinearSystem mismatch!");
  linearSystemData[3].equationIndex = 121;
  linearSystemData[3].size = 1;
  linearSystemData[3].nnz = 0;
  linearSystemData[3].method = 1;   /* Symbolic Jacobian available */
  linearSystemData[3].residualFunc = residualFunc121;
  linearSystemData[3].strictTearingFunctionCall = NULL;
  linearSystemData[3].analyticalJacobianColumn = oc_latch_functionJacLSJac3_column;
  linearSystemData[3].initialAnalyticalJacobian = oc_latch_initialAnalyticJacobianLSJac3;
  linearSystemData[3].jacobianIndex = 3 /*jacInx*/;
  linearSystemData[3].setA = NULL;  //setLinearMatrixA121;
  linearSystemData[3].setb = NULL;  //setLinearVectorb121;
  linearSystemData[3].initializeStaticLSData = initializeStaticLSData121;
  
  assertStreamPrint(NULL, nLinearSystems > 2, "Internal Error: indexlinearSystem mismatch!");
  linearSystemData[2].equationIndex = 98;
  linearSystemData[2].size = 1;
  linearSystemData[2].nnz = 0;
  linearSystemData[2].method = 1;   /* Symbolic Jacobian available */
  linearSystemData[2].residualFunc = residualFunc98;
  linearSystemData[2].strictTearingFunctionCall = NULL;
  linearSystemData[2].analyticalJacobianColumn = oc_latch_functionJacLSJac2_column;
  linearSystemData[2].initialAnalyticalJacobian = oc_latch_initialAnalyticJacobianLSJac2;
  linearSystemData[2].jacobianIndex = 2 /*jacInx*/;
  linearSystemData[2].setA = NULL;  //setLinearMatrixA98;
  linearSystemData[2].setb = NULL;  //setLinearVectorb98;
  linearSystemData[2].initializeStaticLSData = initializeStaticLSData98;
  
  assertStreamPrint(NULL, nLinearSystems > 1, "Internal Error: indexlinearSystem mismatch!");
  linearSystemData[1].equationIndex = 33;
  linearSystemData[1].size = 1;
  linearSystemData[1].nnz = 0;
  linearSystemData[1].method = 1;   /* Symbolic Jacobian available */
  linearSystemData[1].residualFunc = residualFunc33;
  linearSystemData[1].strictTearingFunctionCall = NULL;
  linearSystemData[1].analyticalJacobianColumn = oc_latch_functionJacLSJac1_column;
  linearSystemData[1].initialAnalyticalJacobian = oc_latch_initialAnalyticJacobianLSJac1;
  linearSystemData[1].jacobianIndex = 1 /*jacInx*/;
  linearSystemData[1].setA = NULL;  //setLinearMatrixA33;
  linearSystemData[1].setb = NULL;  //setLinearVectorb33;
  linearSystemData[1].initializeStaticLSData = initializeStaticLSData33;
  
  assertStreamPrint(NULL, nLinearSystems > 0, "Internal Error: indexlinearSystem mismatch!");
  linearSystemData[0].equationIndex = 23;
  linearSystemData[0].size = 1;
  linearSystemData[0].nnz = 0;
  linearSystemData[0].method = 1;   /* Symbolic Jacobian available */
  linearSystemData[0].residualFunc = residualFunc23;
  linearSystemData[0].strictTearingFunctionCall = NULL;
  linearSystemData[0].analyticalJacobianColumn = oc_latch_functionJacLSJac0_column;
  linearSystemData[0].initialAnalyticalJacobian = oc_latch_initialAnalyticJacobianLSJac0;
  linearSystemData[0].jacobianIndex = 0 /*jacInx*/;
  linearSystemData[0].setA = NULL;  //setLinearMatrixA23;
  linearSystemData[0].setb = NULL;  //setLinearVectorb23;
  linearSystemData[0].initializeStaticLSData = initializeStaticLSData23;
}

#if defined(__cplusplus)
}
#endif

