/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2023 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f4xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

void HAL_TIM_MspPostInit(TIM_HandleTypeDef *htim);

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define LED1_Pin GPIO_PIN_10
#define LED1_GPIO_Port GPIOE
#define PWM_SERVO_1_Pin GPIO_PIN_11
#define PWM_SERVO_1_GPIO_Port GPIOA
#define PWM_SERVO_2_Pin GPIO_PIN_12
#define PWM_SERVO_2_GPIO_Port GPIOA

/* USER CODE BEGIN Private defines */

/* ===== 电机 PWM 引脚 (TIM1 CH1~CH4 → PE9/PE11/PE13/PE14) ===== */
#define MOTOR1_PWM_POS_Pin      GPIO_PIN_9    /* TIM1_CH1  电机1正转 */
#define MOTOR1_PWM_POS_Port     GPIOE
#define MOTOR1_PWM_NEG_Pin      GPIO_PIN_11   /* TIM1_CH2  电机1反转 */
#define MOTOR1_PWM_NEG_Port     GPIOE
#define MOTOR2_PWM_POS_Pin      GPIO_PIN_13   /* TIM1_CH3  电机2正转 */
#define MOTOR2_PWM_POS_Port     GPIOE
#define MOTOR2_PWM_NEG_Pin      GPIO_PIN_14   /* TIM1_CH4  电机2反转 */
#define MOTOR2_PWM_NEG_Port     GPIOE

/* ===== 舵机软件PWM参数 ===== */
#define SERVO_PULSE_MIN         50    /* 0.5ms  → 0°   (50 * 10μs) */
#define SERVO_PULSE_MAX         250   /* 2.5ms  → 180° (250 * 10μs) */
#define SERVO_PERIOD            2000  /* 20ms周期 (2000 * 10μs = 200Hz中断, 每2次为一个舵机周期) */

/* ===== 电机PWM参数 ===== */
#define MOTOR_PWM_MAX           999   /* TIM1 ARR=999, 占空比0~999 */

/* ===== 函数声明 ===== */
void Servo_SetAngle(uint8_t servo_id, float angle);
void Motor_SetSpeed(uint8_t motor_id, int16_t speed);
int32_t Encoder_GetCount(uint8_t encoder_id);

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
