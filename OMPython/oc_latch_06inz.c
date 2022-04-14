/* Initialization */
#include "oc_latch_model.h"
#include "oc_latch_11mix.h"
#include "oc_latch_12jac.h"
#if defined(__cplusplus)
extern "C" {
#endif

void oc_latch_functionInitialEquations_0(DATA *data, threadData_t *threadData);

/*
equation index: 1
type: SIMPLE_ASSIGN
opAmp.VMin.i = 0.0
*/
void oc_latch_eqFunction_1(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,1};
  (data->localData[0]->realVars[22]/* opAmp.VMin.i variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 2
type: SIMPLE_ASSIGN
opAmp1.VMin.i = 0.0
*/
void oc_latch_eqFunction_2(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,2};
  (data->localData[0]->realVars[29]/* opAmp1.VMin.i variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 3
type: SIMPLE_ASSIGN
signalVoltage.i = 0.0
*/
void oc_latch_eqFunction_3(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,3};
  (data->localData[0]->realVars[54]/* signalVoltage.i variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 4
type: SIMPLE_ASSIGN
opAmp.in_n.i = 0.0
*/
void oc_latch_eqFunction_4(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,4};
  (data->localData[0]->realVars[25]/* opAmp.in_n.i variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 5
type: SIMPLE_ASSIGN
opAmp1.in_p.i = 0.0
*/
void oc_latch_eqFunction_5(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,5};
  (data->localData[0]->realVars[33]/* opAmp1.in_p.i variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 6
type: SIMPLE_ASSIGN
capacitor.i = 0.0
*/
void oc_latch_eqFunction_6(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,6};
  (data->localData[0]->realVars[7]/* capacitor.i variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 7
type: SIMPLE_ASSIGN
opAmp.f = 2.0 / constantVoltage.V
*/
void oc_latch_eqFunction_7(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,7};
  (data->localData[0]->realVars[24]/* opAmp.f variable */)  = DIVISION_SIM(2.0,(data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */) ,"constantVoltage.V",equationIndexes);
  TRACE_POP
}

/*
equation index: 8
type: SIMPLE_ASSIGN
opAmp1.f = 2.0 / constantVoltage.V
*/
void oc_latch_eqFunction_8(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,8};
  (data->localData[0]->realVars[31]/* opAmp1.f variable */)  = DIVISION_SIM(2.0,(data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */) ,"constantVoltage.V",equationIndexes);
  TRACE_POP
}

/*
equation index: 9
type: SIMPLE_ASSIGN
resistor3.R_actual = resistor3.R * (1.0 + resistor3.alpha * (resistor3.T - resistor3.T_ref))
*/
void oc_latch_eqFunction_9(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,9};
  (data->localData[0]->realVars[51]/* resistor3.R_actual variable */)  = ((data->simulationInfo->realParameter[56]/* resistor3.R PARAM */) ) * (1.0 + ((data->simulationInfo->realParameter[60]/* resistor3.alpha PARAM */) ) * ((data->simulationInfo->realParameter[57]/* resistor3.T PARAM */)  - (data->simulationInfo->realParameter[59]/* resistor3.T_ref PARAM */) ));
  TRACE_POP
}

/*
equation index: 10
type: SIMPLE_ASSIGN
resistor2.R_actual = resistor2.R * (1.0 + resistor2.alpha * (resistor2.T - resistor2.T_ref))
*/
void oc_latch_eqFunction_10(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,10};
  (data->localData[0]->realVars[48]/* resistor2.R_actual variable */)  = ((data->simulationInfo->realParameter[50]/* resistor2.R PARAM */) ) * (1.0 + ((data->simulationInfo->realParameter[54]/* resistor2.alpha PARAM */) ) * ((data->simulationInfo->realParameter[51]/* resistor2.T PARAM */)  - (data->simulationInfo->realParameter[53]/* resistor2.T_ref PARAM */) ));
  TRACE_POP
}

/*
equation index: 11
type: SIMPLE_ASSIGN
resistor1.R_actual = resistor1.R * (1.0 + resistor1.alpha * (resistor1.T - resistor1.T_ref))
*/
void oc_latch_eqFunction_11(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,11};
  (data->localData[0]->realVars[44]/* resistor1.R_actual variable */)  = ((data->simulationInfo->realParameter[44]/* resistor1.R PARAM */) ) * (1.0 + ((data->simulationInfo->realParameter[48]/* resistor1.alpha PARAM */) ) * ((data->simulationInfo->realParameter[45]/* resistor1.T PARAM */)  - (data->simulationInfo->realParameter[47]/* resistor1.T_ref PARAM */) ));
  TRACE_POP
}

/*
equation index: 12
type: SIMPLE_ASSIGN
resistor.R_actual = resistor.R * (1.0 + resistor.alpha * (resistor.T - resistor.T_ref))
*/
void oc_latch_eqFunction_12(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,12};
  (data->localData[0]->realVars[40]/* resistor.R_actual variable */)  = ((data->simulationInfo->realParameter[38]/* resistor.R PARAM */) ) * (1.0 + ((data->simulationInfo->realParameter[42]/* resistor.alpha PARAM */) ) * ((data->simulationInfo->realParameter[39]/* resistor.T PARAM */)  - (data->simulationInfo->realParameter[41]/* resistor.T_ref PARAM */) ));
  TRACE_POP
}

/*
equation index: 13
type: SIMPLE_ASSIGN
R2.R_actual = R2.R * (1.0 + R2.alpha * (R2.T - R2.T_ref))
*/
void oc_latch_eqFunction_13(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,13};
  (data->localData[0]->realVars[4]/* R2.R_actual variable */)  = ((data->simulationInfo->realParameter[6]/* R2.R PARAM */) ) * (1.0 + ((data->simulationInfo->realParameter[10]/* R2.alpha PARAM */) ) * ((data->simulationInfo->realParameter[7]/* R2.T PARAM */)  - (data->simulationInfo->realParameter[9]/* R2.T_ref PARAM */) ));
  TRACE_POP
}

/*
equation index: 14
type: SIMPLE_ASSIGN
R1.R_actual = R1.R * (1.0 + R1.alpha * (R1.T - R1.T_ref))
*/
void oc_latch_eqFunction_14(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,14};
  (data->localData[0]->realVars[1]/* R1.R_actual variable */)  = ((data->simulationInfo->realParameter[0]/* R1.R PARAM */) ) * (1.0 + ((data->simulationInfo->realParameter[4]/* R1.alpha PARAM */) ) * ((data->simulationInfo->realParameter[1]/* R1.T PARAM */)  - (data->simulationInfo->realParameter[3]/* R1.T_ref PARAM */) ));
  TRACE_POP
}

/*
equation index: 15
type: SIMPLE_ASSIGN
opAmp.absSlope = if opAmp.Slope < 0.0 then -opAmp.Slope else opAmp.Slope
*/
void oc_latch_eqFunction_15(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,15};
  modelica_boolean tmp0;
  tmp0 = Less((data->simulationInfo->realParameter[34]/* opAmp.Slope PARAM */) ,0.0);
  (data->localData[0]->realVars[23]/* opAmp.absSlope variable */)  = (tmp0?(-(data->simulationInfo->realParameter[34]/* opAmp.Slope PARAM */) ):(data->simulationInfo->realParameter[34]/* opAmp.Slope PARAM */) );
  TRACE_POP
}

/*
equation index: 16
type: SIMPLE_ASSIGN
opAmp1.absSlope = if opAmp1.Slope < 0.0 then -opAmp1.Slope else opAmp1.Slope
*/
void oc_latch_eqFunction_16(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,16};
  modelica_boolean tmp1;
  tmp1 = Less((data->simulationInfo->realParameter[36]/* opAmp1.Slope PARAM */) ,0.0);
  (data->localData[0]->realVars[30]/* opAmp1.absSlope variable */)  = (tmp1?(-(data->simulationInfo->realParameter[36]/* opAmp1.Slope PARAM */) ):(data->simulationInfo->realParameter[36]/* opAmp1.Slope PARAM */) );
  TRACE_POP
}

/*
equation index: 23
type: LINEAR

<var>R2.v</var>
<row>

</row>
<matrix>
</matrix>
*/
OMC_DISABLE_OPT
void oc_latch_eqFunction_23(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,23};
  /* Linear equation system */
  int retValue;
  double aux_x[1] = { (data->localData[1]->realVars[6]/* R2.v variable */)  };
  if(ACTIVE_STREAM(LOG_DT))
  {
    infoStreamPrint(LOG_DT, 1, "Solving linear system 23 (STRICT TEARING SET if tearing enabled) at time = %18.10e", data->localData[0]->timeValue);
    messageClose(LOG_DT);
  }
  
  retValue = solve_linear_system(data, threadData, 0, &aux_x[0]);
  
  /* check if solution process was successful */
  if (retValue > 0){
    const int indexes[2] = {1,23};
    throwStreamPrintWithEquationIndexes(threadData, indexes, "Solving linear system 23 failed at time=%.15g.\nFor more information please use -lv LOG_LS.", data->localData[0]->timeValue);
  }
  /* write solution */
  (data->localData[0]->realVars[6]/* R2.v variable */)  = aux_x[0];

  TRACE_POP
}
extern void oc_latch_eqFunction_122(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_132(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_105(DATA *data, threadData_t *threadData);


/*
equation index: 33
type: LINEAR

<var>resistor3.v</var>
<row>

</row>
<matrix>
</matrix>
*/
OMC_DISABLE_OPT
void oc_latch_eqFunction_33(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,33};
  /* Linear equation system */
  int retValue;
  double aux_x[1] = { (data->localData[1]->realVars[53]/* resistor3.v variable */)  };
  if(ACTIVE_STREAM(LOG_DT))
  {
    infoStreamPrint(LOG_DT, 1, "Solving linear system 33 (STRICT TEARING SET if tearing enabled) at time = %18.10e", data->localData[0]->timeValue);
    messageClose(LOG_DT);
  }
  
  retValue = solve_linear_system(data, threadData, 1, &aux_x[0]);
  
  /* check if solution process was successful */
  if (retValue > 0){
    const int indexes[2] = {1,33};
    throwStreamPrintWithEquationIndexes(threadData, indexes, "Solving linear system 33 failed at time=%.15g.\nFor more information please use -lv LOG_LS.", data->localData[0]->timeValue);
  }
  /* write solution */
  (data->localData[0]->realVars[53]/* resistor3.v variable */)  = aux_x[0];

  TRACE_POP
}
extern void oc_latch_eqFunction_99(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_100(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_91(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_90(DATA *data, threadData_t *threadData);


/*
equation index: 38
type: SIMPLE_ASSIGN
combiTimeTable.nextTimeEventScaled = Modelica.Blocks.Tables.Internal.getNextTimeEvent(combiTimeTable.tableID, combiTimeTable.timeScaled)
*/
void oc_latch_eqFunction_38(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,38};
  (data->localData[0]->realVars[57]/* combiTimeTable.nextTimeEventScaled DISCRETE */)  = omc_Modelica_Blocks_Tables_Internal_getNextTimeEvent(threadData, (data->simulationInfo->extObjs[0]), (data->localData[0]->realVars[9]/* combiTimeTable.timeScaled variable */) );
  TRACE_POP
}

/*
equation index: 39
type: SIMPLE_ASSIGN
combiTimeTable.nextTimeEvent = if combiTimeTable.nextTimeEventScaled < 9.999999999999999e+59 then combiTimeTable.nextTimeEventScaled else 9.999999999999999e+59
*/
void oc_latch_eqFunction_39(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,39};
  modelica_boolean tmp2;
  tmp2 = Less((data->localData[0]->realVars[57]/* combiTimeTable.nextTimeEventScaled DISCRETE */) ,9.999999999999999e+59);
  (data->localData[0]->realVars[56]/* combiTimeTable.nextTimeEvent DISCRETE */)  = (tmp2?(data->localData[0]->realVars[57]/* combiTimeTable.nextTimeEventScaled DISCRETE */) :9.999999999999999e+59);
  TRACE_POP
}

/*
equation index: 40
type: SIMPLE_ASSIGN
$PRE.combiTimeTable.nextTimeEventScaled = 0.0
*/
void oc_latch_eqFunction_40(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,40};
  (data->simulationInfo->realVarsPre[57]/* combiTimeTable.nextTimeEventScaled DISCRETE */)  = 0.0;
  TRACE_POP
}

/*
equation index: 41
type: SIMPLE_ASSIGN
combiTimeTable.y[1] = Modelica.Blocks.Tables.Internal.getTimeTableValueNoDer(combiTimeTable.tableID, 1, combiTimeTable.timeScaled, combiTimeTable.nextTimeEventScaled, $PRE.combiTimeTable.nextTimeEventScaled)
*/
void oc_latch_eqFunction_41(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,41};
  (data->localData[0]->realVars[10]/* combiTimeTable.y[1] variable */)  = omc_Modelica_Blocks_Tables_Internal_getTimeTableValueNoDer(threadData, (data->simulationInfo->extObjs[0]), ((modelica_integer) 1), (data->localData[0]->realVars[9]/* combiTimeTable.timeScaled variable */) , (data->localData[0]->realVars[57]/* combiTimeTable.nextTimeEventScaled DISCRETE */) , (data->simulationInfo->realVarsPre[57]/* combiTimeTable.nextTimeEventScaled DISCRETE */) );
  TRACE_POP
}
extern void oc_latch_eqFunction_109(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_110(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_114(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_111(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_112(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_113(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_123(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_124(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_128(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_129(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_125(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_126(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_127(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_133(DATA *data, threadData_t *threadData);


/*
equation index: 56
type: SIMPLE_ASSIGN
$PRE.pre11.u = pre11.pre_u_start
*/
void oc_latch_eqFunction_56(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,56};
  (data->simulationInfo->booleanVarsPre[9]/* pre11.u DISCRETE */)  = (data->simulationInfo->booleanParameter[6]/* pre11.pre_u_start PARAM */) ;
  TRACE_POP
}

/*
equation index: 57
type: SIMPLE_ASSIGN
pre11.y = $PRE.pre11.u
*/
void oc_latch_eqFunction_57(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,57};
  (data->localData[0]->booleanVars[10]/* pre11.y DISCRETE */)  = (data->simulationInfo->booleanVarsPre[9]/* pre11.u DISCRETE */) ;
  TRACE_POP
}
extern void oc_latch_eqFunction_130(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_131(DATA *data, threadData_t *threadData);


/*
equation index: 60
type: SIMPLE_ASSIGN
$PRE.pre1.u = pre1.pre_u_start
*/
void oc_latch_eqFunction_60(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,60};
  (data->simulationInfo->booleanVarsPre[8]/* pre1.u DISCRETE */)  = (data->simulationInfo->booleanParameter[5]/* pre1.pre_u_start PARAM */) ;
  TRACE_POP
}

/*
equation index: 61
type: SIMPLE_ASSIGN
nor1.u1 = $PRE.pre1.u
*/
void oc_latch_eqFunction_61(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,61};
  (data->localData[0]->booleanVars[5]/* nor1.u1 DISCRETE */)  = (data->simulationInfo->booleanVarsPre[8]/* pre1.u DISCRETE */) ;
  TRACE_POP
}
extern void oc_latch_eqFunction_103(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_104(DATA *data, threadData_t *threadData);


/*
equation index: 64
type: SIMPLE_ASSIGN
ground.p.v = 0.0
*/
void oc_latch_eqFunction_64(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,64};
  (data->localData[0]->realVars[12]/* ground.p.v variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 65
type: SIMPLE_ASSIGN
opAmp.in_p.i = 0.0
*/
void oc_latch_eqFunction_65(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,65};
  (data->localData[0]->realVars[26]/* opAmp.in_p.i variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 66
type: SIMPLE_ASSIGN
opAmp.VMax.i = 0.0
*/
void oc_latch_eqFunction_66(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,66};
  (data->localData[0]->realVars[21]/* opAmp.VMax.i variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 67
type: SIMPLE_ASSIGN
ground1.p.v = 0.0
*/
void oc_latch_eqFunction_67(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,67};
  (data->localData[0]->realVars[13]/* ground1.p.v variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 68
type: SIMPLE_ASSIGN
ground2.p.v = 0.0
*/
void oc_latch_eqFunction_68(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,68};
  (data->localData[0]->realVars[14]/* ground2.p.v variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 69
type: SIMPLE_ASSIGN
ground3.p.v = 0.0
*/
void oc_latch_eqFunction_69(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,69};
  (data->localData[0]->realVars[16]/* ground3.p.v variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 70
type: SIMPLE_ASSIGN
ground4.p.v = 0.0
*/
void oc_latch_eqFunction_70(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,70};
  (data->localData[0]->realVars[17]/* ground4.p.v variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 71
type: SIMPLE_ASSIGN
potentialSensor.p.i = 0.0
*/
void oc_latch_eqFunction_71(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,71};
  (data->localData[0]->realVars[35]/* potentialSensor.p.i variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 72
type: SIMPLE_ASSIGN
opAmp1.in_n.i = 0.0
*/
void oc_latch_eqFunction_72(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,72};
  (data->localData[0]->realVars[32]/* opAmp1.in_n.i variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 73
type: SIMPLE_ASSIGN
opAmp1.VMax.i = 0.0
*/
void oc_latch_eqFunction_73(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,73};
  (data->localData[0]->realVars[28]/* opAmp1.VMax.i variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 74
type: SIMPLE_ASSIGN
ground5.p.v = 0.0
*/
void oc_latch_eqFunction_74(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,74};
  (data->localData[0]->realVars[19]/* ground5.p.v variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 75
type: SIMPLE_ASSIGN
potentialSensor1.p.i = 0.0
*/
void oc_latch_eqFunction_75(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,75};
  (data->localData[0]->realVars[37]/* potentialSensor1.p.i variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 76
type: SIMPLE_ASSIGN
ground6.p.v = 0.0
*/
void oc_latch_eqFunction_76(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,76};
  (data->localData[0]->realVars[20]/* ground6.p.v variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 77
type: SIMPLE_ASSIGN
capacitor.n.i = 0.0
*/
void oc_latch_eqFunction_77(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,77};
  (data->localData[0]->realVars[8]/* capacitor.n.i variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 78
type: SIMPLE_ASSIGN
signalVoltage.n.i = 0.0
*/
void oc_latch_eqFunction_78(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,78};
  (data->localData[0]->realVars[55]/* signalVoltage.n.i variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 79
type: SIMPLE_ASSIGN
ground5.p.i = 0.0
*/
void oc_latch_eqFunction_79(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,79};
  (data->localData[0]->realVars[18]/* ground5.p.i variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 80
type: SIMPLE_ASSIGN
ground3.p.i = 0.0
*/
void oc_latch_eqFunction_80(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,80};
  (data->localData[0]->realVars[15]/* ground3.p.i variable */)  = 0.0;
  TRACE_POP
}

/*
equation index: 81
type: SIMPLE_ASSIGN
$PRE.combiTimeTable.nextTimeEvent = 0.0
*/
void oc_latch_eqFunction_81(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,81};
  (data->simulationInfo->realVarsPre[56]/* combiTimeTable.nextTimeEvent DISCRETE */)  = 0.0;
  TRACE_POP
}

/*
equation index: 82
type: SIMPLE_ASSIGN
$whenCondition1 = time >= $PRE.combiTimeTable.nextTimeEvent
*/
void oc_latch_eqFunction_82(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,82};
  modelica_boolean tmp3;
  tmp3 = GreaterEq(data->localData[0]->timeValue,(data->simulationInfo->realVarsPre[56]/* combiTimeTable.nextTimeEvent DISCRETE */) );
  (data->localData[0]->booleanVars[0]/* $whenCondition1 DISCRETE */)  = tmp3;
  TRACE_POP
}

/*
equation index: 88
type: ALGORITHM

  assert(1.0 + resistor3.alpha * (resistor3.T - resistor3.T_ref) >= 1e-15, "Temperature outside scope of model!");
*/
void oc_latch_eqFunction_88(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,88};
  modelica_boolean tmp4;
  static const MMC_DEFSTRINGLIT(tmp5,35,"Temperature outside scope of model!");
  static int tmp6 = 0;
  {
    tmp4 = GreaterEq(1.0 + ((data->simulationInfo->realParameter[60]/* resistor3.alpha PARAM */) ) * ((data->simulationInfo->realParameter[57]/* resistor3.T PARAM */)  - (data->simulationInfo->realParameter[59]/* resistor3.T_ref PARAM */) ),1e-15);
    if(!tmp4)
    {
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\n1.0 + resistor3.alpha * (resistor3.T - resistor3.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp5)));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\n1.0 + resistor3.alpha * (resistor3.T - resistor3.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp5)));
        }
      }
    }
  }
  TRACE_POP
}

/*
equation index: 87
type: ALGORITHM

  assert(1.0 + resistor2.alpha * (resistor2.T - resistor2.T_ref) >= 1e-15, "Temperature outside scope of model!");
*/
void oc_latch_eqFunction_87(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,87};
  modelica_boolean tmp7;
  static const MMC_DEFSTRINGLIT(tmp8,35,"Temperature outside scope of model!");
  static int tmp9 = 0;
  {
    tmp7 = GreaterEq(1.0 + ((data->simulationInfo->realParameter[54]/* resistor2.alpha PARAM */) ) * ((data->simulationInfo->realParameter[51]/* resistor2.T PARAM */)  - (data->simulationInfo->realParameter[53]/* resistor2.T_ref PARAM */) ),1e-15);
    if(!tmp7)
    {
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\n1.0 + resistor2.alpha * (resistor2.T - resistor2.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp8)));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\n1.0 + resistor2.alpha * (resistor2.T - resistor2.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp8)));
        }
      }
    }
  }
  TRACE_POP
}

/*
equation index: 86
type: ALGORITHM

  assert(1.0 + resistor1.alpha * (resistor1.T - resistor1.T_ref) >= 1e-15, "Temperature outside scope of model!");
*/
void oc_latch_eqFunction_86(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,86};
  modelica_boolean tmp10;
  static const MMC_DEFSTRINGLIT(tmp11,35,"Temperature outside scope of model!");
  static int tmp12 = 0;
  {
    tmp10 = GreaterEq(1.0 + ((data->simulationInfo->realParameter[48]/* resistor1.alpha PARAM */) ) * ((data->simulationInfo->realParameter[45]/* resistor1.T PARAM */)  - (data->simulationInfo->realParameter[47]/* resistor1.T_ref PARAM */) ),1e-15);
    if(!tmp10)
    {
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\n1.0 + resistor1.alpha * (resistor1.T - resistor1.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp11)));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\n1.0 + resistor1.alpha * (resistor1.T - resistor1.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp11)));
        }
      }
    }
  }
  TRACE_POP
}

/*
equation index: 85
type: ALGORITHM

  assert(1.0 + resistor.alpha * (resistor.T - resistor.T_ref) >= 1e-15, "Temperature outside scope of model!");
*/
void oc_latch_eqFunction_85(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,85};
  modelica_boolean tmp13;
  static const MMC_DEFSTRINGLIT(tmp14,35,"Temperature outside scope of model!");
  static int tmp15 = 0;
  {
    tmp13 = GreaterEq(1.0 + ((data->simulationInfo->realParameter[42]/* resistor.alpha PARAM */) ) * ((data->simulationInfo->realParameter[39]/* resistor.T PARAM */)  - (data->simulationInfo->realParameter[41]/* resistor.T_ref PARAM */) ),1e-15);
    if(!tmp13)
    {
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\n1.0 + resistor.alpha * (resistor.T - resistor.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp14)));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\n1.0 + resistor.alpha * (resistor.T - resistor.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp14)));
        }
      }
    }
  }
  TRACE_POP
}

/*
equation index: 84
type: ALGORITHM

  assert(1.0 + R2.alpha * (R2.T - R2.T_ref) >= 1e-15, "Temperature outside scope of model!");
*/
void oc_latch_eqFunction_84(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,84};
  modelica_boolean tmp16;
  static const MMC_DEFSTRINGLIT(tmp17,35,"Temperature outside scope of model!");
  static int tmp18 = 0;
  {
    tmp16 = GreaterEq(1.0 + ((data->simulationInfo->realParameter[10]/* R2.alpha PARAM */) ) * ((data->simulationInfo->realParameter[7]/* R2.T PARAM */)  - (data->simulationInfo->realParameter[9]/* R2.T_ref PARAM */) ),1e-15);
    if(!tmp16)
    {
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\n1.0 + R2.alpha * (R2.T - R2.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp17)));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\n1.0 + R2.alpha * (R2.T - R2.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp17)));
        }
      }
    }
  }
  TRACE_POP
}

/*
equation index: 83
type: ALGORITHM

  assert(1.0 + R1.alpha * (R1.T - R1.T_ref) >= 1e-15, "Temperature outside scope of model!");
*/
void oc_latch_eqFunction_83(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,83};
  modelica_boolean tmp19;
  static const MMC_DEFSTRINGLIT(tmp20,35,"Temperature outside scope of model!");
  static int tmp21 = 0;
  {
    tmp19 = GreaterEq(1.0 + ((data->simulationInfo->realParameter[4]/* R1.alpha PARAM */) ) * ((data->simulationInfo->realParameter[1]/* R1.T PARAM */)  - (data->simulationInfo->realParameter[3]/* R1.T_ref PARAM */) ),1e-15);
    if(!tmp19)
    {
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\n1.0 + R1.alpha * (R1.T - R1.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp20)));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\n1.0 + R1.alpha * (R1.T - R1.T_ref) >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp20)));
        }
      }
    }
  }
  TRACE_POP
}
OMC_DISABLE_OPT
void oc_latch_functionInitialEquations_0(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  oc_latch_eqFunction_1(data, threadData);
  oc_latch_eqFunction_2(data, threadData);
  oc_latch_eqFunction_3(data, threadData);
  oc_latch_eqFunction_4(data, threadData);
  oc_latch_eqFunction_5(data, threadData);
  oc_latch_eqFunction_6(data, threadData);
  oc_latch_eqFunction_7(data, threadData);
  oc_latch_eqFunction_8(data, threadData);
  oc_latch_eqFunction_9(data, threadData);
  oc_latch_eqFunction_10(data, threadData);
  oc_latch_eqFunction_11(data, threadData);
  oc_latch_eqFunction_12(data, threadData);
  oc_latch_eqFunction_13(data, threadData);
  oc_latch_eqFunction_14(data, threadData);
  oc_latch_eqFunction_15(data, threadData);
  oc_latch_eqFunction_16(data, threadData);
  oc_latch_eqFunction_23(data, threadData);
  oc_latch_eqFunction_122(data, threadData);
  oc_latch_eqFunction_132(data, threadData);
  oc_latch_eqFunction_105(data, threadData);
  oc_latch_eqFunction_33(data, threadData);
  oc_latch_eqFunction_99(data, threadData);
  oc_latch_eqFunction_100(data, threadData);
  oc_latch_eqFunction_91(data, threadData);
  oc_latch_eqFunction_90(data, threadData);
  oc_latch_eqFunction_38(data, threadData);
  oc_latch_eqFunction_39(data, threadData);
  oc_latch_eqFunction_40(data, threadData);
  oc_latch_eqFunction_41(data, threadData);
  oc_latch_eqFunction_109(data, threadData);
  oc_latch_eqFunction_110(data, threadData);
  oc_latch_eqFunction_114(data, threadData);
  oc_latch_eqFunction_111(data, threadData);
  oc_latch_eqFunction_112(data, threadData);
  oc_latch_eqFunction_113(data, threadData);
  oc_latch_eqFunction_123(data, threadData);
  oc_latch_eqFunction_124(data, threadData);
  oc_latch_eqFunction_128(data, threadData);
  oc_latch_eqFunction_129(data, threadData);
  oc_latch_eqFunction_125(data, threadData);
  oc_latch_eqFunction_126(data, threadData);
  oc_latch_eqFunction_127(data, threadData);
  oc_latch_eqFunction_133(data, threadData);
  oc_latch_eqFunction_56(data, threadData);
  oc_latch_eqFunction_57(data, threadData);
  oc_latch_eqFunction_130(data, threadData);
  oc_latch_eqFunction_131(data, threadData);
  oc_latch_eqFunction_60(data, threadData);
  oc_latch_eqFunction_61(data, threadData);
  oc_latch_eqFunction_103(data, threadData);
  oc_latch_eqFunction_104(data, threadData);
  oc_latch_eqFunction_64(data, threadData);
  oc_latch_eqFunction_65(data, threadData);
  oc_latch_eqFunction_66(data, threadData);
  oc_latch_eqFunction_67(data, threadData);
  oc_latch_eqFunction_68(data, threadData);
  oc_latch_eqFunction_69(data, threadData);
  oc_latch_eqFunction_70(data, threadData);
  oc_latch_eqFunction_71(data, threadData);
  oc_latch_eqFunction_72(data, threadData);
  oc_latch_eqFunction_73(data, threadData);
  oc_latch_eqFunction_74(data, threadData);
  oc_latch_eqFunction_75(data, threadData);
  oc_latch_eqFunction_76(data, threadData);
  oc_latch_eqFunction_77(data, threadData);
  oc_latch_eqFunction_78(data, threadData);
  oc_latch_eqFunction_79(data, threadData);
  oc_latch_eqFunction_80(data, threadData);
  oc_latch_eqFunction_81(data, threadData);
  oc_latch_eqFunction_82(data, threadData);
  oc_latch_eqFunction_88(data, threadData);
  oc_latch_eqFunction_87(data, threadData);
  oc_latch_eqFunction_86(data, threadData);
  oc_latch_eqFunction_85(data, threadData);
  oc_latch_eqFunction_84(data, threadData);
  oc_latch_eqFunction_83(data, threadData);
  TRACE_POP
}

int oc_latch_functionInitialEquations(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH

  data->simulationInfo->discreteCall = 1;
  oc_latch_functionInitialEquations_0(data, threadData);
  data->simulationInfo->discreteCall = 0;
  
  TRACE_POP
  return 0;
}

/* No oc_latch_functionInitialEquations_lambda0 function */

int oc_latch_functionRemovedInitialEquations(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int *equationIndexes = NULL;
  double res = 0.0;

  
  TRACE_POP
  return 0;
}


#if defined(__cplusplus)
}
#endif

