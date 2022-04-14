/* Main Simulation File */

#if defined(__cplusplus)
extern "C" {
#endif

#include "oc_latch_model.h"
#include "simulation/solver/events.h"

/* FIXME these defines are ugly and hard to read, why not use direct function pointers instead? */
#define prefixedName_performSimulation oc_latch_performSimulation
#define prefixedName_updateContinuousSystem oc_latch_updateContinuousSystem
#include <simulation/solver/perform_simulation.c.inc>

#define prefixedName_performQSSSimulation oc_latch_performQSSSimulation
#include <simulation/solver/perform_qss_simulation.c.inc>


/* dummy VARINFO and FILEINFO */
const FILE_INFO dummyFILE_INFO = omc_dummyFileInfo;
const VAR_INFO dummyVAR_INFO = omc_dummyVarInfo;

int oc_latch_input_function(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH

  
  TRACE_POP
  return 0;
}

int oc_latch_input_function_init(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH

  
  TRACE_POP
  return 0;
}

int oc_latch_input_function_updateStartValues(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH

  
  TRACE_POP
  return 0;
}

int oc_latch_inputNames(DATA *data, char ** names){
  TRACE_PUSH

  
  TRACE_POP
  return 0;
}

int oc_latch_data_function(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH

  TRACE_POP
  return 0;
}

int oc_latch_dataReconciliationInputNames(DATA *data, char ** names){
  TRACE_PUSH

  
  TRACE_POP
  return 0;
}

int oc_latch_output_function(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH

  
  TRACE_POP
  return 0;
}

int oc_latch_setc_function(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH

  
  TRACE_POP
  return 0;
}


/*
equation index: 89
type: SIMPLE_ASSIGN
$whenCondition1 = time >= pre(combiTimeTable.nextTimeEvent)
*/
void oc_latch_eqFunction_89(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,89};
  modelica_boolean tmp0;
  relationhysteresis(data, &tmp0, data->localData[0]->timeValue, (data->simulationInfo->realVarsPre[56]/* combiTimeTable.nextTimeEvent DISCRETE */) , 6, GreaterEq, GreaterEqZC);
  (data->localData[0]->booleanVars[0]/* $whenCondition1 DISCRETE */)  = tmp0;
  TRACE_POP
}
/*
equation index: 90
type: SIMPLE_ASSIGN
reset = time >= 0.95 and time <= 0.96
*/
void oc_latch_eqFunction_90(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,90};
  modelica_boolean tmp1;
  modelica_boolean tmp2;
  relationhysteresis(data, &tmp1, data->localData[0]->timeValue, 0.95, 4, GreaterEq, GreaterEqZC);
  relationhysteresis(data, &tmp2, data->localData[0]->timeValue, 0.96, 5, LessEq, LessEqZC);
  (data->localData[0]->booleanVars[11]/* reset DISCRETE */)  = (tmp1 && tmp2);
  TRACE_POP
}
/*
equation index: 91
type: SIMPLE_ASSIGN
enable = time <= 0.1 or time >= 0.9
*/
void oc_latch_eqFunction_91(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,91};
  modelica_boolean tmp3;
  modelica_boolean tmp4;
  relationhysteresis(data, &tmp3, data->localData[0]->timeValue, 0.1, 2, LessEq, LessEqZC);
  relationhysteresis(data, &tmp4, data->localData[0]->timeValue, 0.9, 3, GreaterEq, GreaterEqZC);
  (data->localData[0]->booleanVars[2]/* enable DISCRETE */)  = (tmp3 || tmp4);
  TRACE_POP
}
/*
equation index: 98
type: LINEAR

<var>resistor2.v</var>
<row>

</row>
<matrix>
</matrix>
*/
OMC_DISABLE_OPT
void oc_latch_eqFunction_98(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,98};
  /* Linear equation system */
  int retValue;
  double aux_x[1] = { (data->localData[1]->realVars[49]/* resistor2.v variable */)  };
  if(ACTIVE_STREAM(LOG_DT))
  {
    infoStreamPrint(LOG_DT, 1, "Solving linear system 98 (STRICT TEARING SET if tearing enabled) at time = %18.10e", data->localData[0]->timeValue);
    messageClose(LOG_DT);
  }
  
  retValue = solve_linear_system(data, threadData, 2, &aux_x[0]);
  
  /* check if solution process was successful */
  if (retValue > 0){
    const int indexes[2] = {1,98};
    throwStreamPrintWithEquationIndexes(threadData, indexes, "Solving linear system 98 failed at time=%.15g.\nFor more information please use -lv LOG_LS.", data->localData[0]->timeValue);
  }
  /* write solution */
  (data->localData[0]->realVars[49]/* resistor2.v variable */)  = aux_x[0];

  TRACE_POP
}
/*
equation index: 99
type: SIMPLE_ASSIGN
resistor2.LossPower = resistor2.v * resistor3.i
*/
void oc_latch_eqFunction_99(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,99};
  (data->localData[0]->realVars[47]/* resistor2.LossPower variable */)  = ((data->localData[0]->realVars[49]/* resistor2.v variable */) ) * ((data->localData[0]->realVars[52]/* resistor3.i variable */) );
  TRACE_POP
}
/*
equation index: 100
type: SIMPLE_ASSIGN
resistor3.LossPower = resistor3.v * resistor3.i
*/
void oc_latch_eqFunction_100(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,100};
  (data->localData[0]->realVars[50]/* resistor3.LossPower variable */)  = ((data->localData[0]->realVars[53]/* resistor3.v variable */) ) * ((data->localData[0]->realVars[52]/* resistor3.i variable */) );
  TRACE_POP
}
/*
equation index: 101
type: SIMPLE_ASSIGN
pre11.y = pre(pre11.u)
*/
void oc_latch_eqFunction_101(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,101};
  (data->localData[0]->booleanVars[10]/* pre11.y DISCRETE */)  = (data->simulationInfo->booleanVarsPre[9]/* pre11.u DISCRETE */) ;
  TRACE_POP
}
/*
equation index: 102
type: SIMPLE_ASSIGN
nor1.u1 = pre(pre1.u)
*/
void oc_latch_eqFunction_102(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,102};
  (data->localData[0]->booleanVars[5]/* nor1.u1 DISCRETE */)  = (data->simulationInfo->booleanVarsPre[8]/* pre1.u DISCRETE */) ;
  TRACE_POP
}
/*
equation index: 103
type: SIMPLE_ASSIGN
SW = not (nor1.u1 or pre11.y)
*/
void oc_latch_eqFunction_103(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,103};
  (data->localData[0]->booleanVars[1]/* SW DISCRETE */)  = (!((data->localData[0]->booleanVars[5]/* nor1.u1 DISCRETE */)  || (data->localData[0]->booleanVars[10]/* pre11.y DISCRETE */) ));
  TRACE_POP
}
/*
equation index: 104
type: SIMPLE_ASSIGN
pre1.u = not (SW or enable)
*/
void oc_latch_eqFunction_104(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,104};
  (data->localData[0]->booleanVars[8]/* pre1.u DISCRETE */)  = (!((data->localData[0]->booleanVars[1]/* SW DISCRETE */)  || (data->localData[0]->booleanVars[2]/* enable DISCRETE */) ));
  TRACE_POP
}
/*
equation index: 105
type: SIMPLE_ASSIGN
combiTimeTable.timeScaled = time
*/
void oc_latch_eqFunction_105(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,105};
  (data->localData[0]->realVars[9]/* combiTimeTable.timeScaled variable */)  = data->localData[0]->timeValue;
  TRACE_POP
}
/*
equation index: 106
type: WHEN

when {$whenCondition1} then
  combiTimeTable.nextTimeEventScaled = Modelica.Blocks.Tables.Internal.getNextTimeEvent(combiTimeTable.tableID, combiTimeTable.timeScaled);
end when;
*/
void oc_latch_eqFunction_106(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,106};
  if(((data->localData[0]->booleanVars[0]/* $whenCondition1 DISCRETE */)  && !(data->simulationInfo->booleanVarsPre[0]/* $whenCondition1 DISCRETE */)  /* edge */))
  {
    (data->localData[0]->realVars[57]/* combiTimeTable.nextTimeEventScaled DISCRETE */)  = omc_Modelica_Blocks_Tables_Internal_getNextTimeEvent(threadData, (data->simulationInfo->extObjs[0]), (data->localData[0]->realVars[9]/* combiTimeTable.timeScaled variable */) );
  }
  TRACE_POP
}
/*
equation index: 107
type: SIMPLE_ASSIGN
combiTimeTable.y[1] = Modelica.Blocks.Tables.Internal.getTimeTableValueNoDer(combiTimeTable.tableID, 1, combiTimeTable.timeScaled, combiTimeTable.nextTimeEventScaled, pre(combiTimeTable.nextTimeEventScaled))
*/
void oc_latch_eqFunction_107(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,107};
  (data->localData[0]->realVars[10]/* combiTimeTable.y[1] variable */)  = omc_Modelica_Blocks_Tables_Internal_getTimeTableValueNoDer(threadData, (data->simulationInfo->extObjs[0]), ((modelica_integer) 1), (data->localData[0]->realVars[9]/* combiTimeTable.timeScaled variable */) , (data->localData[0]->realVars[57]/* combiTimeTable.nextTimeEventScaled DISCRETE */) , (data->simulationInfo->realVarsPre[57]/* combiTimeTable.nextTimeEventScaled DISCRETE */) );
  TRACE_POP
}
/*
equation index: 108
type: WHEN

when {$whenCondition1} then
  combiTimeTable.nextTimeEvent = if combiTimeTable.nextTimeEventScaled < 9.999999999999999e+59 then combiTimeTable.nextTimeEventScaled else 9.999999999999999e+59;
end when;
*/
void oc_latch_eqFunction_108(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,108};
  modelica_boolean tmp5;
  if(((data->localData[0]->booleanVars[0]/* $whenCondition1 DISCRETE */)  && !(data->simulationInfo->booleanVarsPre[0]/* $whenCondition1 DISCRETE */)  /* edge */))
  {
    tmp5 = Less((data->localData[0]->realVars[57]/* combiTimeTable.nextTimeEventScaled DISCRETE */) ,9.999999999999999e+59);
    (data->localData[0]->realVars[56]/* combiTimeTable.nextTimeEvent DISCRETE */)  = (tmp5?(data->localData[0]->realVars[57]/* combiTimeTable.nextTimeEventScaled DISCRETE */) :9.999999999999999e+59);
  }
  TRACE_POP
}
/*
equation index: 109
type: SIMPLE_ASSIGN
opAmp1.vin = combiTimeTable.y[1] - resistor3.v
*/
void oc_latch_eqFunction_109(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,109};
  (data->localData[0]->realVars[34]/* opAmp1.vin variable */)  = (data->localData[0]->realVars[10]/* combiTimeTable.y[1] variable */)  - (data->localData[0]->realVars[53]/* resistor3.v variable */) ;
  TRACE_POP
}
/*
equation index: 110
type: SIMPLE_ASSIGN
potentialSensor1.phi = 0.5 * constantVoltage.V + opAmp1.absSlope * opAmp1.vin / (1.0 + opAmp1.absSlope * smooth(0, if opAmp1.f * opAmp1.vin < 0.0 then (-opAmp1.f) * opAmp1.vin else opAmp1.f * opAmp1.vin))
*/
void oc_latch_eqFunction_110(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,110};
  modelica_boolean tmp6;
  tmp6 = Less(((data->localData[0]->realVars[31]/* opAmp1.f variable */) ) * ((data->localData[0]->realVars[34]/* opAmp1.vin variable */) ),0.0);
  (data->localData[0]->realVars[38]/* potentialSensor1.phi variable */)  = (0.5) * ((data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */) ) + ((data->localData[0]->realVars[30]/* opAmp1.absSlope variable */) ) * (DIVISION_SIM((data->localData[0]->realVars[34]/* opAmp1.vin variable */) ,1.0 + ((data->localData[0]->realVars[30]/* opAmp1.absSlope variable */) ) * ((tmp6?((-(data->localData[0]->realVars[31]/* opAmp1.f variable */) )) * ((data->localData[0]->realVars[34]/* opAmp1.vin variable */) ):((data->localData[0]->realVars[31]/* opAmp1.f variable */) ) * ((data->localData[0]->realVars[34]/* opAmp1.vin variable */) ))),"1.0 + opAmp1.absSlope * smooth(0, if opAmp1.f * opAmp1.vin < 0.0 then (-opAmp1.f) * opAmp1.vin else opAmp1.f * opAmp1.vin)",equationIndexes));
  TRACE_POP
}
/*
equation index: 111
type: SIMPLE_ASSIGN
resistor1.v = constantVoltage.V - potentialSensor1.phi
*/
void oc_latch_eqFunction_111(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,111};
  (data->localData[0]->realVars[46]/* resistor1.v variable */)  = (data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */)  - (data->localData[0]->realVars[38]/* potentialSensor1.phi variable */) ;
  TRACE_POP
}
/*
equation index: 112
type: SIMPLE_ASSIGN
resistor1.i = resistor1.v / resistor1.R_actual
*/
void oc_latch_eqFunction_112(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,112};
  (data->localData[0]->realVars[45]/* resistor1.i variable */)  = DIVISION_SIM((data->localData[0]->realVars[46]/* resistor1.v variable */) ,(data->localData[0]->realVars[44]/* resistor1.R_actual variable */) ,"resistor1.R_actual",equationIndexes);
  TRACE_POP
}
/*
equation index: 113
type: SIMPLE_ASSIGN
resistor1.LossPower = resistor1.v * resistor1.i
*/
void oc_latch_eqFunction_113(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,113};
  (data->localData[0]->realVars[43]/* resistor1.LossPower variable */)  = ((data->localData[0]->realVars[46]/* resistor1.v variable */) ) * ((data->localData[0]->realVars[45]/* resistor1.i variable */) );
  TRACE_POP
}
/*
equation index: 114
type: SIMPLE_ASSIGN
greaterEqualThreshold1.y = potentialSensor1.phi >= greaterEqualThreshold1.threshold
*/
void oc_latch_eqFunction_114(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,114};
  modelica_boolean tmp7;
  relationhysteresis(data, &tmp7, (data->localData[0]->realVars[38]/* potentialSensor1.phi variable */) , (data->simulationInfo->realParameter[33]/* greaterEqualThreshold1.threshold PARAM */) , 1, GreaterEq, GreaterEqZC);
  (data->localData[0]->booleanVars[3]/* greaterEqualThreshold1.y DISCRETE */)  = tmp7;
  TRACE_POP
}
/*
equation index: 121
type: LINEAR

<var>R2.i</var>
<row>

</row>
<matrix>
</matrix>
*/
OMC_DISABLE_OPT
void oc_latch_eqFunction_121(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,121};
  /* Linear equation system */
  int retValue;
  double aux_x[1] = { (data->localData[1]->realVars[5]/* R2.i variable */)  };
  if(ACTIVE_STREAM(LOG_DT))
  {
    infoStreamPrint(LOG_DT, 1, "Solving linear system 121 (STRICT TEARING SET if tearing enabled) at time = %18.10e", data->localData[0]->timeValue);
    messageClose(LOG_DT);
  }
  
  retValue = solve_linear_system(data, threadData, 3, &aux_x[0]);
  
  /* check if solution process was successful */
  if (retValue > 0){
    const int indexes[2] = {1,121};
    throwStreamPrintWithEquationIndexes(threadData, indexes, "Solving linear system 121 failed at time=%.15g.\nFor more information please use -lv LOG_LS.", data->localData[0]->timeValue);
  }
  /* write solution */
  (data->localData[0]->realVars[5]/* R2.i variable */)  = aux_x[0];

  TRACE_POP
}
/*
equation index: 122
type: SIMPLE_ASSIGN
R1.LossPower = R1.v * R2.i
*/
void oc_latch_eqFunction_122(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,122};
  (data->localData[0]->realVars[0]/* R1.LossPower variable */)  = ((data->localData[0]->realVars[2]/* R1.v variable */) ) * ((data->localData[0]->realVars[5]/* R2.i variable */) );
  TRACE_POP
}
/*
equation index: 123
type: SIMPLE_ASSIGN
opAmp.vin = R2.v - combiTimeTable.y[1]
*/
void oc_latch_eqFunction_123(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,123};
  (data->localData[0]->realVars[27]/* opAmp.vin variable */)  = (data->localData[0]->realVars[6]/* R2.v variable */)  - (data->localData[0]->realVars[10]/* combiTimeTable.y[1] variable */) ;
  TRACE_POP
}
/*
equation index: 124
type: SIMPLE_ASSIGN
potentialSensor.phi = 0.5 * constantVoltage.V + opAmp.absSlope * opAmp.vin / (1.0 + opAmp.absSlope * smooth(0, if opAmp.f * opAmp.vin < 0.0 then (-opAmp.f) * opAmp.vin else opAmp.f * opAmp.vin))
*/
void oc_latch_eqFunction_124(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,124};
  modelica_boolean tmp8;
  tmp8 = Less(((data->localData[0]->realVars[24]/* opAmp.f variable */) ) * ((data->localData[0]->realVars[27]/* opAmp.vin variable */) ),0.0);
  (data->localData[0]->realVars[36]/* potentialSensor.phi variable */)  = (0.5) * ((data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */) ) + ((data->localData[0]->realVars[23]/* opAmp.absSlope variable */) ) * (DIVISION_SIM((data->localData[0]->realVars[27]/* opAmp.vin variable */) ,1.0 + ((data->localData[0]->realVars[23]/* opAmp.absSlope variable */) ) * ((tmp8?((-(data->localData[0]->realVars[24]/* opAmp.f variable */) )) * ((data->localData[0]->realVars[27]/* opAmp.vin variable */) ):((data->localData[0]->realVars[24]/* opAmp.f variable */) ) * ((data->localData[0]->realVars[27]/* opAmp.vin variable */) ))),"1.0 + opAmp.absSlope * smooth(0, if opAmp.f * opAmp.vin < 0.0 then (-opAmp.f) * opAmp.vin else opAmp.f * opAmp.vin)",equationIndexes));
  TRACE_POP
}
/*
equation index: 125
type: SIMPLE_ASSIGN
resistor.v = constantVoltage.V - potentialSensor.phi
*/
void oc_latch_eqFunction_125(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,125};
  (data->localData[0]->realVars[42]/* resistor.v variable */)  = (data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */)  - (data->localData[0]->realVars[36]/* potentialSensor.phi variable */) ;
  TRACE_POP
}
/*
equation index: 126
type: SIMPLE_ASSIGN
resistor.i = resistor.v / resistor.R_actual
*/
void oc_latch_eqFunction_126(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,126};
  (data->localData[0]->realVars[41]/* resistor.i variable */)  = DIVISION_SIM((data->localData[0]->realVars[42]/* resistor.v variable */) ,(data->localData[0]->realVars[40]/* resistor.R_actual variable */) ,"resistor.R_actual",equationIndexes);
  TRACE_POP
}
/*
equation index: 127
type: SIMPLE_ASSIGN
resistor.LossPower = resistor.v * resistor.i
*/
void oc_latch_eqFunction_127(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,127};
  (data->localData[0]->realVars[39]/* resistor.LossPower variable */)  = ((data->localData[0]->realVars[42]/* resistor.v variable */) ) * ((data->localData[0]->realVars[41]/* resistor.i variable */) );
  TRACE_POP
}
/*
equation index: 128
type: SIMPLE_ASSIGN
nand.u1 = potentialSensor.phi >= greaterEqualThreshold.threshold
*/
void oc_latch_eqFunction_128(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,128};
  modelica_boolean tmp9;
  relationhysteresis(data, &tmp9, (data->localData[0]->realVars[36]/* potentialSensor.phi variable */) , (data->simulationInfo->realParameter[32]/* greaterEqualThreshold.threshold PARAM */) , 0, GreaterEq, GreaterEqZC);
  (data->localData[0]->booleanVars[4]/* nand.u1 DISCRETE */)  = tmp9;
  TRACE_POP
}
/*
equation index: 129
type: SIMPLE_ASSIGN
nor3.u2 = not (nand.u1 and greaterEqualThreshold1.y)
*/
void oc_latch_eqFunction_129(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,129};
  (data->localData[0]->booleanVars[6]/* nor3.u2 DISCRETE */)  = (!((data->localData[0]->booleanVars[4]/* nand.u1 DISCRETE */)  && (data->localData[0]->booleanVars[3]/* greaterEqualThreshold1.y DISCRETE */) ));
  TRACE_POP
}
/*
equation index: 130
type: SIMPLE_ASSIGN
nor3.y = not (pre11.y or nor3.u2)
*/
void oc_latch_eqFunction_130(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,130};
  (data->localData[0]->booleanVars[7]/* nor3.y DISCRETE */)  = (!((data->localData[0]->booleanVars[10]/* pre11.y DISCRETE */)  || (data->localData[0]->booleanVars[6]/* nor3.u2 DISCRETE */) ));
  TRACE_POP
}
/*
equation index: 131
type: SIMPLE_ASSIGN
pre11.u = not (nor3.y or reset)
*/
void oc_latch_eqFunction_131(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,131};
  (data->localData[0]->booleanVars[9]/* pre11.u DISCRETE */)  = (!((data->localData[0]->booleanVars[7]/* nor3.y DISCRETE */)  || (data->localData[0]->booleanVars[11]/* reset DISCRETE */) ));
  TRACE_POP
}
/*
equation index: 132
type: SIMPLE_ASSIGN
R2.LossPower = R2.v * R2.i
*/
void oc_latch_eqFunction_132(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,132};
  (data->localData[0]->realVars[3]/* R2.LossPower variable */)  = ((data->localData[0]->realVars[6]/* R2.v variable */) ) * ((data->localData[0]->realVars[5]/* R2.i variable */) );
  TRACE_POP
}
/*
equation index: 133
type: SIMPLE_ASSIGN
constantVoltage.i = (-resistor3.i) - resistor1.i - resistor.i - R2.i
*/
void oc_latch_eqFunction_133(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,133};
  (data->localData[0]->realVars[11]/* constantVoltage.i variable */)  = (-(data->localData[0]->realVars[52]/* resistor3.i variable */) ) - (data->localData[0]->realVars[45]/* resistor1.i variable */)  - (data->localData[0]->realVars[41]/* resistor.i variable */)  - (data->localData[0]->realVars[5]/* R2.i variable */) ;
  TRACE_POP
}
/*
equation index: 139
type: ALGORITHM

  assert(1.0 + resistor3.alpha * (resistor3.T - resistor3.T_ref) >= 1e-15, "Temperature outside scope of model!");
*/
void oc_latch_eqFunction_139(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,139};
  modelica_boolean tmp10;
  static const MMC_DEFSTRINGLIT(tmp11,35,"Temperature outside scope of model!");
  static int tmp12 = 0;
  {
    tmp10 = GreaterEq(1.0 + ((data->simulationInfo->realParameter[60]/* resistor3.alpha PARAM */) ) * ((data->simulationInfo->realParameter[57]/* resistor3.T PARAM */)  - (data->simulationInfo->realParameter[59]/* resistor3.T_ref PARAM */) ),1e-15);
    if(!tmp10)
    {
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\n1.0 + resistor3.alpha * (resistor3.T - resistor3.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp11)));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\n1.0 + resistor3.alpha * (resistor3.T - resistor3.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp11)));
        }
      }
    }
  }
  TRACE_POP
}
/*
equation index: 138
type: ALGORITHM

  assert(1.0 + resistor2.alpha * (resistor2.T - resistor2.T_ref) >= 1e-15, "Temperature outside scope of model!");
*/
void oc_latch_eqFunction_138(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,138};
  modelica_boolean tmp13;
  static const MMC_DEFSTRINGLIT(tmp14,35,"Temperature outside scope of model!");
  static int tmp15 = 0;
  {
    tmp13 = GreaterEq(1.0 + ((data->simulationInfo->realParameter[54]/* resistor2.alpha PARAM */) ) * ((data->simulationInfo->realParameter[51]/* resistor2.T PARAM */)  - (data->simulationInfo->realParameter[53]/* resistor2.T_ref PARAM */) ),1e-15);
    if(!tmp13)
    {
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\n1.0 + resistor2.alpha * (resistor2.T - resistor2.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp14)));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\n1.0 + resistor2.alpha * (resistor2.T - resistor2.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp14)));
        }
      }
    }
  }
  TRACE_POP
}
/*
equation index: 137
type: ALGORITHM

  assert(1.0 + resistor1.alpha * (resistor1.T - resistor1.T_ref) >= 1e-15, "Temperature outside scope of model!");
*/
void oc_latch_eqFunction_137(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,137};
  modelica_boolean tmp16;
  static const MMC_DEFSTRINGLIT(tmp17,35,"Temperature outside scope of model!");
  static int tmp18 = 0;
  {
    tmp16 = GreaterEq(1.0 + ((data->simulationInfo->realParameter[48]/* resistor1.alpha PARAM */) ) * ((data->simulationInfo->realParameter[45]/* resistor1.T PARAM */)  - (data->simulationInfo->realParameter[47]/* resistor1.T_ref PARAM */) ),1e-15);
    if(!tmp16)
    {
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\n1.0 + resistor1.alpha * (resistor1.T - resistor1.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp17)));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\n1.0 + resistor1.alpha * (resistor1.T - resistor1.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp17)));
        }
      }
    }
  }
  TRACE_POP
}
/*
equation index: 136
type: ALGORITHM

  assert(1.0 + resistor.alpha * (resistor.T - resistor.T_ref) >= 1e-15, "Temperature outside scope of model!");
*/
void oc_latch_eqFunction_136(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,136};
  modelica_boolean tmp19;
  static const MMC_DEFSTRINGLIT(tmp20,35,"Temperature outside scope of model!");
  static int tmp21 = 0;
  {
    tmp19 = GreaterEq(1.0 + ((data->simulationInfo->realParameter[42]/* resistor.alpha PARAM */) ) * ((data->simulationInfo->realParameter[39]/* resistor.T PARAM */)  - (data->simulationInfo->realParameter[41]/* resistor.T_ref PARAM */) ),1e-15);
    if(!tmp19)
    {
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\n1.0 + resistor.alpha * (resistor.T - resistor.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp20)));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\n1.0 + resistor.alpha * (resistor.T - resistor.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp20)));
        }
      }
    }
  }
  TRACE_POP
}
/*
equation index: 135
type: ALGORITHM

  assert(1.0 + R2.alpha * (R2.T - R2.T_ref) >= 1e-15, "Temperature outside scope of model!");
*/
void oc_latch_eqFunction_135(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,135};
  modelica_boolean tmp22;
  static const MMC_DEFSTRINGLIT(tmp23,35,"Temperature outside scope of model!");
  static int tmp24 = 0;
  {
    tmp22 = GreaterEq(1.0 + ((data->simulationInfo->realParameter[10]/* R2.alpha PARAM */) ) * ((data->simulationInfo->realParameter[7]/* R2.T PARAM */)  - (data->simulationInfo->realParameter[9]/* R2.T_ref PARAM */) ),1e-15);
    if(!tmp22)
    {
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\n1.0 + R2.alpha * (R2.T - R2.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp23)));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\n1.0 + R2.alpha * (R2.T - R2.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp23)));
        }
      }
    }
  }
  TRACE_POP
}
/*
equation index: 134
type: ALGORITHM

  assert(1.0 + R1.alpha * (R1.T - R1.T_ref) >= 1e-15, "Temperature outside scope of model!");
*/
void oc_latch_eqFunction_134(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,134};
  modelica_boolean tmp25;
  static const MMC_DEFSTRINGLIT(tmp26,35,"Temperature outside scope of model!");
  static int tmp27 = 0;
  {
    tmp25 = GreaterEq(1.0 + ((data->simulationInfo->realParameter[4]/* R1.alpha PARAM */) ) * ((data->simulationInfo->realParameter[1]/* R1.T PARAM */)  - (data->simulationInfo->realParameter[3]/* R1.T_ref PARAM */) ),1e-15);
    if(!tmp25)
    {
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\n1.0 + R1.alpha * (R1.T - R1.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp26)));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\n1.0 + R1.alpha * (R1.T - R1.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp26)));
        }
      }
    }
  }
  TRACE_POP
}

OMC_DISABLE_OPT
int oc_latch_functionDAE(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  int equationIndexes[1] = {0};
#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_tick(SIM_TIMER_DAE);
#endif

  data->simulationInfo->needToIterate = 0;
  data->simulationInfo->discreteCall = 1;
  oc_latch_functionLocalKnownVars(data, threadData);
  oc_latch_eqFunction_89(data, threadData);

  oc_latch_eqFunction_90(data, threadData);

  oc_latch_eqFunction_91(data, threadData);

  oc_latch_eqFunction_98(data, threadData);

  oc_latch_eqFunction_99(data, threadData);

  oc_latch_eqFunction_100(data, threadData);

  oc_latch_eqFunction_101(data, threadData);

  oc_latch_eqFunction_102(data, threadData);

  oc_latch_eqFunction_103(data, threadData);

  oc_latch_eqFunction_104(data, threadData);

  oc_latch_eqFunction_105(data, threadData);

  oc_latch_eqFunction_106(data, threadData);

  oc_latch_eqFunction_107(data, threadData);

  oc_latch_eqFunction_108(data, threadData);

  oc_latch_eqFunction_109(data, threadData);

  oc_latch_eqFunction_110(data, threadData);

  oc_latch_eqFunction_111(data, threadData);

  oc_latch_eqFunction_112(data, threadData);

  oc_latch_eqFunction_113(data, threadData);

  oc_latch_eqFunction_114(data, threadData);

  oc_latch_eqFunction_121(data, threadData);

  oc_latch_eqFunction_122(data, threadData);

  oc_latch_eqFunction_123(data, threadData);

  oc_latch_eqFunction_124(data, threadData);

  oc_latch_eqFunction_125(data, threadData);

  oc_latch_eqFunction_126(data, threadData);

  oc_latch_eqFunction_127(data, threadData);

  oc_latch_eqFunction_128(data, threadData);

  oc_latch_eqFunction_129(data, threadData);

  oc_latch_eqFunction_130(data, threadData);

  oc_latch_eqFunction_131(data, threadData);

  oc_latch_eqFunction_132(data, threadData);

  oc_latch_eqFunction_133(data, threadData);

  oc_latch_eqFunction_139(data, threadData);

  oc_latch_eqFunction_138(data, threadData);

  oc_latch_eqFunction_137(data, threadData);

  oc_latch_eqFunction_136(data, threadData);

  oc_latch_eqFunction_135(data, threadData);

  oc_latch_eqFunction_134(data, threadData);
  data->simulationInfo->discreteCall = 0;
  
#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_accumulate(SIM_TIMER_DAE);
#endif
  TRACE_POP
  return 0;
}


int oc_latch_functionLocalKnownVars(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH

  
  TRACE_POP
  return 0;
}


int oc_latch_functionODE(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_tick(SIM_TIMER_FUNCTION_ODE);
#endif

  
  data->simulationInfo->callStatistics.functionODE++;
  
  oc_latch_functionLocalKnownVars(data, threadData);
  /* no ODE systems */

#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_accumulate(SIM_TIMER_FUNCTION_ODE);
#endif

  TRACE_POP
  return 0;
}

/* forward the main in the simulation runtime */
extern int _main_SimulationRuntime(int argc, char**argv, DATA *data, threadData_t *threadData);

#include "oc_latch_12jac.h"
#include "oc_latch_13opt.h"

struct OpenModelicaGeneratedFunctionCallbacks oc_latch_callback = {
   (int (*)(DATA *, threadData_t *, void *)) oc_latch_performSimulation,    /* performSimulation */
   (int (*)(DATA *, threadData_t *, void *)) oc_latch_performQSSSimulation,    /* performQSSSimulation */
   oc_latch_updateContinuousSystem,    /* updateContinuousSystem */
   oc_latch_callExternalObjectDestructors,    /* callExternalObjectDestructors */
   NULL,    /* initialNonLinearSystem */
   oc_latch_initialLinearSystem,    /* initialLinearSystem */
   NULL,    /* initialMixedSystem */
   #if !defined(OMC_NO_STATESELECTION)
   oc_latch_initializeStateSets,
   #else
   NULL,
   #endif    /* initializeStateSets */
   oc_latch_initializeDAEmodeData,
   oc_latch_functionODE,
   oc_latch_functionAlgebraics,
   oc_latch_functionDAE,
   oc_latch_functionLocalKnownVars,
   oc_latch_input_function,
   oc_latch_input_function_init,
   oc_latch_input_function_updateStartValues,
   oc_latch_data_function,
   oc_latch_output_function,
   oc_latch_setc_function,
   oc_latch_function_storeDelayed,
   oc_latch_function_storeSpatialDistribution,
   oc_latch_function_initSpatialDistribution,
   oc_latch_updateBoundVariableAttributes,
   oc_latch_functionInitialEquations,
   1, /* useHomotopy - 0: local homotopy (equidistant lambda), 1: global homotopy (equidistant lambda), 2: new global homotopy approach (adaptive lambda), 3: new local homotopy approach (adaptive lambda)*/
   NULL,
   oc_latch_functionRemovedInitialEquations,
   oc_latch_updateBoundParameters,
   oc_latch_checkForAsserts,
   oc_latch_function_ZeroCrossingsEquations,
   oc_latch_function_ZeroCrossings,
   oc_latch_function_updateRelations,
   oc_latch_zeroCrossingDescription,
   oc_latch_relationDescription,
   oc_latch_function_initSample,
   oc_latch_INDEX_JAC_A,
   oc_latch_INDEX_JAC_B,
   oc_latch_INDEX_JAC_C,
   oc_latch_INDEX_JAC_D,
   oc_latch_INDEX_JAC_F,
   oc_latch_initialAnalyticJacobianA,
   oc_latch_initialAnalyticJacobianB,
   oc_latch_initialAnalyticJacobianC,
   oc_latch_initialAnalyticJacobianD,
   oc_latch_initialAnalyticJacobianF,
   oc_latch_functionJacA_column,
   oc_latch_functionJacB_column,
   oc_latch_functionJacC_column,
   oc_latch_functionJacD_column,
   oc_latch_functionJacF_column,
   oc_latch_linear_model_frame,
   oc_latch_linear_model_datarecovery_frame,
   oc_latch_mayer,
   oc_latch_lagrange,
   oc_latch_pickUpBoundsForInputsInOptimization,
   oc_latch_setInputData,
   oc_latch_getTimeGrid,
   oc_latch_symbolicInlineSystem,
   oc_latch_function_initSynchronous,
   oc_latch_function_updateSynchronous,
   oc_latch_function_equationsSynchronous,
   oc_latch_inputNames,
   oc_latch_dataReconciliationInputNames,
   NULL,
   NULL,
   NULL,
   -1,
   NULL,
   NULL,
   -1

};

#define _OMC_LIT_RESOURCE_0_name_data "Complex"
#define _OMC_LIT_RESOURCE_0_dir_data "C:/OpenModelica/lib/omlibrary"
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_0_name,7,_OMC_LIT_RESOURCE_0_name_data);
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_0_dir,29,_OMC_LIT_RESOURCE_0_dir_data);

#define _OMC_LIT_RESOURCE_1_name_data "Modelica"
#define _OMC_LIT_RESOURCE_1_dir_data "C:/OpenModelica/lib/omlibrary/Modelica 4.0.0"
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_1_name,8,_OMC_LIT_RESOURCE_1_name_data);
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_1_dir,44,_OMC_LIT_RESOURCE_1_dir_data);

#define _OMC_LIT_RESOURCE_2_name_data "ModelicaServices"
#define _OMC_LIT_RESOURCE_2_dir_data "C:/OpenModelica/lib/omlibrary/ModelicaServices 4.0.0"
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_2_name,16,_OMC_LIT_RESOURCE_2_name_data);
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_2_dir,52,_OMC_LIT_RESOURCE_2_dir_data);

#define _OMC_LIT_RESOURCE_3_name_data "oc_latch"
#define _OMC_LIT_RESOURCE_3_dir_data "C:/Users/Trista Arinomo/Desktop"
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_3_name,8,_OMC_LIT_RESOURCE_3_name_data);
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_3_dir,31,_OMC_LIT_RESOURCE_3_dir_data);

static const MMC_DEFSTRUCTLIT(_OMC_LIT_RESOURCES,8,MMC_ARRAY_TAG) {MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_0_name), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_0_dir), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_1_name), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_1_dir), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_2_name), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_2_dir), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_3_name), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_3_dir)}};
void oc_latch_setupDataStruc(DATA *data, threadData_t *threadData)
{
  assertStreamPrint(threadData,0!=data, "Error while initialize Data");
  threadData->localRoots[LOCAL_ROOT_SIMULATION_DATA] = data;
  data->callback = &oc_latch_callback;
  OpenModelica_updateUriMapping(threadData, MMC_REFSTRUCTLIT(_OMC_LIT_RESOURCES));
  data->modelData->modelName = "oc_latch";
  data->modelData->modelFilePrefix = "oc_latch";
  data->modelData->resultFileName = NULL;
  data->modelData->modelDir = "C:/Users/Trista Arinomo/Desktop";
  data->modelData->modelGUID = "{0bd7ea97-3ec1-4ce3-9bdb-fdce290ea4a0}";
  #if defined(OPENMODELICA_XML_FROM_FILE_AT_RUNTIME)
  data->modelData->initXMLData = NULL;
  data->modelData->modelDataXml.infoXMLData = NULL;
  #else
  #if defined(_MSC_VER) /* handle joke compilers */
  {
  /* for MSVC we encode a string like char x[] = {'a', 'b', 'c', '\0'} */
  /* because the string constant limit is 65535 bytes */
  static const char contents_init[] =
    #include "oc_latch_init.c"
    ;
  static const char contents_info[] =
    #include "oc_latch_info.c"
    ;
    data->modelData->initXMLData = contents_init;
    data->modelData->modelDataXml.infoXMLData = contents_info;
  }
  #else /* handle real compilers */
  data->modelData->initXMLData =
  #include "oc_latch_init.c"
    ;
  data->modelData->modelDataXml.infoXMLData =
  #include "oc_latch_info.c"
    ;
  #endif /* defined(_MSC_VER) */
  #endif /* defined(OPENMODELICA_XML_FROM_FILE_AT_RUNTIME) */
  data->modelData->runTestsuite = 0;
  
  data->modelData->nStates = 0;
  data->modelData->nVariablesReal = 58;
  data->modelData->nDiscreteReal = 2;
  data->modelData->nVariablesInteger = 0;
  data->modelData->nVariablesBoolean = 12;
  data->modelData->nVariablesString = 0;
  data->modelData->nParametersReal = 61;
  data->modelData->nParametersInteger = 5;
  data->modelData->nParametersBoolean = 11;
  data->modelData->nParametersString = 2;
  data->modelData->nInputVars = 0;
  data->modelData->nOutputVars = 0;
  
  data->modelData->nAliasReal = 50;
  data->modelData->nAliasInteger = 0;
  data->modelData->nAliasBoolean = 13;
  data->modelData->nAliasString = 0;
  
  data->modelData->nZeroCrossings = 5;
  data->modelData->nSamples = 0;
  data->modelData->nRelations = 7;
  data->modelData->nMathEvents = 0;
  data->modelData->nExtObjs = 1;
  
  data->modelData->modelDataXml.fileName = "oc_latch_info.json";
  data->modelData->modelDataXml.modelInfoXmlLength = 0;
  data->modelData->modelDataXml.nFunctions = 6;
  data->modelData->modelDataXml.nProfileBlocks = 0;
  data->modelData->modelDataXml.nEquations = 240;
  data->modelData->nMixedSystems = 0;
  data->modelData->nLinearSystems = 4;
  data->modelData->nNonLinearSystems = 0;
  data->modelData->nStateSets = 0;
  data->modelData->nJacobians = 9;
  data->modelData->nOptimizeConstraints = 0;
  data->modelData->nOptimizeFinalConstraints = 0;
  
  data->modelData->nDelayExpressions = 0;
  
  data->modelData->nBaseClocks = 0;
  
  data->modelData->nSpatialDistributions = 0;
  
  data->modelData->nSensitivityVars = 0;
  data->modelData->nSensitivityParamVars = 0;
  data->modelData->nSetcVars = 0;
  data->modelData->ndataReconVars = 0;
  data->modelData->linearizationDumpLanguage =
  OMC_LINEARIZE_DUMP_LANGUAGE_MODELICA;
}

static int rml_execution_failed()
{
  fflush(NULL);
  fprintf(stderr, "Execution failed!\n");
  fflush(NULL);
  return 1;
}

#if defined(threadData)
#undef threadData
#endif
/* call the simulation runtime main from our main! */
int main(int argc, char**argv)
{
  /*
    Set the error functions to be used for simulation.
    The default value for them is 'functions' version. Change it here to 'simulation' versions
  */
  omc_assert = omc_assert_simulation;
  omc_assert_withEquationIndexes = omc_assert_simulation_withEquationIndexes;

  omc_assert_warning_withEquationIndexes = omc_assert_warning_simulation_withEquationIndexes;
  omc_assert_warning = omc_assert_warning_simulation;
  omc_terminate = omc_terminate_simulation;
  omc_throw = omc_throw_simulation;

  int res;
  DATA data;
  MODEL_DATA modelData;
  SIMULATION_INFO simInfo;
  data.modelData = &modelData;
  data.simulationInfo = &simInfo;
  measure_time_flag = 0;
  compiledInDAEMode = 0;
  compiledWithSymSolver = 0;
  MMC_INIT(0);
  omc_alloc_interface.init();
  {
    MMC_TRY_TOP()
  
    MMC_TRY_STACK()
  
    oc_latch_setupDataStruc(&data, threadData);
    res = _main_SimulationRuntime(argc, argv, &data, threadData);
    
    MMC_ELSE()
    rml_execution_failed();
    fprintf(stderr, "Stack overflow detected and was not caught.\nSend us a bug report at https://trac.openmodelica.org/OpenModelica/newticket\n    Include the following trace:\n");
    printStacktraceMessages();
    fflush(NULL);
    return 1;
    MMC_CATCH_STACK()
    
    MMC_CATCH_TOP(return rml_execution_failed());
  }

  fflush(NULL);
  EXIT(res);
  return res;
}

#ifdef __cplusplus
}
#endif


