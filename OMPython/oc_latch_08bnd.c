/* update bound parameters and variable attributes (start, nominal, min, max) */
#include "oc_latch_model.h"
#if defined(__cplusplus)
extern "C" {
#endif

OMC_DISABLE_OPT
int oc_latch_updateBoundVariableAttributes(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  /* min ******************************************************** */
  
  infoStreamPrint(LOG_INIT, 1, "updating min-values");
  if (ACTIVE_STREAM(LOG_INIT)) messageClose(LOG_INIT);
  
  /* max ******************************************************** */
  
  infoStreamPrint(LOG_INIT, 1, "updating max-values");
  if (ACTIVE_STREAM(LOG_INIT)) messageClose(LOG_INIT);
  
  /* nominal **************************************************** */
  
  infoStreamPrint(LOG_INIT, 1, "updating nominal-values");
  if (ACTIVE_STREAM(LOG_INIT)) messageClose(LOG_INIT);
  
  /* start ****************************************************** */
  infoStreamPrint(LOG_INIT, 1, "updating primary start-values");
  if (ACTIVE_STREAM(LOG_INIT)) messageClose(LOG_INIT);
  
  TRACE_POP
  return 0;
}

void oc_latch_updateBoundParameters_0(DATA *data, threadData_t *threadData);

/*
equation index: 140
type: SIMPLE_ASSIGN
combiTimeTable.shiftTime = combiTimeTable.startTime
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_140(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,140};
  (data->simulationInfo->realParameter[16]/* combiTimeTable.shiftTime PARAM */)  = (data->simulationInfo->realParameter[17]/* combiTimeTable.startTime PARAM */) ;
  TRACE_POP
}

/*
equation index: 141
type: SIMPLE_ASSIGN
combiTimeTable.tableID = Modelica.Blocks.Types.ExternalCombiTimeTable.constructor("NoName", "NoName", combiTimeTable.table, combiTimeTable.startTime, {2}, Modelica.Blocks.Types.Smoothness.ConstantSegments, Modelica.Blocks.Types.Extrapolation.HoldLastPoint, combiTimeTable.shiftTime, Modelica.Blocks.Types.TimeEvents.Always, false)
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_141(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,141};
  real_array tmp0;
  real_array_create(&tmp0, ((modelica_real*)&((&data->simulationInfo->realParameter[22]/* combiTimeTable.table[1,1] PARAM */)[(((modelica_integer) 1) - 1) * 2 + (((modelica_integer) 1)-1)] )), 2, (_index_t)3, (_index_t)2);
  (data->simulationInfo->extObjs[0]) = omc_Modelica_Blocks_Types_ExternalCombiTimeTable_constructor(threadData, _OMC_LIT2, _OMC_LIT2, tmp0, (data->simulationInfo->realParameter[17]/* combiTimeTable.startTime PARAM */) , _OMC_LIT3, 3, 1, (data->simulationInfo->realParameter[16]/* combiTimeTable.shiftTime PARAM */) , 1, 0);
  TRACE_POP
}

/*
equation index: 142
type: SIMPLE_ASSIGN
capacitor.v = constantVoltage.V
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_142(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,142};
  (data->simulationInfo->realParameter[13]/* capacitor.v PARAM */)  = (data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */) ;
  TRACE_POP
}

/*
equation index: 143
type: SIMPLE_ASSIGN
resistor2.p.v = constantVoltage.V
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_143(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,143};
  (data->simulationInfo->realParameter[55]/* resistor2.p.v PARAM */)  = (data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */) ;
  TRACE_POP
}

/*
equation index: 144
type: SIMPLE_ASSIGN
constantVoltage.p.v = constantVoltage.V
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_144(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,144};
  (data->simulationInfo->realParameter[30]/* constantVoltage.p.v PARAM */)  = (data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */) ;
  TRACE_POP
}

/*
equation index: 145
type: SIMPLE_ASSIGN
opAmp1.VMax.v = constantVoltage.V
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_145(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,145};
  (data->simulationInfo->realParameter[37]/* opAmp1.VMax.v PARAM */)  = (data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */) ;
  TRACE_POP
}

/*
equation index: 146
type: SIMPLE_ASSIGN
resistor1.p.v = constantVoltage.V
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_146(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,146};
  (data->simulationInfo->realParameter[49]/* resistor1.p.v PARAM */)  = (data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */) ;
  TRACE_POP
}

/*
equation index: 147
type: SIMPLE_ASSIGN
resistor.p.v = constantVoltage.V
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_147(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,147};
  (data->simulationInfo->realParameter[43]/* resistor.p.v PARAM */)  = (data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */) ;
  TRACE_POP
}

/*
equation index: 148
type: SIMPLE_ASSIGN
opAmp.VMax.v = constantVoltage.V
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_148(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,148};
  (data->simulationInfo->realParameter[35]/* opAmp.VMax.v PARAM */)  = (data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */) ;
  TRACE_POP
}

/*
equation index: 149
type: SIMPLE_ASSIGN
R1.p.v = constantVoltage.V
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_149(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,149};
  (data->simulationInfo->realParameter[5]/* R1.p.v PARAM */)  = (data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */) ;
  TRACE_POP
}

/*
equation index: 150
type: SIMPLE_ASSIGN
capacitor.p.v = constantVoltage.V
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_150(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,150};
  (data->simulationInfo->realParameter[12]/* capacitor.p.v PARAM */)  = (data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */) ;
  TRACE_POP
}

/*
equation index: 151
type: SIMPLE_ASSIGN
constantVoltage.v = constantVoltage.V
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_151(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,151};
  (data->simulationInfo->realParameter[31]/* constantVoltage.v PARAM */)  = (data->simulationInfo->realParameter[29]/* constantVoltage.V PARAM */) ;
  TRACE_POP
}

/*
equation index: 152
type: SIMPLE_ASSIGN
R1.T = R1.T_ref
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_152(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,152};
  (data->simulationInfo->realParameter[1]/* R1.T PARAM */)  = (data->simulationInfo->realParameter[3]/* R1.T_ref PARAM */) ;
  TRACE_POP
}

/*
equation index: 153
type: SIMPLE_ASSIGN
R1.T_heatPort = R1.T
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_153(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,153};
  (data->simulationInfo->realParameter[2]/* R1.T_heatPort PARAM */)  = (data->simulationInfo->realParameter[1]/* R1.T PARAM */) ;
  TRACE_POP
}

/*
equation index: 154
type: SIMPLE_ASSIGN
R2.T = R2.T_ref
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_154(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,154};
  (data->simulationInfo->realParameter[7]/* R2.T PARAM */)  = (data->simulationInfo->realParameter[9]/* R2.T_ref PARAM */) ;
  TRACE_POP
}

/*
equation index: 155
type: SIMPLE_ASSIGN
R2.T_heatPort = R2.T
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_155(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,155};
  (data->simulationInfo->realParameter[8]/* R2.T_heatPort PARAM */)  = (data->simulationInfo->realParameter[7]/* R2.T PARAM */) ;
  TRACE_POP
}

/*
equation index: 156
type: SIMPLE_ASSIGN
resistor.T = resistor.T_ref
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_156(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,156};
  (data->simulationInfo->realParameter[39]/* resistor.T PARAM */)  = (data->simulationInfo->realParameter[41]/* resistor.T_ref PARAM */) ;
  TRACE_POP
}

/*
equation index: 157
type: SIMPLE_ASSIGN
resistor.T_heatPort = resistor.T
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_157(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,157};
  (data->simulationInfo->realParameter[40]/* resistor.T_heatPort PARAM */)  = (data->simulationInfo->realParameter[39]/* resistor.T PARAM */) ;
  TRACE_POP
}

/*
equation index: 158
type: SIMPLE_ASSIGN
resistor1.T = resistor1.T_ref
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_158(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,158};
  (data->simulationInfo->realParameter[45]/* resistor1.T PARAM */)  = (data->simulationInfo->realParameter[47]/* resistor1.T_ref PARAM */) ;
  TRACE_POP
}

/*
equation index: 159
type: SIMPLE_ASSIGN
resistor1.T_heatPort = resistor1.T
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_159(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,159};
  (data->simulationInfo->realParameter[46]/* resistor1.T_heatPort PARAM */)  = (data->simulationInfo->realParameter[45]/* resistor1.T PARAM */) ;
  TRACE_POP
}

/*
equation index: 160
type: SIMPLE_ASSIGN
resistor2.T = resistor2.T_ref
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_160(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,160};
  (data->simulationInfo->realParameter[51]/* resistor2.T PARAM */)  = (data->simulationInfo->realParameter[53]/* resistor2.T_ref PARAM */) ;
  TRACE_POP
}

/*
equation index: 161
type: SIMPLE_ASSIGN
resistor2.T_heatPort = resistor2.T
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_161(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,161};
  (data->simulationInfo->realParameter[52]/* resistor2.T_heatPort PARAM */)  = (data->simulationInfo->realParameter[51]/* resistor2.T PARAM */) ;
  TRACE_POP
}

/*
equation index: 162
type: SIMPLE_ASSIGN
resistor3.T = resistor3.T_ref
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_162(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,162};
  (data->simulationInfo->realParameter[57]/* resistor3.T PARAM */)  = (data->simulationInfo->realParameter[59]/* resistor3.T_ref PARAM */) ;
  TRACE_POP
}

/*
equation index: 163
type: SIMPLE_ASSIGN
resistor3.T_heatPort = resistor3.T
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_163(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,163};
  (data->simulationInfo->realParameter[58]/* resistor3.T_heatPort PARAM */)  = (data->simulationInfo->realParameter[57]/* resistor3.T PARAM */) ;
  TRACE_POP
}

/*
equation index: 171
type: SIMPLE_ASSIGN
combiTimeTable.t_maxScaled = Modelica.Blocks.Tables.Internal.getTimeTableTmax(combiTimeTable.tableID)
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_171(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,171};
  (data->simulationInfo->realParameter[19]/* combiTimeTable.t_maxScaled PARAM */)  = omc_Modelica_Blocks_Tables_Internal_getTimeTableTmax(threadData, (data->simulationInfo->extObjs[0]));
  TRACE_POP
}

/*
equation index: 172
type: SIMPLE_ASSIGN
combiTimeTable.t_minScaled = Modelica.Blocks.Tables.Internal.getTimeTableTmin(combiTimeTable.tableID)
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_172(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,172};
  (data->simulationInfo->realParameter[21]/* combiTimeTable.t_minScaled PARAM */)  = omc_Modelica_Blocks_Tables_Internal_getTimeTableTmin(threadData, (data->simulationInfo->extObjs[0]));
  TRACE_POP
}

/*
equation index: 173
type: SIMPLE_ASSIGN
combiTimeTable.t_max = combiTimeTable.t_maxScaled
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_173(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,173};
  (data->simulationInfo->realParameter[18]/* combiTimeTable.t_max PARAM */)  = (data->simulationInfo->realParameter[19]/* combiTimeTable.t_maxScaled PARAM */) ;
  TRACE_POP
}

/*
equation index: 174
type: SIMPLE_ASSIGN
combiTimeTable.t_min = combiTimeTable.t_minScaled
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_174(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,174};
  (data->simulationInfo->realParameter[20]/* combiTimeTable.t_min PARAM */)  = (data->simulationInfo->realParameter[21]/* combiTimeTable.t_minScaled PARAM */) ;
  TRACE_POP
}
extern void oc_latch_eqFunction_76(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_75(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_74(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_16(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_73(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_72(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_71(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_70(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_69(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_68(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_67(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_15(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_66(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_65(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_64(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_14(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_13(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_12(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_11(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_10(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_9(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_8(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_7(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_6(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_5(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_4(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_3(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_2(DATA *data, threadData_t *threadData);

extern void oc_latch_eqFunction_1(DATA *data, threadData_t *threadData);


/*
equation index: 216
type: ALGORITHM

  assert(R1.T_ref >= 0.0, "Variable violating min constraint: 0.0 <= R1.T_ref, has value: " + String(R1.T_ref, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_216(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,216};
  modelica_boolean tmp1;
  static const MMC_DEFSTRINGLIT(tmp2,63,"Variable violating min constraint: 0.0 <= R1.T_ref, has value: ");
  modelica_string tmp3;
  modelica_metatype tmpMeta4;
  static int tmp5 = 0;
  if(!tmp5)
  {
    tmp1 = GreaterEq((data->simulationInfo->realParameter[3]/* R1.T_ref PARAM */) ,0.0);
    if(!tmp1)
    {
      tmp3 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[3]/* R1.T_ref PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta4 = stringAppend(MMC_REFSTRINGLIT(tmp2),tmp3);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nR1.T_ref >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta4));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",5,3,5,64,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nR1.T_ref >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta4));
        }
      }
      tmp5 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 217
type: ALGORITHM

  assert(R1.T >= 0.0, "Variable violating min constraint: 0.0 <= R1.T, has value: " + String(R1.T, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_217(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,217};
  modelica_boolean tmp6;
  static const MMC_DEFSTRINGLIT(tmp7,59,"Variable violating min constraint: 0.0 <= R1.T, has value: ");
  modelica_string tmp8;
  modelica_metatype tmpMeta9;
  static int tmp10 = 0;
  if(!tmp10)
  {
    tmp6 = GreaterEq((data->simulationInfo->realParameter[1]/* R1.T PARAM */) ,0.0);
    if(!tmp6)
    {
      tmp8 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[1]/* R1.T PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta9 = stringAppend(MMC_REFSTRINGLIT(tmp7),tmp8);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nR1.T >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta9));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Interfaces/ConditionalHeatPort.mo",7,3,8,97,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nR1.T >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta9));
        }
      }
      tmp10 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 218
type: ALGORITHM

  assert(R1.T_heatPort >= 0.0, "Variable violating min constraint: 0.0 <= R1.T_heatPort, has value: " + String(R1.T_heatPort, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_218(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,218};
  modelica_boolean tmp11;
  static const MMC_DEFSTRINGLIT(tmp12,68,"Variable violating min constraint: 0.0 <= R1.T_heatPort, has value: ");
  modelica_string tmp13;
  modelica_metatype tmpMeta14;
  static int tmp15 = 0;
  if(!tmp15)
  {
    tmp11 = GreaterEq((data->simulationInfo->realParameter[2]/* R1.T_heatPort PARAM */) ,0.0);
    if(!tmp11)
    {
      tmp13 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[2]/* R1.T_heatPort PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta14 = stringAppend(MMC_REFSTRINGLIT(tmp12),tmp13);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nR1.T_heatPort >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta14));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Interfaces/ConditionalHeatPort.mo",14,3,14,54,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nR1.T_heatPort >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta14));
        }
      }
      tmp15 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 219
type: ALGORITHM

  assert(R2.T_ref >= 0.0, "Variable violating min constraint: 0.0 <= R2.T_ref, has value: " + String(R2.T_ref, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_219(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,219};
  modelica_boolean tmp16;
  static const MMC_DEFSTRINGLIT(tmp17,63,"Variable violating min constraint: 0.0 <= R2.T_ref, has value: ");
  modelica_string tmp18;
  modelica_metatype tmpMeta19;
  static int tmp20 = 0;
  if(!tmp20)
  {
    tmp16 = GreaterEq((data->simulationInfo->realParameter[9]/* R2.T_ref PARAM */) ,0.0);
    if(!tmp16)
    {
      tmp18 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[9]/* R2.T_ref PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta19 = stringAppend(MMC_REFSTRINGLIT(tmp17),tmp18);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nR2.T_ref >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta19));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",5,3,5,64,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nR2.T_ref >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta19));
        }
      }
      tmp20 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 220
type: ALGORITHM

  assert(R2.T >= 0.0, "Variable violating min constraint: 0.0 <= R2.T, has value: " + String(R2.T, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_220(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,220};
  modelica_boolean tmp21;
  static const MMC_DEFSTRINGLIT(tmp22,59,"Variable violating min constraint: 0.0 <= R2.T, has value: ");
  modelica_string tmp23;
  modelica_metatype tmpMeta24;
  static int tmp25 = 0;
  if(!tmp25)
  {
    tmp21 = GreaterEq((data->simulationInfo->realParameter[7]/* R2.T PARAM */) ,0.0);
    if(!tmp21)
    {
      tmp23 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[7]/* R2.T PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta24 = stringAppend(MMC_REFSTRINGLIT(tmp22),tmp23);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nR2.T >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta24));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Interfaces/ConditionalHeatPort.mo",7,3,8,97,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nR2.T >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta24));
        }
      }
      tmp25 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 221
type: ALGORITHM

  assert(R2.T_heatPort >= 0.0, "Variable violating min constraint: 0.0 <= R2.T_heatPort, has value: " + String(R2.T_heatPort, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_221(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,221};
  modelica_boolean tmp26;
  static const MMC_DEFSTRINGLIT(tmp27,68,"Variable violating min constraint: 0.0 <= R2.T_heatPort, has value: ");
  modelica_string tmp28;
  modelica_metatype tmpMeta29;
  static int tmp30 = 0;
  if(!tmp30)
  {
    tmp26 = GreaterEq((data->simulationInfo->realParameter[8]/* R2.T_heatPort PARAM */) ,0.0);
    if(!tmp26)
    {
      tmp28 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[8]/* R2.T_heatPort PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta29 = stringAppend(MMC_REFSTRINGLIT(tmp27),tmp28);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nR2.T_heatPort >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta29));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Interfaces/ConditionalHeatPort.mo",14,3,14,54,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nR2.T_heatPort >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta29));
        }
      }
      tmp30 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 222
type: ALGORITHM

  assert(resistor.T_ref >= 0.0, "Variable violating min constraint: 0.0 <= resistor.T_ref, has value: " + String(resistor.T_ref, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_222(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,222};
  modelica_boolean tmp31;
  static const MMC_DEFSTRINGLIT(tmp32,69,"Variable violating min constraint: 0.0 <= resistor.T_ref, has value: ");
  modelica_string tmp33;
  modelica_metatype tmpMeta34;
  static int tmp35 = 0;
  if(!tmp35)
  {
    tmp31 = GreaterEq((data->simulationInfo->realParameter[41]/* resistor.T_ref PARAM */) ,0.0);
    if(!tmp31)
    {
      tmp33 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[41]/* resistor.T_ref PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta34 = stringAppend(MMC_REFSTRINGLIT(tmp32),tmp33);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nresistor.T_ref >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta34));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",5,3,5,64,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nresistor.T_ref >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta34));
        }
      }
      tmp35 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 223
type: ALGORITHM

  assert(resistor.T >= 0.0, "Variable violating min constraint: 0.0 <= resistor.T, has value: " + String(resistor.T, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_223(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,223};
  modelica_boolean tmp36;
  static const MMC_DEFSTRINGLIT(tmp37,65,"Variable violating min constraint: 0.0 <= resistor.T, has value: ");
  modelica_string tmp38;
  modelica_metatype tmpMeta39;
  static int tmp40 = 0;
  if(!tmp40)
  {
    tmp36 = GreaterEq((data->simulationInfo->realParameter[39]/* resistor.T PARAM */) ,0.0);
    if(!tmp36)
    {
      tmp38 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[39]/* resistor.T PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta39 = stringAppend(MMC_REFSTRINGLIT(tmp37),tmp38);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nresistor.T >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta39));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Interfaces/ConditionalHeatPort.mo",7,3,8,97,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nresistor.T >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta39));
        }
      }
      tmp40 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 224
type: ALGORITHM

  assert(resistor.T_heatPort >= 0.0, "Variable violating min constraint: 0.0 <= resistor.T_heatPort, has value: " + String(resistor.T_heatPort, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_224(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,224};
  modelica_boolean tmp41;
  static const MMC_DEFSTRINGLIT(tmp42,74,"Variable violating min constraint: 0.0 <= resistor.T_heatPort, has value: ");
  modelica_string tmp43;
  modelica_metatype tmpMeta44;
  static int tmp45 = 0;
  if(!tmp45)
  {
    tmp41 = GreaterEq((data->simulationInfo->realParameter[40]/* resistor.T_heatPort PARAM */) ,0.0);
    if(!tmp41)
    {
      tmp43 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[40]/* resistor.T_heatPort PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta44 = stringAppend(MMC_REFSTRINGLIT(tmp42),tmp43);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nresistor.T_heatPort >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta44));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Interfaces/ConditionalHeatPort.mo",14,3,14,54,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nresistor.T_heatPort >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta44));
        }
      }
      tmp45 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 225
type: ALGORITHM

  assert(resistor1.T_ref >= 0.0, "Variable violating min constraint: 0.0 <= resistor1.T_ref, has value: " + String(resistor1.T_ref, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_225(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,225};
  modelica_boolean tmp46;
  static const MMC_DEFSTRINGLIT(tmp47,70,"Variable violating min constraint: 0.0 <= resistor1.T_ref, has value: ");
  modelica_string tmp48;
  modelica_metatype tmpMeta49;
  static int tmp50 = 0;
  if(!tmp50)
  {
    tmp46 = GreaterEq((data->simulationInfo->realParameter[47]/* resistor1.T_ref PARAM */) ,0.0);
    if(!tmp46)
    {
      tmp48 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[47]/* resistor1.T_ref PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta49 = stringAppend(MMC_REFSTRINGLIT(tmp47),tmp48);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nresistor1.T_ref >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta49));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",5,3,5,64,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nresistor1.T_ref >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta49));
        }
      }
      tmp50 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 226
type: ALGORITHM

  assert(resistor1.T >= 0.0, "Variable violating min constraint: 0.0 <= resistor1.T, has value: " + String(resistor1.T, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_226(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,226};
  modelica_boolean tmp51;
  static const MMC_DEFSTRINGLIT(tmp52,66,"Variable violating min constraint: 0.0 <= resistor1.T, has value: ");
  modelica_string tmp53;
  modelica_metatype tmpMeta54;
  static int tmp55 = 0;
  if(!tmp55)
  {
    tmp51 = GreaterEq((data->simulationInfo->realParameter[45]/* resistor1.T PARAM */) ,0.0);
    if(!tmp51)
    {
      tmp53 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[45]/* resistor1.T PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta54 = stringAppend(MMC_REFSTRINGLIT(tmp52),tmp53);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nresistor1.T >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta54));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Interfaces/ConditionalHeatPort.mo",7,3,8,97,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nresistor1.T >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta54));
        }
      }
      tmp55 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 227
type: ALGORITHM

  assert(resistor1.T_heatPort >= 0.0, "Variable violating min constraint: 0.0 <= resistor1.T_heatPort, has value: " + String(resistor1.T_heatPort, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_227(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,227};
  modelica_boolean tmp56;
  static const MMC_DEFSTRINGLIT(tmp57,75,"Variable violating min constraint: 0.0 <= resistor1.T_heatPort, has value: ");
  modelica_string tmp58;
  modelica_metatype tmpMeta59;
  static int tmp60 = 0;
  if(!tmp60)
  {
    tmp56 = GreaterEq((data->simulationInfo->realParameter[46]/* resistor1.T_heatPort PARAM */) ,0.0);
    if(!tmp56)
    {
      tmp58 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[46]/* resistor1.T_heatPort PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta59 = stringAppend(MMC_REFSTRINGLIT(tmp57),tmp58);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nresistor1.T_heatPort >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta59));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Interfaces/ConditionalHeatPort.mo",14,3,14,54,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nresistor1.T_heatPort >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta59));
        }
      }
      tmp60 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 228
type: ALGORITHM

  assert(resistor2.T_ref >= 0.0, "Variable violating min constraint: 0.0 <= resistor2.T_ref, has value: " + String(resistor2.T_ref, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_228(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,228};
  modelica_boolean tmp61;
  static const MMC_DEFSTRINGLIT(tmp62,70,"Variable violating min constraint: 0.0 <= resistor2.T_ref, has value: ");
  modelica_string tmp63;
  modelica_metatype tmpMeta64;
  static int tmp65 = 0;
  if(!tmp65)
  {
    tmp61 = GreaterEq((data->simulationInfo->realParameter[53]/* resistor2.T_ref PARAM */) ,0.0);
    if(!tmp61)
    {
      tmp63 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[53]/* resistor2.T_ref PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta64 = stringAppend(MMC_REFSTRINGLIT(tmp62),tmp63);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nresistor2.T_ref >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta64));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",5,3,5,64,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nresistor2.T_ref >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta64));
        }
      }
      tmp65 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 229
type: ALGORITHM

  assert(resistor2.T >= 0.0, "Variable violating min constraint: 0.0 <= resistor2.T, has value: " + String(resistor2.T, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_229(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,229};
  modelica_boolean tmp66;
  static const MMC_DEFSTRINGLIT(tmp67,66,"Variable violating min constraint: 0.0 <= resistor2.T, has value: ");
  modelica_string tmp68;
  modelica_metatype tmpMeta69;
  static int tmp70 = 0;
  if(!tmp70)
  {
    tmp66 = GreaterEq((data->simulationInfo->realParameter[51]/* resistor2.T PARAM */) ,0.0);
    if(!tmp66)
    {
      tmp68 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[51]/* resistor2.T PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta69 = stringAppend(MMC_REFSTRINGLIT(tmp67),tmp68);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nresistor2.T >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta69));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Interfaces/ConditionalHeatPort.mo",7,3,8,97,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nresistor2.T >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta69));
        }
      }
      tmp70 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 230
type: ALGORITHM

  assert(resistor2.T_heatPort >= 0.0, "Variable violating min constraint: 0.0 <= resistor2.T_heatPort, has value: " + String(resistor2.T_heatPort, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_230(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,230};
  modelica_boolean tmp71;
  static const MMC_DEFSTRINGLIT(tmp72,75,"Variable violating min constraint: 0.0 <= resistor2.T_heatPort, has value: ");
  modelica_string tmp73;
  modelica_metatype tmpMeta74;
  static int tmp75 = 0;
  if(!tmp75)
  {
    tmp71 = GreaterEq((data->simulationInfo->realParameter[52]/* resistor2.T_heatPort PARAM */) ,0.0);
    if(!tmp71)
    {
      tmp73 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[52]/* resistor2.T_heatPort PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta74 = stringAppend(MMC_REFSTRINGLIT(tmp72),tmp73);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nresistor2.T_heatPort >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta74));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Interfaces/ConditionalHeatPort.mo",14,3,14,54,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nresistor2.T_heatPort >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta74));
        }
      }
      tmp75 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 231
type: ALGORITHM

  assert(resistor3.T_ref >= 0.0, "Variable violating min constraint: 0.0 <= resistor3.T_ref, has value: " + String(resistor3.T_ref, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_231(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,231};
  modelica_boolean tmp76;
  static const MMC_DEFSTRINGLIT(tmp77,70,"Variable violating min constraint: 0.0 <= resistor3.T_ref, has value: ");
  modelica_string tmp78;
  modelica_metatype tmpMeta79;
  static int tmp80 = 0;
  if(!tmp80)
  {
    tmp76 = GreaterEq((data->simulationInfo->realParameter[59]/* resistor3.T_ref PARAM */) ,0.0);
    if(!tmp76)
    {
      tmp78 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[59]/* resistor3.T_ref PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta79 = stringAppend(MMC_REFSTRINGLIT(tmp77),tmp78);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nresistor3.T_ref >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta79));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Resistor.mo",5,3,5,64,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nresistor3.T_ref >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta79));
        }
      }
      tmp80 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 232
type: ALGORITHM

  assert(resistor3.T >= 0.0, "Variable violating min constraint: 0.0 <= resistor3.T, has value: " + String(resistor3.T, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_232(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,232};
  modelica_boolean tmp81;
  static const MMC_DEFSTRINGLIT(tmp82,66,"Variable violating min constraint: 0.0 <= resistor3.T, has value: ");
  modelica_string tmp83;
  modelica_metatype tmpMeta84;
  static int tmp85 = 0;
  if(!tmp85)
  {
    tmp81 = GreaterEq((data->simulationInfo->realParameter[57]/* resistor3.T PARAM */) ,0.0);
    if(!tmp81)
    {
      tmp83 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[57]/* resistor3.T PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta84 = stringAppend(MMC_REFSTRINGLIT(tmp82),tmp83);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nresistor3.T >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta84));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Interfaces/ConditionalHeatPort.mo",7,3,8,97,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nresistor3.T >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta84));
        }
      }
      tmp85 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 233
type: ALGORITHM

  assert(resistor3.T_heatPort >= 0.0, "Variable violating min constraint: 0.0 <= resistor3.T_heatPort, has value: " + String(resistor3.T_heatPort, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_233(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,233};
  modelica_boolean tmp86;
  static const MMC_DEFSTRINGLIT(tmp87,75,"Variable violating min constraint: 0.0 <= resistor3.T_heatPort, has value: ");
  modelica_string tmp88;
  modelica_metatype tmpMeta89;
  static int tmp90 = 0;
  if(!tmp90)
  {
    tmp86 = GreaterEq((data->simulationInfo->realParameter[58]/* resistor3.T_heatPort PARAM */) ,0.0);
    if(!tmp86)
    {
      tmp88 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[58]/* resistor3.T_heatPort PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta89 = stringAppend(MMC_REFSTRINGLIT(tmp87),tmp88);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\nresistor3.T_heatPort >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta89));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Interfaces/ConditionalHeatPort.mo",14,3,14,54,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\nresistor3.T_heatPort >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta89));
        }
      }
      tmp90 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 234
type: ALGORITHM

  assert(combiTimeTable.timeEvents >= Modelica.Blocks.Types.TimeEvents.Always and combiTimeTable.timeEvents <= Modelica.Blocks.Types.TimeEvents.NoTimeEvents, "Variable violating min/max constraint: Modelica.Blocks.Types.TimeEvents.Always <= combiTimeTable.timeEvents <= Modelica.Blocks.Types.TimeEvents.NoTimeEvents, has value: " + String(combiTimeTable.timeEvents, "d"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_234(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,234};
  modelica_boolean tmp91;
  modelica_boolean tmp92;
  static const MMC_DEFSTRINGLIT(tmp93,169,"Variable violating min/max constraint: Modelica.Blocks.Types.TimeEvents.Always <= combiTimeTable.timeEvents <= Modelica.Blocks.Types.TimeEvents.NoTimeEvents, has value: ");
  modelica_string tmp94;
  modelica_metatype tmpMeta95;
  static int tmp96 = 0;
  if(!tmp96)
  {
    tmp91 = GreaterEq((data->simulationInfo->integerParameter[4]/* combiTimeTable.timeEvents PARAM */) ,1);
    tmp92 = LessEq((data->simulationInfo->integerParameter[4]/* combiTimeTable.timeEvents PARAM */) ,3);
    if(!(tmp91 && tmp92))
    {
      tmp94 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[4]/* combiTimeTable.timeEvents PARAM */) , (modelica_string) mmc_strings_len1[100]);
      tmpMeta95 = stringAppend(MMC_REFSTRINGLIT(tmp93),tmp94);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\ncombiTimeTable.timeEvents >= Modelica.Blocks.Types.TimeEvents.Always and combiTimeTable.timeEvents <= Modelica.Blocks.Types.TimeEvents.NoTimeEvents", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta95));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Blocks/Sources.mo",1600,5,1602,131,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\ncombiTimeTable.timeEvents >= Modelica.Blocks.Types.TimeEvents.Always and combiTimeTable.timeEvents <= Modelica.Blocks.Types.TimeEvents.NoTimeEvents", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta95));
        }
      }
      tmp96 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 235
type: ALGORITHM

  assert(combiTimeTable.timeScale >= 1e-15, "Variable violating min constraint: 1e-15 <= combiTimeTable.timeScale, has value: " + String(combiTimeTable.timeScale, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_235(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,235};
  modelica_boolean tmp97;
  static const MMC_DEFSTRINGLIT(tmp98,81,"Variable violating min constraint: 1e-15 <= combiTimeTable.timeScale, has value: ");
  modelica_string tmp99;
  modelica_metatype tmpMeta100;
  static int tmp101 = 0;
  if(!tmp101)
  {
    tmp97 = GreaterEq((data->simulationInfo->realParameter[28]/* combiTimeTable.timeScale PARAM */) ,1e-15);
    if(!tmp97)
    {
      tmp99 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[28]/* combiTimeTable.timeScale PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta100 = stringAppend(MMC_REFSTRINGLIT(tmp98),tmp99);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\ncombiTimeTable.timeScale >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta100));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Blocks/Sources.mo",1589,5,1591,76,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\ncombiTimeTable.timeScale >= 1e-15", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta100));
        }
      }
      tmp101 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 236
type: ALGORITHM

  assert(combiTimeTable.extrapolation >= Modelica.Blocks.Types.Extrapolation.HoldLastPoint and combiTimeTable.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation, "Variable violating min/max constraint: Modelica.Blocks.Types.Extrapolation.HoldLastPoint <= combiTimeTable.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation, has value: " + String(combiTimeTable.extrapolation, "d"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_236(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,236};
  modelica_boolean tmp102;
  modelica_boolean tmp103;
  static const MMC_DEFSTRINGLIT(tmp104,188,"Variable violating min/max constraint: Modelica.Blocks.Types.Extrapolation.HoldLastPoint <= combiTimeTable.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation, has value: ");
  modelica_string tmp105;
  modelica_metatype tmpMeta106;
  static int tmp107 = 0;
  if(!tmp107)
  {
    tmp102 = GreaterEq((data->simulationInfo->integerParameter[1]/* combiTimeTable.extrapolation PARAM */) ,1);
    tmp103 = LessEq((data->simulationInfo->integerParameter[1]/* combiTimeTable.extrapolation PARAM */) ,4);
    if(!(tmp102 && tmp103))
    {
      tmp105 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[1]/* combiTimeTable.extrapolation PARAM */) , (modelica_string) mmc_strings_len1[100]);
      tmpMeta106 = stringAppend(MMC_REFSTRINGLIT(tmp104),tmp105);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\ncombiTimeTable.extrapolation >= Modelica.Blocks.Types.Extrapolation.HoldLastPoint and combiTimeTable.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta106));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Blocks/Sources.mo",1586,5,1588,61,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\ncombiTimeTable.extrapolation >= Modelica.Blocks.Types.Extrapolation.HoldLastPoint and combiTimeTable.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta106));
        }
      }
      tmp107 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 237
type: ALGORITHM

  assert(combiTimeTable.smoothness >= Modelica.Blocks.Types.Smoothness.LinearSegments and combiTimeTable.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative, "Variable violating min/max constraint: Modelica.Blocks.Types.Smoothness.LinearSegments <= combiTimeTable.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative, has value: " + String(combiTimeTable.smoothness, "d"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_237(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,237};
  modelica_boolean tmp108;
  modelica_boolean tmp109;
  static const MMC_DEFSTRINGLIT(tmp110,193,"Variable violating min/max constraint: Modelica.Blocks.Types.Smoothness.LinearSegments <= combiTimeTable.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative, has value: ");
  modelica_string tmp111;
  modelica_metatype tmpMeta112;
  static int tmp113 = 0;
  if(!tmp113)
  {
    tmp108 = GreaterEq((data->simulationInfo->integerParameter[3]/* combiTimeTable.smoothness PARAM */) ,1);
    tmp109 = LessEq((data->simulationInfo->integerParameter[3]/* combiTimeTable.smoothness PARAM */) ,6);
    if(!(tmp108 && tmp109))
    {
      tmp111 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[3]/* combiTimeTable.smoothness PARAM */) , (modelica_string) mmc_strings_len1[100]);
      tmpMeta112 = stringAppend(MMC_REFSTRINGLIT(tmp110),tmp111);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\ncombiTimeTable.smoothness >= Modelica.Blocks.Types.Smoothness.LinearSegments and combiTimeTable.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta112));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Blocks/Sources.mo",1583,5,1585,61,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\ncombiTimeTable.smoothness >= Modelica.Blocks.Types.Smoothness.LinearSegments and combiTimeTable.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta112));
        }
      }
      tmp113 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 238
type: ALGORITHM

  assert(combiTimeTable.nout >= 1, "Variable violating min constraint: 1 <= combiTimeTable.nout, has value: " + String(combiTimeTable.nout, "d"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_238(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,238};
  modelica_boolean tmp114;
  static const MMC_DEFSTRINGLIT(tmp115,72,"Variable violating min constraint: 1 <= combiTimeTable.nout, has value: ");
  modelica_string tmp116;
  modelica_metatype tmpMeta117;
  static int tmp118 = 0;
  if(!tmp118)
  {
    tmp114 = GreaterEq((data->simulationInfo->integerParameter[2]/* combiTimeTable.nout PARAM */) ,((modelica_integer) 1));
    if(!tmp114)
    {
      tmp116 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[2]/* combiTimeTable.nout PARAM */) , (modelica_string) mmc_strings_len1[100]);
      tmpMeta117 = stringAppend(MMC_REFSTRINGLIT(tmp115),tmp116);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\ncombiTimeTable.nout >= 1", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta117));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Blocks/Interfaces.mo",313,5,313,58,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\ncombiTimeTable.nout >= 1", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta117));
        }
      }
      tmp118 = 1;
    }
  }
  TRACE_POP
}

/*
equation index: 239
type: ALGORITHM

  assert(capacitor.C >= 0.0, "Variable violating min constraint: 0.0 <= capacitor.C, has value: " + String(capacitor.C, "g"));
*/
OMC_DISABLE_OPT
static void oc_latch_eqFunction_239(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  const int equationIndexes[2] = {1,239};
  modelica_boolean tmp119;
  static const MMC_DEFSTRINGLIT(tmp120,66,"Variable violating min constraint: 0.0 <= capacitor.C, has value: ");
  modelica_string tmp121;
  modelica_metatype tmpMeta122;
  static int tmp123 = 0;
  if(!tmp123)
  {
    tmp119 = GreaterEq((data->simulationInfo->realParameter[11]/* capacitor.C PARAM */) ,0.0);
    if(!tmp119)
    {
      tmp121 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[11]/* capacitor.C PARAM */) , (modelica_string) mmc_strings_len1[103]);
      tmpMeta122 = stringAppend(MMC_REFSTRINGLIT(tmp120),tmp121);
      {
        if (data->simulationInfo->noThrowAsserts) {
          infoStreamPrintWithEquationIndexes(LOG_ASSERT, 0, equationIndexes, "The following assertion has been violated %sat time %f\ncapacitor.C >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          infoStreamPrint(LOG_ASSERT, 0, "%s", MMC_STRINGDATA(tmpMeta122));
        } else {
          FILE_INFO info = {"C:/OpenModelica/lib/omlibrary/Modelica 4.0.0/Electrical/Analog/Basic/Capacitor.mo",4,3,4,52,0};
          omc_assert_warning(info, "The following assertion has been violated %sat time %f\ncapacitor.C >= 0.0", initial() ? "during initialization " : "", data->localData[0]->timeValue);
          omc_assert_warning_withEquationIndexes(info, equationIndexes, MMC_STRINGDATA(tmpMeta122));
        }
      }
      tmp123 = 1;
    }
  }
  TRACE_POP
}
OMC_DISABLE_OPT
void oc_latch_updateBoundParameters_0(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  oc_latch_eqFunction_140(data, threadData);
  oc_latch_eqFunction_141(data, threadData);
  oc_latch_eqFunction_142(data, threadData);
  oc_latch_eqFunction_143(data, threadData);
  oc_latch_eqFunction_144(data, threadData);
  oc_latch_eqFunction_145(data, threadData);
  oc_latch_eqFunction_146(data, threadData);
  oc_latch_eqFunction_147(data, threadData);
  oc_latch_eqFunction_148(data, threadData);
  oc_latch_eqFunction_149(data, threadData);
  oc_latch_eqFunction_150(data, threadData);
  oc_latch_eqFunction_151(data, threadData);
  oc_latch_eqFunction_152(data, threadData);
  oc_latch_eqFunction_153(data, threadData);
  oc_latch_eqFunction_154(data, threadData);
  oc_latch_eqFunction_155(data, threadData);
  oc_latch_eqFunction_156(data, threadData);
  oc_latch_eqFunction_157(data, threadData);
  oc_latch_eqFunction_158(data, threadData);
  oc_latch_eqFunction_159(data, threadData);
  oc_latch_eqFunction_160(data, threadData);
  oc_latch_eqFunction_161(data, threadData);
  oc_latch_eqFunction_162(data, threadData);
  oc_latch_eqFunction_163(data, threadData);
  oc_latch_eqFunction_171(data, threadData);
  oc_latch_eqFunction_172(data, threadData);
  oc_latch_eqFunction_173(data, threadData);
  oc_latch_eqFunction_174(data, threadData);
  oc_latch_eqFunction_76(data, threadData);
  oc_latch_eqFunction_75(data, threadData);
  oc_latch_eqFunction_74(data, threadData);
  oc_latch_eqFunction_16(data, threadData);
  oc_latch_eqFunction_73(data, threadData);
  oc_latch_eqFunction_72(data, threadData);
  oc_latch_eqFunction_71(data, threadData);
  oc_latch_eqFunction_70(data, threadData);
  oc_latch_eqFunction_69(data, threadData);
  oc_latch_eqFunction_68(data, threadData);
  oc_latch_eqFunction_67(data, threadData);
  oc_latch_eqFunction_15(data, threadData);
  oc_latch_eqFunction_66(data, threadData);
  oc_latch_eqFunction_65(data, threadData);
  oc_latch_eqFunction_64(data, threadData);
  oc_latch_eqFunction_14(data, threadData);
  oc_latch_eqFunction_13(data, threadData);
  oc_latch_eqFunction_12(data, threadData);
  oc_latch_eqFunction_11(data, threadData);
  oc_latch_eqFunction_10(data, threadData);
  oc_latch_eqFunction_9(data, threadData);
  oc_latch_eqFunction_8(data, threadData);
  oc_latch_eqFunction_7(data, threadData);
  oc_latch_eqFunction_6(data, threadData);
  oc_latch_eqFunction_5(data, threadData);
  oc_latch_eqFunction_4(data, threadData);
  oc_latch_eqFunction_3(data, threadData);
  oc_latch_eqFunction_2(data, threadData);
  oc_latch_eqFunction_1(data, threadData);
  oc_latch_eqFunction_216(data, threadData);
  oc_latch_eqFunction_217(data, threadData);
  oc_latch_eqFunction_218(data, threadData);
  oc_latch_eqFunction_219(data, threadData);
  oc_latch_eqFunction_220(data, threadData);
  oc_latch_eqFunction_221(data, threadData);
  oc_latch_eqFunction_222(data, threadData);
  oc_latch_eqFunction_223(data, threadData);
  oc_latch_eqFunction_224(data, threadData);
  oc_latch_eqFunction_225(data, threadData);
  oc_latch_eqFunction_226(data, threadData);
  oc_latch_eqFunction_227(data, threadData);
  oc_latch_eqFunction_228(data, threadData);
  oc_latch_eqFunction_229(data, threadData);
  oc_latch_eqFunction_230(data, threadData);
  oc_latch_eqFunction_231(data, threadData);
  oc_latch_eqFunction_232(data, threadData);
  oc_latch_eqFunction_233(data, threadData);
  oc_latch_eqFunction_234(data, threadData);
  oc_latch_eqFunction_235(data, threadData);
  oc_latch_eqFunction_236(data, threadData);
  oc_latch_eqFunction_237(data, threadData);
  oc_latch_eqFunction_238(data, threadData);
  oc_latch_eqFunction_239(data, threadData);
  TRACE_POP
}
OMC_DISABLE_OPT
int oc_latch_updateBoundParameters(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  (data->simulationInfo->integerParameter[0]/* combiTimeTable.columns[1] PARAM */)  = ((modelica_integer) 2);
  data->modelData->integerParameterData[0].time_unvarying = 1;
  (data->simulationInfo->integerParameter[2]/* combiTimeTable.nout PARAM */)  = ((modelica_integer) 1);
  data->modelData->integerParameterData[2].time_unvarying = 1;
  (data->localData[0]->realVars[8]/* capacitor.n.i variable */)  = -0.0;
  data->modelData->realVarsData[8].time_unvarying = 1;
  (data->localData[0]->realVars[15]/* ground3.p.i variable */)  = -0.0;
  data->modelData->realVarsData[15].time_unvarying = 1;
  (data->localData[0]->realVars[18]/* ground5.p.i variable */)  = -0.0;
  data->modelData->realVarsData[18].time_unvarying = 1;
  (data->localData[0]->realVars[55]/* signalVoltage.n.i variable */)  = -0.0;
  data->modelData->realVarsData[55].time_unvarying = 1;
  (data->simulationInfo->realParameter[14]/* combiTimeTable.offset[1] PARAM */)  = 0.0;
  data->modelData->realParameterData[14].time_unvarying = 1;
  (data->simulationInfo->realParameter[15]/* combiTimeTable.p_offset[1] PARAM */)  = 0.0;
  data->modelData->realParameterData[15].time_unvarying = 1;
  (data->simulationInfo->realParameter[28]/* combiTimeTable.timeScale PARAM */)  = 1.0;
  data->modelData->realParameterData[28].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[0]/* R1.useHeatPort PARAM */)  = 0;
  data->modelData->booleanParameterData[0].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[1]/* R2.useHeatPort PARAM */)  = 0;
  data->modelData->booleanParameterData[1].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[2]/* combiTimeTable.tableOnFile PARAM */)  = 0;
  data->modelData->booleanParameterData[2].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[3]/* combiTimeTable.verboseExtrapolation PARAM */)  = 0;
  data->modelData->booleanParameterData[3].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[7]/* resistor.useHeatPort PARAM */)  = 0;
  data->modelData->booleanParameterData[7].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[8]/* resistor1.useHeatPort PARAM */)  = 0;
  data->modelData->booleanParameterData[8].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[9]/* resistor2.useHeatPort PARAM */)  = 0;
  data->modelData->booleanParameterData[9].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[10]/* resistor3.useHeatPort PARAM */)  = 0;
  data->modelData->booleanParameterData[10].time_unvarying = 1;
  (data->simulationInfo->integerParameter[1]/* combiTimeTable.extrapolation PARAM */)  = 1;
  data->modelData->integerParameterData[1].time_unvarying = 1;
  (data->simulationInfo->integerParameter[3]/* combiTimeTable.smoothness PARAM */)  = 3;
  data->modelData->integerParameterData[3].time_unvarying = 1;
  oc_latch_updateBoundParameters_0(data, threadData);
  TRACE_POP
  return 0;
}

#if defined(__cplusplus)
}
#endif

