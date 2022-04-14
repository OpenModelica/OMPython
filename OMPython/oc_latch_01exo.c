/* External objects file */
#include "oc_latch_model.h"
#if defined(__cplusplus)
extern "C" {
#endif

void oc_latch_callExternalObjectDestructors(DATA *data, threadData_t *threadData)
{
  if(data->simulationInfo->extObjs)
  {
    omc_Modelica_Blocks_Types_ExternalCombiTimeTable_destructor(threadData,(data->simulationInfo->extObjs[0]));
    free(data->simulationInfo->extObjs);
    data->simulationInfo->extObjs = 0;
  }
}
#if defined(__cplusplus)
}
#endif

