/* Events: Sample, Zero Crossings, Relations, Discrete Changes */
#include "oc_latch_model.h"
#if defined(__cplusplus)
extern "C" {
#endif

/* Initializes the raw time events of the simulation using the now
   calcualted parameters. */
void oc_latch_function_initSample(DATA *data, threadData_t *threadData)
{
  long i=0;
}

const char *oc_latch_zeroCrossingDescription(int i, int **out_EquationIndexes)
{
  static const char *res[] = {"potentialSensor.phi >= greaterEqualThreshold.threshold",
  "potentialSensor1.phi >= greaterEqualThreshold1.threshold",
  "time <= 0.1 or time >= 0.9",
  "time >= 0.95 and time <= 0.96",
  "time >= pre(combiTimeTable.nextTimeEvent)"};
  static const int occurEqs0[] = {1,128};
  static const int occurEqs1[] = {1,114};
  static const int occurEqs2[] = {1,91};
  static const int occurEqs3[] = {1,90};
  static const int occurEqs4[] = {1,89};
  static const int *occurEqs[] = {occurEqs0,occurEqs1,occurEqs2,occurEqs3,occurEqs4};
  *out_EquationIndexes = (int*) occurEqs[i];
  return res[i];
}

/* forwarded equations */
extern void oc_latch_eqFunction_89(DATA* data, threadData_t *threadData);
extern void oc_latch_eqFunction_98(DATA* data, threadData_t *threadData);
extern void oc_latch_eqFunction_105(DATA* data, threadData_t *threadData);
extern void oc_latch_eqFunction_107(DATA* data, threadData_t *threadData);
extern void oc_latch_eqFunction_109(DATA* data, threadData_t *threadData);
extern void oc_latch_eqFunction_110(DATA* data, threadData_t *threadData);
extern void oc_latch_eqFunction_121(DATA* data, threadData_t *threadData);
extern void oc_latch_eqFunction_123(DATA* data, threadData_t *threadData);
extern void oc_latch_eqFunction_124(DATA* data, threadData_t *threadData);

int oc_latch_function_ZeroCrossingsEquations(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH

  data->simulationInfo->callStatistics.functionZeroCrossingsEquations++;

  oc_latch_eqFunction_89(data, threadData);

  oc_latch_eqFunction_98(data, threadData);

  oc_latch_eqFunction_105(data, threadData);

  oc_latch_eqFunction_107(data, threadData);

  oc_latch_eqFunction_109(data, threadData);

  oc_latch_eqFunction_110(data, threadData);

  oc_latch_eqFunction_121(data, threadData);

  oc_latch_eqFunction_123(data, threadData);

  oc_latch_eqFunction_124(data, threadData);
  
  TRACE_POP
  return 0;
}

int oc_latch_function_ZeroCrossings(DATA *data, threadData_t *threadData, double *gout)
{
  TRACE_PUSH
  const int *equationIndexes = NULL;

  modelica_boolean tmp0;
  modelica_boolean tmp1;
  modelica_boolean tmp2;
  modelica_boolean tmp3;
  modelica_boolean tmp4;
  modelica_boolean tmp5;
  modelica_boolean tmp6;

#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_tick(SIM_TIMER_ZC);
#endif
  data->simulationInfo->callStatistics.functionZeroCrossings++;

  tmp0 = GreaterEqZC((data->localData[0]->realVars[36]/* potentialSensor.phi variable */) , (data->simulationInfo->realParameter[32]/* greaterEqualThreshold.threshold PARAM */) , data->simulationInfo->storedRelations[0]);
  gout[0] = (tmp0) ? 1 : -1;
  tmp1 = GreaterEqZC((data->localData[0]->realVars[38]/* potentialSensor1.phi variable */) , (data->simulationInfo->realParameter[33]/* greaterEqualThreshold1.threshold PARAM */) , data->simulationInfo->storedRelations[1]);
  gout[1] = (tmp1) ? 1 : -1;
  tmp2 = LessEqZC(data->localData[0]->timeValue, 0.1, data->simulationInfo->storedRelations[2]);
  tmp3 = GreaterEqZC(data->localData[0]->timeValue, 0.9, data->simulationInfo->storedRelations[3]);
  gout[2] = ((tmp2 || tmp3)) ? 1 : -1;
  tmp4 = GreaterEqZC(data->localData[0]->timeValue, 0.95, data->simulationInfo->storedRelations[4]);
  tmp5 = LessEqZC(data->localData[0]->timeValue, 0.96, data->simulationInfo->storedRelations[5]);
  gout[3] = ((tmp4 && tmp5)) ? 1 : -1;
  tmp6 = GreaterEqZC(data->localData[0]->timeValue, (data->simulationInfo->realVarsPre[56]/* combiTimeTable.nextTimeEvent DISCRETE */) , data->simulationInfo->storedRelations[6]);
  gout[4] = (tmp6) ? 1 : -1;

#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_accumulate(SIM_TIMER_ZC);
#endif

  TRACE_POP
  return 0;
}

const char *oc_latch_relationDescription(int i)
{
  const char *res[] = {"potentialSensor.phi >= greaterEqualThreshold.threshold",
  "potentialSensor1.phi >= greaterEqualThreshold1.threshold",
  "time <= 0.1",
  "time >= 0.9",
  "time >= 0.95",
  "time <= 0.96",
  "time >= pre(combiTimeTable.nextTimeEvent)"};
  return res[i];
}

int oc_latch_function_updateRelations(DATA *data, threadData_t *threadData, int evalforZeroCross)
{
  TRACE_PUSH
  const int *equationIndexes = NULL;

  modelica_boolean tmp7;
  modelica_boolean tmp8;
  modelica_boolean tmp9;
  modelica_boolean tmp10;
  modelica_boolean tmp11;
  modelica_boolean tmp12;
  modelica_boolean tmp13;
  
  if(evalforZeroCross) {
    tmp7 = GreaterEqZC((data->localData[0]->realVars[36]/* potentialSensor.phi variable */) , (data->simulationInfo->realParameter[32]/* greaterEqualThreshold.threshold PARAM */) , data->simulationInfo->storedRelations[0]);
    data->simulationInfo->relations[0] = tmp7;
    tmp8 = GreaterEqZC((data->localData[0]->realVars[38]/* potentialSensor1.phi variable */) , (data->simulationInfo->realParameter[33]/* greaterEqualThreshold1.threshold PARAM */) , data->simulationInfo->storedRelations[1]);
    data->simulationInfo->relations[1] = tmp8;
    tmp9 = LessEqZC(data->localData[0]->timeValue, 0.1, data->simulationInfo->storedRelations[2]);
    data->simulationInfo->relations[2] = tmp9;
    tmp10 = GreaterEqZC(data->localData[0]->timeValue, 0.9, data->simulationInfo->storedRelations[3]);
    data->simulationInfo->relations[3] = tmp10;
    tmp11 = GreaterEqZC(data->localData[0]->timeValue, 0.95, data->simulationInfo->storedRelations[4]);
    data->simulationInfo->relations[4] = tmp11;
    tmp12 = LessEqZC(data->localData[0]->timeValue, 0.96, data->simulationInfo->storedRelations[5]);
    data->simulationInfo->relations[5] = tmp12;
    tmp13 = GreaterEqZC(data->localData[0]->timeValue, (data->simulationInfo->realVarsPre[56]/* combiTimeTable.nextTimeEvent DISCRETE */) , data->simulationInfo->storedRelations[6]);
    data->simulationInfo->relations[6] = tmp13;
  } else {
    data->simulationInfo->relations[0] = ((data->localData[0]->realVars[36]/* potentialSensor.phi variable */)  >= (data->simulationInfo->realParameter[32]/* greaterEqualThreshold.threshold PARAM */) );
    data->simulationInfo->relations[1] = ((data->localData[0]->realVars[38]/* potentialSensor1.phi variable */)  >= (data->simulationInfo->realParameter[33]/* greaterEqualThreshold1.threshold PARAM */) );
    data->simulationInfo->relations[2] = (data->localData[0]->timeValue <= 0.1);
    data->simulationInfo->relations[3] = (data->localData[0]->timeValue >= 0.9);
    data->simulationInfo->relations[4] = (data->localData[0]->timeValue >= 0.95);
    data->simulationInfo->relations[5] = (data->localData[0]->timeValue <= 0.96);
    data->simulationInfo->relations[6] = (data->localData[0]->timeValue >= (data->simulationInfo->realVarsPre[56]/* combiTimeTable.nextTimeEvent DISCRETE */) );
  }
  
  TRACE_POP
  return 0;
}

#if defined(__cplusplus)
}
#endif

