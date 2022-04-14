/* Synchronous systems */
#include "oc_latch_model.h"
#if defined(__cplusplus)
extern "C" {
#endif

/* Initializes the clocks of model. */
void oc_latch_function_initSynchronous(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH
  data->simulationInfo->baseClocks = calloc(0, sizeof(BASECLOCK_DATA));
  
  TRACE_POP
}

/* Update base-clock. */
void oc_latch_function_updateSynchronous(DATA *data, threadData_t *threadData, long base_idx)
{
  TRACE_PUSH
  modelica_boolean ret;
  switch (base_idx) {
    default:
      throwStreamPrint(NULL, "Internal Error: unknown base partition %ld", base_idx);
      break;
  }
  TRACE_POP
}



/* Clocked systems equations */
int oc_latch_function_equationsSynchronous(DATA *data, threadData_t *threadData, long base_idx, long sub_idx)
{
  TRACE_PUSH
  int ret;

  switch (base_idx) {
    default:
      throwStreamPrint(NULL, "Internal Error: unknown base-clock partition %ld", base_idx);
      ret = 1;
      break;
  }

  TRACE_POP
  return ret;
}

/* %v% = pre(%v%)*/
void oc_latch_function_savePreSynchronous(DATA *data, threadData_t *threadData)
{
  TRACE_PUSH

  
  TRACE_POP
}

#if defined(__cplusplus)
}
#endif

