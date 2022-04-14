/* Jacobians 9 */
#include "oc_latch_model.h"
#include "oc_latch_12jac.h"
/* constant equations */
/* dynamic equations */

/*
equation index: 20
type: SIMPLE_ASSIGN
R2.i.$pDERLSJac0.dummyVarLSJac0 = R2.v.SeedLSJac0 / R2.R_actual
*/
void oc_latch_eqFunction_20(DATA *data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  const int baseClockIndex = 0;
  const int subClockIndex = 0;
  const int equationIndexes[2] = {1,20};
  jacobian->tmpVars[0] /* R2.i.$pDERLSJac0.dummyVarLSJac0 JACOBIAN_DIFF_VAR */ = DIVISION(jacobian->seedVars[0] /* R2.v.SeedLSJac0 SEED_VAR */,(data->localData[0]->realVars[4]/* R2.R_actual variable */) ,"R2.R_actual");
  TRACE_POP
}

/*
equation index: 21
type: SIMPLE_ASSIGN
R1.v.$pDERLSJac0.dummyVarLSJac0 = R1.R_actual * R2.i.$pDERLSJac0.dummyVarLSJac0
*/
void oc_latch_eqFunction_21(DATA *data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  const int baseClockIndex = 0;
  const int subClockIndex = 1;
  const int equationIndexes[2] = {1,21};
  jacobian->tmpVars[1] /* R1.v.$pDERLSJac0.dummyVarLSJac0 JACOBIAN_DIFF_VAR */ = ((data->localData[0]->realVars[1]/* R1.R_actual variable */) ) * (jacobian->tmpVars[0] /* R2.i.$pDERLSJac0.dummyVarLSJac0 JACOBIAN_DIFF_VAR */);
  TRACE_POP
}

/*
equation index: 22
type: SIMPLE_ASSIGN
$res_LSJac0_1.$pDERLSJac0.dummyVarLSJac0 = (-R2.v.SeedLSJac0) - R1.v.$pDERLSJac0.dummyVarLSJac0
*/
void oc_latch_eqFunction_22(DATA *data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  const int baseClockIndex = 0;
  const int subClockIndex = 2;
  const int equationIndexes[2] = {1,22};
  jacobian->resultVars[0] /* $res_LSJac0_1.$pDERLSJac0.dummyVarLSJac0 JACOBIAN_VAR */ = (-jacobian->seedVars[0] /* R2.v.SeedLSJac0 SEED_VAR */) - jacobian->tmpVars[1] /* R1.v.$pDERLSJac0.dummyVarLSJac0 JACOBIAN_DIFF_VAR */;
  TRACE_POP
}

OMC_DISABLE_OPT
int oc_latch_functionJacLSJac0_constantEqns(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH

  DATA* data = ((DATA*)inData);
  int index = oc_latch_INDEX_JAC_LSJac0;
  
  
  TRACE_POP
  return 0;
}

int oc_latch_functionJacLSJac0_column(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH

  DATA* data = ((DATA*)inData);
  int index = oc_latch_INDEX_JAC_LSJac0;
  oc_latch_eqFunction_20(data, threadData, jacobian, parentJacobian);
  oc_latch_eqFunction_21(data, threadData, jacobian, parentJacobian);
  oc_latch_eqFunction_22(data, threadData, jacobian, parentJacobian);
  TRACE_POP
  return 0;
}
/* constant equations */
/* dynamic equations */

/*
equation index: 30
type: SIMPLE_ASSIGN
resistor3.i.$pDERLSJac1.dummyVarLSJac1 = resistor3.v.SeedLSJac1 / resistor3.R_actual
*/
void oc_latch_eqFunction_30(DATA *data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  const int baseClockIndex = 0;
  const int subClockIndex = 0;
  const int equationIndexes[2] = {1,30};
  jacobian->tmpVars[0] /* resistor3.i.$pDERLSJac1.dummyVarLSJac1 JACOBIAN_DIFF_VAR */ = DIVISION(jacobian->seedVars[0] /* resistor3.v.SeedLSJac1 SEED_VAR */,(data->localData[0]->realVars[51]/* resistor3.R_actual variable */) ,"resistor3.R_actual");
  TRACE_POP
}

/*
equation index: 31
type: SIMPLE_ASSIGN
resistor2.v.$pDERLSJac1.dummyVarLSJac1 = resistor2.R_actual * resistor3.i.$pDERLSJac1.dummyVarLSJac1
*/
void oc_latch_eqFunction_31(DATA *data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  const int baseClockIndex = 0;
  const int subClockIndex = 1;
  const int equationIndexes[2] = {1,31};
  jacobian->tmpVars[1] /* resistor2.v.$pDERLSJac1.dummyVarLSJac1 JACOBIAN_DIFF_VAR */ = ((data->localData[0]->realVars[48]/* resistor2.R_actual variable */) ) * (jacobian->tmpVars[0] /* resistor3.i.$pDERLSJac1.dummyVarLSJac1 JACOBIAN_DIFF_VAR */);
  TRACE_POP
}

/*
equation index: 32
type: SIMPLE_ASSIGN
$res_LSJac1_1.$pDERLSJac1.dummyVarLSJac1 = (-resistor3.v.SeedLSJac1) - resistor2.v.$pDERLSJac1.dummyVarLSJac1
*/
void oc_latch_eqFunction_32(DATA *data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  const int baseClockIndex = 0;
  const int subClockIndex = 2;
  const int equationIndexes[2] = {1,32};
  jacobian->resultVars[0] /* $res_LSJac1_1.$pDERLSJac1.dummyVarLSJac1 JACOBIAN_VAR */ = (-jacobian->seedVars[0] /* resistor3.v.SeedLSJac1 SEED_VAR */) - jacobian->tmpVars[1] /* resistor2.v.$pDERLSJac1.dummyVarLSJac1 JACOBIAN_DIFF_VAR */;
  TRACE_POP
}

OMC_DISABLE_OPT
int oc_latch_functionJacLSJac1_constantEqns(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH

  DATA* data = ((DATA*)inData);
  int index = oc_latch_INDEX_JAC_LSJac1;
  
  
  TRACE_POP
  return 0;
}

int oc_latch_functionJacLSJac1_column(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH

  DATA* data = ((DATA*)inData);
  int index = oc_latch_INDEX_JAC_LSJac1;
  oc_latch_eqFunction_30(data, threadData, jacobian, parentJacobian);
  oc_latch_eqFunction_31(data, threadData, jacobian, parentJacobian);
  oc_latch_eqFunction_32(data, threadData, jacobian, parentJacobian);
  TRACE_POP
  return 0;
}
/* constant equations */
/* dynamic equations */

/*
equation index: 95
type: SIMPLE_ASSIGN
resistor3.i.$pDERLSJac2.dummyVarLSJac2 = resistor2.v.SeedLSJac2 / resistor2.R_actual
*/
void oc_latch_eqFunction_95(DATA *data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  const int baseClockIndex = 0;
  const int subClockIndex = 0;
  const int equationIndexes[2] = {1,95};
  jacobian->tmpVars[0] /* resistor3.i.$pDERLSJac2.dummyVarLSJac2 JACOBIAN_DIFF_VAR */ = DIVISION(jacobian->seedVars[0] /* resistor2.v.SeedLSJac2 SEED_VAR */,(data->localData[0]->realVars[48]/* resistor2.R_actual variable */) ,"resistor2.R_actual");
  TRACE_POP
}

/*
equation index: 96
type: SIMPLE_ASSIGN
resistor3.v.$pDERLSJac2.dummyVarLSJac2 = resistor3.R_actual * resistor3.i.$pDERLSJac2.dummyVarLSJac2
*/
void oc_latch_eqFunction_96(DATA *data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  const int baseClockIndex = 0;
  const int subClockIndex = 1;
  const int equationIndexes[2] = {1,96};
  jacobian->tmpVars[1] /* resistor3.v.$pDERLSJac2.dummyVarLSJac2 JACOBIAN_DIFF_VAR */ = ((data->localData[0]->realVars[51]/* resistor3.R_actual variable */) ) * (jacobian->tmpVars[0] /* resistor3.i.$pDERLSJac2.dummyVarLSJac2 JACOBIAN_DIFF_VAR */);
  TRACE_POP
}

/*
equation index: 97
type: SIMPLE_ASSIGN
$res_LSJac2_1.$pDERLSJac2.dummyVarLSJac2 = (-resistor3.v.$pDERLSJac2.dummyVarLSJac2) - resistor2.v.SeedLSJac2
*/
void oc_latch_eqFunction_97(DATA *data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  const int baseClockIndex = 0;
  const int subClockIndex = 2;
  const int equationIndexes[2] = {1,97};
  jacobian->resultVars[0] /* $res_LSJac2_1.$pDERLSJac2.dummyVarLSJac2 JACOBIAN_VAR */ = (-jacobian->tmpVars[1] /* resistor3.v.$pDERLSJac2.dummyVarLSJac2 JACOBIAN_DIFF_VAR */) - jacobian->seedVars[0] /* resistor2.v.SeedLSJac2 SEED_VAR */;
  TRACE_POP
}

OMC_DISABLE_OPT
int oc_latch_functionJacLSJac2_constantEqns(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH

  DATA* data = ((DATA*)inData);
  int index = oc_latch_INDEX_JAC_LSJac2;
  
  
  TRACE_POP
  return 0;
}

int oc_latch_functionJacLSJac2_column(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH

  DATA* data = ((DATA*)inData);
  int index = oc_latch_INDEX_JAC_LSJac2;
  oc_latch_eqFunction_95(data, threadData, jacobian, parentJacobian);
  oc_latch_eqFunction_96(data, threadData, jacobian, parentJacobian);
  oc_latch_eqFunction_97(data, threadData, jacobian, parentJacobian);
  TRACE_POP
  return 0;
}
/* constant equations */
/* dynamic equations */

/*
equation index: 118
type: SIMPLE_ASSIGN
R1.v.$pDERLSJac3.dummyVarLSJac3 = R1.R_actual * R2.i.SeedLSJac3
*/
void oc_latch_eqFunction_118(DATA *data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  const int baseClockIndex = 0;
  const int subClockIndex = 0;
  const int equationIndexes[2] = {1,118};
  jacobian->tmpVars[0] /* R1.v.$pDERLSJac3.dummyVarLSJac3 JACOBIAN_DIFF_VAR */ = ((data->localData[0]->realVars[1]/* R1.R_actual variable */) ) * (jacobian->seedVars[0] /* R2.i.SeedLSJac3 SEED_VAR */);
  TRACE_POP
}

/*
equation index: 119
type: SIMPLE_ASSIGN
R2.v.$pDERLSJac3.dummyVarLSJac3 = R2.R_actual * R2.i.SeedLSJac3
*/
void oc_latch_eqFunction_119(DATA *data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  const int baseClockIndex = 0;
  const int subClockIndex = 1;
  const int equationIndexes[2] = {1,119};
  jacobian->tmpVars[1] /* R2.v.$pDERLSJac3.dummyVarLSJac3 JACOBIAN_DIFF_VAR */ = ((data->localData[0]->realVars[4]/* R2.R_actual variable */) ) * (jacobian->seedVars[0] /* R2.i.SeedLSJac3 SEED_VAR */);
  TRACE_POP
}

/*
equation index: 120
type: SIMPLE_ASSIGN
$res_LSJac3_1.$pDERLSJac3.dummyVarLSJac3 = (-R2.v.$pDERLSJac3.dummyVarLSJac3) - R1.v.$pDERLSJac3.dummyVarLSJac3
*/
void oc_latch_eqFunction_120(DATA *data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  const int baseClockIndex = 0;
  const int subClockIndex = 2;
  const int equationIndexes[2] = {1,120};
  jacobian->resultVars[0] /* $res_LSJac3_1.$pDERLSJac3.dummyVarLSJac3 JACOBIAN_VAR */ = (-jacobian->tmpVars[1] /* R2.v.$pDERLSJac3.dummyVarLSJac3 JACOBIAN_DIFF_VAR */) - jacobian->tmpVars[0] /* R1.v.$pDERLSJac3.dummyVarLSJac3 JACOBIAN_DIFF_VAR */;
  TRACE_POP
}

OMC_DISABLE_OPT
int oc_latch_functionJacLSJac3_constantEqns(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH

  DATA* data = ((DATA*)inData);
  int index = oc_latch_INDEX_JAC_LSJac3;
  
  
  TRACE_POP
  return 0;
}

int oc_latch_functionJacLSJac3_column(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH

  DATA* data = ((DATA*)inData);
  int index = oc_latch_INDEX_JAC_LSJac3;
  oc_latch_eqFunction_118(data, threadData, jacobian, parentJacobian);
  oc_latch_eqFunction_119(data, threadData, jacobian, parentJacobian);
  oc_latch_eqFunction_120(data, threadData, jacobian, parentJacobian);
  TRACE_POP
  return 0;
}
int oc_latch_functionJacF_column(void* data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  TRACE_POP
  return 0;
}
int oc_latch_functionJacD_column(void* data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  TRACE_POP
  return 0;
}
int oc_latch_functionJacC_column(void* data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  TRACE_POP
  return 0;
}
int oc_latch_functionJacB_column(void* data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  TRACE_POP
  return 0;
}
int oc_latch_functionJacA_column(void* data, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian, ANALYTIC_JACOBIAN *parentJacobian)
{
  TRACE_PUSH
  TRACE_POP
  return 0;
}

OMC_DISABLE_OPT
int oc_latch_initialAnalyticJacobianLSJac0(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian)
{
  TRACE_PUSH
  DATA* data = ((DATA*)inData);
  const int colPtrIndex[1+1] = {0,1};
  const int rowIndex[1] = {0};
  int i = 0;
  
  jacobian->sizeCols = 1;
  jacobian->sizeRows = 1;
  jacobian->sizeTmpVars = 3;
  jacobian->seedVars = (modelica_real*) calloc(1,sizeof(modelica_real));
  jacobian->resultVars = (modelica_real*) calloc(1,sizeof(modelica_real));
  jacobian->tmpVars = (modelica_real*) calloc(3,sizeof(modelica_real));
  jacobian->sparsePattern = (SPARSE_PATTERN*) malloc(sizeof(SPARSE_PATTERN));
  jacobian->sparsePattern->leadindex = (unsigned int*) malloc((1+1)*sizeof(unsigned int));
  jacobian->sparsePattern->index = (unsigned int*) malloc(1*sizeof(unsigned int));
  jacobian->sparsePattern->numberOfNonZeros = 1;
  jacobian->sparsePattern->colorCols = (unsigned int*) malloc(1*sizeof(unsigned int));
  jacobian->sparsePattern->maxColors = 1;
  jacobian->constantEqns = NULL;
  
  /* write lead index of compressed sparse column */
  memcpy(jacobian->sparsePattern->leadindex, colPtrIndex, (1+1)*sizeof(unsigned int));
  
  for(i=2;i<1+1;++i)
    jacobian->sparsePattern->leadindex[i] += jacobian->sparsePattern->leadindex[i-1];
  
  /* call sparse index */
  memcpy(jacobian->sparsePattern->index, rowIndex, 1*sizeof(unsigned int));
  
  /* write color array */
  jacobian->sparsePattern->colorCols[0] = 1;
  TRACE_POP
  return 0;
}
OMC_DISABLE_OPT
int oc_latch_initialAnalyticJacobianLSJac1(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian)
{
  TRACE_PUSH
  DATA* data = ((DATA*)inData);
  const int colPtrIndex[1+1] = {0,1};
  const int rowIndex[1] = {0};
  int i = 0;
  
  jacobian->sizeCols = 1;
  jacobian->sizeRows = 1;
  jacobian->sizeTmpVars = 3;
  jacobian->seedVars = (modelica_real*) calloc(1,sizeof(modelica_real));
  jacobian->resultVars = (modelica_real*) calloc(1,sizeof(modelica_real));
  jacobian->tmpVars = (modelica_real*) calloc(3,sizeof(modelica_real));
  jacobian->sparsePattern = (SPARSE_PATTERN*) malloc(sizeof(SPARSE_PATTERN));
  jacobian->sparsePattern->leadindex = (unsigned int*) malloc((1+1)*sizeof(unsigned int));
  jacobian->sparsePattern->index = (unsigned int*) malloc(1*sizeof(unsigned int));
  jacobian->sparsePattern->numberOfNonZeros = 1;
  jacobian->sparsePattern->colorCols = (unsigned int*) malloc(1*sizeof(unsigned int));
  jacobian->sparsePattern->maxColors = 1;
  jacobian->constantEqns = NULL;
  
  /* write lead index of compressed sparse column */
  memcpy(jacobian->sparsePattern->leadindex, colPtrIndex, (1+1)*sizeof(unsigned int));
  
  for(i=2;i<1+1;++i)
    jacobian->sparsePattern->leadindex[i] += jacobian->sparsePattern->leadindex[i-1];
  
  /* call sparse index */
  memcpy(jacobian->sparsePattern->index, rowIndex, 1*sizeof(unsigned int));
  
  /* write color array */
  jacobian->sparsePattern->colorCols[0] = 1;
  TRACE_POP
  return 0;
}
OMC_DISABLE_OPT
int oc_latch_initialAnalyticJacobianLSJac2(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian)
{
  TRACE_PUSH
  DATA* data = ((DATA*)inData);
  const int colPtrIndex[1+1] = {0,1};
  const int rowIndex[1] = {0};
  int i = 0;
  
  jacobian->sizeCols = 1;
  jacobian->sizeRows = 1;
  jacobian->sizeTmpVars = 3;
  jacobian->seedVars = (modelica_real*) calloc(1,sizeof(modelica_real));
  jacobian->resultVars = (modelica_real*) calloc(1,sizeof(modelica_real));
  jacobian->tmpVars = (modelica_real*) calloc(3,sizeof(modelica_real));
  jacobian->sparsePattern = (SPARSE_PATTERN*) malloc(sizeof(SPARSE_PATTERN));
  jacobian->sparsePattern->leadindex = (unsigned int*) malloc((1+1)*sizeof(unsigned int));
  jacobian->sparsePattern->index = (unsigned int*) malloc(1*sizeof(unsigned int));
  jacobian->sparsePattern->numberOfNonZeros = 1;
  jacobian->sparsePattern->colorCols = (unsigned int*) malloc(1*sizeof(unsigned int));
  jacobian->sparsePattern->maxColors = 1;
  jacobian->constantEqns = NULL;
  
  /* write lead index of compressed sparse column */
  memcpy(jacobian->sparsePattern->leadindex, colPtrIndex, (1+1)*sizeof(unsigned int));
  
  for(i=2;i<1+1;++i)
    jacobian->sparsePattern->leadindex[i] += jacobian->sparsePattern->leadindex[i-1];
  
  /* call sparse index */
  memcpy(jacobian->sparsePattern->index, rowIndex, 1*sizeof(unsigned int));
  
  /* write color array */
  jacobian->sparsePattern->colorCols[0] = 1;
  TRACE_POP
  return 0;
}
OMC_DISABLE_OPT
int oc_latch_initialAnalyticJacobianLSJac3(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian)
{
  TRACE_PUSH
  DATA* data = ((DATA*)inData);
  const int colPtrIndex[1+1] = {0,1};
  const int rowIndex[1] = {0};
  int i = 0;
  
  jacobian->sizeCols = 1;
  jacobian->sizeRows = 1;
  jacobian->sizeTmpVars = 3;
  jacobian->seedVars = (modelica_real*) calloc(1,sizeof(modelica_real));
  jacobian->resultVars = (modelica_real*) calloc(1,sizeof(modelica_real));
  jacobian->tmpVars = (modelica_real*) calloc(3,sizeof(modelica_real));
  jacobian->sparsePattern = (SPARSE_PATTERN*) malloc(sizeof(SPARSE_PATTERN));
  jacobian->sparsePattern->leadindex = (unsigned int*) malloc((1+1)*sizeof(unsigned int));
  jacobian->sparsePattern->index = (unsigned int*) malloc(1*sizeof(unsigned int));
  jacobian->sparsePattern->numberOfNonZeros = 1;
  jacobian->sparsePattern->colorCols = (unsigned int*) malloc(1*sizeof(unsigned int));
  jacobian->sparsePattern->maxColors = 1;
  jacobian->constantEqns = NULL;
  
  /* write lead index of compressed sparse column */
  memcpy(jacobian->sparsePattern->leadindex, colPtrIndex, (1+1)*sizeof(unsigned int));
  
  for(i=2;i<1+1;++i)
    jacobian->sparsePattern->leadindex[i] += jacobian->sparsePattern->leadindex[i-1];
  
  /* call sparse index */
  memcpy(jacobian->sparsePattern->index, rowIndex, 1*sizeof(unsigned int));
  
  /* write color array */
  jacobian->sparsePattern->colorCols[0] = 1;
  TRACE_POP
  return 0;
}
int oc_latch_initialAnalyticJacobianF(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian)
{
  TRACE_PUSH
  TRACE_POP
  return 1;
}
int oc_latch_initialAnalyticJacobianD(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian)
{
  TRACE_PUSH
  TRACE_POP
  return 1;
}
int oc_latch_initialAnalyticJacobianC(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian)
{
  TRACE_PUSH
  TRACE_POP
  return 1;
}
int oc_latch_initialAnalyticJacobianB(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian)
{
  TRACE_PUSH
  TRACE_POP
  return 1;
}
int oc_latch_initialAnalyticJacobianA(void* inData, threadData_t *threadData, ANALYTIC_JACOBIAN *jacobian)
{
  TRACE_PUSH
  TRACE_POP
  return 1;
}


