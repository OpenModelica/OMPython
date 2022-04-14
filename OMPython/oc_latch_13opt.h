#if defined(__cplusplus)
  extern "C" {
#endif
  int oc_latch_mayer(DATA* data, modelica_real** res, short*);
  int oc_latch_lagrange(DATA* data, modelica_real** res, short *, short *);
  int oc_latch_pickUpBoundsForInputsInOptimization(DATA* data, modelica_real* min, modelica_real* max, modelica_real*nominal, modelica_boolean *useNominal, char ** name, modelica_real * start, modelica_real * startTimeOpt);
  int oc_latch_setInputData(DATA *data, const modelica_boolean file);
  int oc_latch_getTimeGrid(DATA *data, modelica_integer * nsi, modelica_real**t);
#if defined(__cplusplus)
}
#endif