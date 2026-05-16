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
/* 丝印M1(电机1): CH3正转/CH4反转 → PE13/PE14, 编码器TIM5(PA0/PA1)  */
/* 丝印M2(电机2): CH1正转/CH2反转 → PE9/PE11,  编码器TIM2(PA15/PB3) */
#define MOTOR1_PWM_POS_Pin      GPIO_PIN_13   /* TIM1_CH3  丝印M1正转 */
#define MOTOR1_PWM_POS_Port     GPIOE
#define MOTOR1_PWM_NEG_Pin      GPIO_PIN_14   /* TIM1_CH4  丝印M1反转 */
#define MOTOR1_PWM_NEG_Port     GPIOE
#define MOTOR2_PWM_POS_Pin      GPIO_PIN_9    /* TIM1_CH1  丝印M2正转 */
#define MOTOR2_PWM_POS_Port     GPIOE
#define MOTOR2_PWM_NEG_Pin      GPIO_PIN_11   /* TIM1_CH2  丝印M2反转 */
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

/* ===== 串口指令速查 ===== */
/* ── 舵机 ── */
/* S1=<deg>      设置舵机1角度 0~180                                   */
/* S2=<deg>      设置舵机2角度 0~180                                   */
/* ── 开环PWM ── */
/* M1=<pwm>      开环控制电机1, pwm范围-999~999 (自动关闭PID)          */
/* M2=<pwm>      开环控制电机2                                        */
/* ── PID闭环速度 ── */
/* V1=<speed>    PID闭环电机1, speed=脉冲/10ms (正/负代表方向)         */
/* V2=<speed>    PID闭环电机2                                        */
/* ── 全局PID参数(同时设置两电机) ── */
/* KP/KI/KD=<v>  同时设置两电机Kp/Ki/Kd                               */
/* ── 电机1独立PID参数 ── */
/* KP1/KI1/KD1   电机1的Kp/Ki/Kd                                      */
/* IMAX1/OMAX1   积分限幅/输出限幅 (默认300/999)                       */
/* DB1           死区, |error|<DB1时忽略 (默认0, 防振荡)              */
/* RAMP1         输出变化率限制(每10ms), 0=不限 (默认0, 防突变)       */
/* ── 电机2独立PID参数 ── */
/* KP2/KI2/KD2   电机2的Kp/Ki/Kd                                      */
/* IMAX2/OMAX2   积分限幅/输出限幅 (默认300/999)                       */
/* DB2           死区                                                 */
/* RAMP2         输出变化率限制                                        */
/* ── 调试命令 ── */
/* RP1/RP2       读回电机1/2全部PID参数                                */
/* RST1/RST2     复位电机1/2积分累加器                                 */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
