
#include "LED_Task.h"

void LED_Task_entry(void *argument)
{
  for(;;)
  {
	  HAL_GPIO_WritePin(LED1_GPIO_Port, LED1_Pin, GPIO_PIN_SET);
	  osDelay(500);
	  HAL_GPIO_WritePin(LED1_GPIO_Port, LED1_Pin, GPIO_PIN_RESET);
	  osDelay(500);
  }
}



