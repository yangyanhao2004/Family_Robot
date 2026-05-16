/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
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
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "cmsis_os.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdarg.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
typedef StaticTask_t osStaticThreadDef_t;
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
TIM_HandleTypeDef htim1;
TIM_HandleTypeDef htim2;
TIM_HandleTypeDef htim5;
TIM_HandleTypeDef htim7;
TIM_HandleTypeDef htim13;

UART_HandleTypeDef huart1;

/* Definitions for defaultTask */
osThreadId_t defaultTaskHandle;
const osThreadAttr_t defaultTask_attributes = {
  .name = "defaultTask",
  .stack_size = 512 * 4,
  .priority = (osPriority_t) osPriorityNormal,
};
/* Definitions for LED_Task */
osThreadId_t LED_TaskHandle;
uint32_t LED_TaskBuffer[ 128 ];
osStaticThreadDef_t LED_TaskControlBlock;
const osThreadAttr_t LED_Task_attributes = {
  .name = "LED_Task",
  .cb_mem = &LED_TaskControlBlock,
  .cb_size = sizeof(LED_TaskControlBlock),
  .stack_mem = &LED_TaskBuffer[0],
  .stack_size = sizeof(LED_TaskBuffer),
  .priority = (osPriority_t) osPriorityLow,
};
/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_TIM1_Init(void);
static void MX_TIM2_Init(void);
static void MX_TIM5_Init(void);
static void MX_TIM7_Init(void);
static void MX_TIM13_Init(void);
static void MX_USART1_UART_Init(void);
void StartDefaultTask(void *argument);
void LED_Task_entry(void *argument);

/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* ===== 舵机软件PWM全局变量 ===== */
static volatile uint16_t servo_pulse[2] = {150, 150};  /* 舵机1/2 高电平脉宽(单位10μs), 默认90° */
static volatile uint16_t servo_tick = 0;               /* TIM13中断计数器 */

/* ===== 编码器速度变量 ===== */
static volatile int32_t encoder1_speed = 0;  /* 丝印M1速度(TIM5 PA0/PA1) */
static volatile int32_t encoder2_speed = 0;  /* 丝印M2速度(TIM2 PA15/PB3) */
static volatile int32_t encoder1_last = 0;   /* 上次计数值 */
static volatile int32_t encoder2_last = 0;

/* ===== 增量式PID结构体 ===== */
typedef struct {
  float  kp;           /* 比例系数 */
  float  ki;           /* 积分系数 */
  float  kd;           /* 微分系数 */
  float  target;       /* 目标速度(脉冲/10ms) */
  float  err;          /* 当前误差 */
  float  err_last;     /* 上次误差 */
  float  err_sum;      /* 误差积分 */
  float  out;          /* PID输出(PWM值) */
  float  out_max;      /* 输出上限 */
  float  i_limit;      /* 积分限幅 */
  float  deadband;     /* 死区: |error|小于此值时忽略, 防振荡 */
  float  ramp;         /* 输出变化率限制(每周期最大增量, 0=不限) */
  uint8_t enabled;     /* 1=PID使能, 0=开环模式 */
} PID_t;

static void uart_printf(const char *fmt, ...);

static void PID_Reset(PID_t *pid)
{
  pid->err_sum  = 0.0f;
  pid->err_last = 0.0f;
  pid->err      = 0.0f;
}

static void PID_Report(uint8_t id, PID_t *pid)
{
  uart_printf("PID%d: kp=%.3f ki=%.3f kd=%.3f target=%.1f out=%.1f "
              "omax=%.0f ilim=%.0f db=%.1f ramp=%.1f en=%d\r\n",
              id, (double)pid->kp, (double)pid->ki, (double)pid->kd,
              (double)pid->target, (double)pid->out,
              (double)pid->out_max, (double)pid->i_limit,
              (double)pid->deadband, (double)pid->ramp, pid->enabled);
}

/* 两个电机的PID实例 */
static PID_t pid1 = {
  .kp = 8.0f, .ki = 1.5f, .kd = 1.0f,
  .out_max = 999.0f, .i_limit = 300.0f,
  .deadband = 0.0f, .ramp = 0.0f,
  .enabled = 0
};
static PID_t pid2 = {
  .kp = 8.0f, .ki = 1.5f, .kd = 1.0f,
  .out_max = 999.0f, .i_limit = 300.0f,
  .deadband = 0.0f, .ramp = 0.0f,
  .enabled = 0
};

/* ===== 增量式PID计算 ===== */
/* 每10ms在TIM7中断里调用一次, actual为编码器测速值 */
static float PID_Calc(PID_t *pid, float actual)
{
  if (!pid->enabled) return pid->out;

  pid->err = pid->target - actual;

  /* 死区: 忽略小误差, 防止负载下震荡 */
  if (pid->deadband > 0.0f)
  {
    if (pid->err > -pid->deadband && pid->err < pid->deadband)
      pid->err = 0.0f;
  }

  /* 积分抗饱和: 仅在误差较显著时累加; 积分限幅 */
  if (pid->err > 0.001f || pid->err < -0.001f)
    pid->err_sum += pid->err;
  if (pid->err_sum >  pid->i_limit) pid->err_sum =  pid->i_limit;
  if (pid->err_sum < -pid->i_limit) pid->err_sum = -pid->i_limit;

  /* PID输出 */
  float output = pid->kp * pid->err
               + pid->ki * pid->err_sum
               + pid->kd * (pid->err - pid->err_last);

  /* 输出变化率限制(防突变, 保护驱动和机械) */
  if (pid->ramp > 0.0f)
  {
    float delta = output - pid->out;
    if (delta >  pid->ramp) output = pid->out + pid->ramp;
    if (delta < -pid->ramp) output = pid->out - pid->ramp;
  }

  /* 输出限幅 */
  if (output >  pid->out_max) output =  pid->out_max;
  if (output < -pid->out_max) output = -pid->out_max;

  pid->err_last = pid->err;
  pid->out = output;
  return output;
}

/* ===== 设置PID目标速度(带符号, 正/负代表方向) ===== */
static void PID_SetTarget(PID_t *pid, float target)
{
  pid->target  = target;
  pid->err     = 0.0f;
  pid->err_last = 0.0f;
  pid->err_sum  = 0.0f;
  pid->out      = 0.0f;
  pid->enabled  = (target != 0.0f) ? 1 : 0;
}

/* ===== 串口接收缓冲 ===== */
static uint8_t uart_rx_byte = 0;

/* ===== 轻量串口格式化输出（替代 printf，避免栈溢出） ===== */
static void uart_printf(const char *fmt, ...)
{
  char buf[80];
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(buf, sizeof(buf), fmt, ap);
  va_end(ap);
  HAL_UART_Transmit(&huart1, (uint8_t *)buf, strlen(buf), HAL_MAX_DELAY);
}

/* ===== 舵机控制 ===== */
void Servo_SetAngle(uint8_t servo_id, float angle)
{
  if (servo_id > 1) return;
  if (angle < 0) angle = 0;
  if (angle > 180) angle = 180;
  /* 角度 → 脉宽: 0°=50, 180°=250, 线性映射 */
  servo_pulse[servo_id] = (uint16_t)(SERVO_PULSE_MIN + (angle / 180.0f) * (SERVO_PULSE_MAX - SERVO_PULSE_MIN));
}

/* ===== 电机控制 ===== */
void Motor_SetSpeed(uint8_t motor_id, int16_t speed)
{
  if (speed > MOTOR_PWM_MAX) speed = MOTOR_PWM_MAX;
  if (speed < -MOTOR_PWM_MAX) speed = -MOTOR_PWM_MAX;

  if (motor_id == 0)  /* 电机1(丝印M1): CH3正转, CH4反转, PE13/PE14 */
  {
    if (speed >= 0)
    {
      __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_3, (uint32_t)speed);
      __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_4, 0);
    }
    else
    {
      __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_3, 0);
      __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_4, (uint32_t)(-speed));
    }
  }
  else if (motor_id == 1)  /* 电机2(丝印M2): CH2正转, CH1反转, PE11/PE9 (右轮方向已校准) */
  {
    if (speed >= 0)
    {
      __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, (uint32_t)speed);
      __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, 0);
    }
    else
    {
      __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, 0);
      __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, (uint32_t)(-speed));
    }
  }
}

/* ===== 编码器读取 ===== */
int32_t Encoder_GetCount(uint8_t encoder_id)
{
  if (encoder_id == 0)  /* 丝印M1 → TIM5(PA0/PA1) */
    return (int32_t)__HAL_TIM_GET_COUNTER(&htim5);
  else if (encoder_id == 1)  /* 丝印M2 → TIM2(PA15/PB3) */
    return (int32_t)__HAL_TIM_GET_COUNTER(&htim2);
  return 0;
}

/* ===== TIM13 软件PWM中断回调 (10μs周期, Update溢出中断) ===== */
void HAL_TIM_PeriodElapsedCallback_TIM13(TIM_HandleTypeDef *htim)
{
  if (htim->Instance != TIM13) return;

  servo_tick++;

  if (servo_tick == 1)
  {
    /* 周期开始: 拉高两个舵机 */
    HAL_GPIO_WritePin(PWM_SERVO_1_GPIO_Port, PWM_SERVO_1_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(PWM_SERVO_2_GPIO_Port, PWM_SERVO_2_Pin, GPIO_PIN_SET);
  }

  if (servo_tick == servo_pulse[0])
  {
    /* 舵机1脉宽到达, 拉低 */
    HAL_GPIO_WritePin(PWM_SERVO_1_GPIO_Port, PWM_SERVO_1_Pin, GPIO_PIN_RESET);
  }

  if (servo_tick == servo_pulse[1])
  {
    /* 舵机2脉宽到达, 拉低 */
    HAL_GPIO_WritePin(PWM_SERVO_2_GPIO_Port, PWM_SERVO_2_Pin, GPIO_PIN_RESET);
  }

  if (servo_tick >= SERVO_PERIOD)
  {
    /* 20ms周期结束, 重启 */
    servo_tick = 0;
  }
}

/* ===== TIM7 10ms测速中断回调 ===== */
void HAL_TIM_PeriodElapsedCallback_TIM7(TIM_HandleTypeDef *htim)
{
  if (htim->Instance != TIM7) return;

  /* 丝印M1→编码器TIM5(PA0/PA1), 丝印M2→编码器TIM2(PA15/PB3) */
  int32_t cur1 = (int32_t)__HAL_TIM_GET_COUNTER(&htim5);
  int32_t cur2 = (int32_t)__HAL_TIM_GET_COUNTER(&htim2);

  encoder1_speed = cur1 - encoder1_last;
  encoder2_speed = cur2 - encoder2_last;

  /* 处理溢出: Period=60000, 如果差值超过一半说明溢出 */
  if (encoder1_speed > 30000)  encoder1_speed -= 60001;
  if (encoder1_speed < -30000) encoder1_speed += 60001;
  if (encoder2_speed > 30000)  encoder2_speed -= 60001;
  if (encoder2_speed < -30000) encoder2_speed += 60001;

  /* 右轮(Motor2)方向校准: 取反使正速度=前进 */
  encoder2_speed = -encoder2_speed;

  encoder1_last = cur1;
  encoder2_last = cur2;

  /* ===== PID闭环控制 ===== */
  if (pid1.enabled)
  {
    float pwm1 = PID_Calc(&pid1, (float)encoder1_speed);
    Motor_SetSpeed(0, (int16_t)pwm1);
  }
  if (pid2.enabled)
  {
    float pwm2 = PID_Calc(&pid2, (float)encoder2_speed);
    Motor_SetSpeed(1, (int16_t)pwm2);
  }
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */
  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_TIM1_Init();
  MX_TIM2_Init();
  MX_TIM5_Init();
  MX_TIM7_Init();
  MX_TIM13_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */

  /* === 启动串口中断接收 === */
  HAL_UART_Receive_IT(&huart1, &uart_rx_byte, 1);

  /* === 启动电机 PWM === */
  HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);
  HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_2);
  HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_3);
  HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_4);
  __HAL_TIM_MOE_ENABLE(&htim1);  /* TIM1是高级定时器,必须使能MOE才能输出PWM */

  /* === 启动编码器 === */
  HAL_TIM_Encoder_Start(&htim2, TIM_CHANNEL_1 | TIM_CHANNEL_2);
  HAL_TIM_Encoder_Start(&htim5, TIM_CHANNEL_1 | TIM_CHANNEL_2);
  __HAL_TIM_SET_COUNTER(&htim2, 30000);
  __HAL_TIM_SET_COUNTER(&htim5, 30000);
  encoder1_last = 30000;
  encoder2_last = 30000;

  /* === 启动测速中断 (10ms) === */
  HAL_TIM_Base_Start_IT(&htim7);

  /* === 启动舵机软件PWM中断 (10μs) === */
  /* 必须在启动前重新配置 TIM13 寄存器，因为 MX_TIM13_Init 里的
   * __HAL_TIM_SET_PRESCALER / __HAL_TIM_SET_AUTORELOAD 可能被
   * HAL_TIM_Base_Start_IT 内部的 __HAL_TIM_ENABLE 覆盖回 .ioc 的值 */
  __HAL_TIM_DISABLE(&htim13);
  htim13.Instance->PSC = 0;    /* PSC=0, 84MHz 不分频 */
  htim13.Instance->ARR = 839;  /* ARR=839, 84MHz/840 = 100kHz = 10μs */
  htim13.Instance->CNT = 0;    /* 清零计数器 */
  __HAL_TIM_CLEAR_FLAG(&htim13, TIM_FLAG_UPDATE);  /* 清除挂起的更新标志 */
  HAL_TIM_Base_Start_IT(&htim13);

  /* === 舵机/电机初始化 === */
  Servo_SetAngle(0, 90.0f);
  Servo_SetAngle(1, 90.0f);
  Motor_SetSpeed(0, 0);
  Motor_SetSpeed(1, 0);

  /* USER CODE END 2 */

  /* Init scheduler */
  osKernelInitialize();

  /* USER CODE BEGIN RTOS_MUTEX */
  /* add mutexes, ... */
  /* USER CODE END RTOS_MUTEX */

  /* USER CODE BEGIN RTOS_SEMAPHORES */
  /* add semaphores, ... */
  /* USER CODE END RTOS_SEMAPHORES */

  /* USER CODE BEGIN RTOS_TIMERS */
  /* start timers, add new ones, ... */
  /* USER CODE END RTOS_TIMERS */

  /* USER CODE BEGIN RTOS_QUEUES */
  /* add queues, ... */
  /* USER CODE END RTOS_QUEUES */

  /* Create the thread(s) */
  /* creation of defaultTask */
  defaultTaskHandle = osThreadNew(StartDefaultTask, NULL, &defaultTask_attributes);

  /* creation of LED_Task */
  LED_TaskHandle = osThreadNew(LED_Task_entry, NULL, &LED_Task_attributes);

  /* USER CODE BEGIN RTOS_THREADS */
  /* add threads, ... */
  /* USER CODE END RTOS_THREADS */

  /* USER CODE BEGIN RTOS_EVENTS */
  /* add events, ... */
  /* USER CODE END RTOS_EVENTS */

  /* Start scheduler */
  osKernelStart();

  /* We should never get here as control is now taken by the scheduler */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLM = 8;
  RCC_OscInitStruct.PLL.PLLN = 168;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = 4;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV4;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV2;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_5) != HAL_OK)
  {
    Error_Handler();
  }

  /** Enables the Clock Security System
  */
  HAL_RCC_EnableCSS();
}

/**
  * @brief TIM1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM1_Init(void)
{

  /* USER CODE BEGIN TIM1_Init 0 */

  /* USER CODE END TIM1_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};
  TIM_BreakDeadTimeConfigTypeDef sBreakDeadTimeConfig = {0};

  /* USER CODE BEGIN TIM1_Init 1 */

  /* USER CODE END TIM1_Init 1 */
  htim1.Instance = TIM1;
  htim1.Init.Prescaler = 839;
  htim1.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim1.Init.Period = 999;
  htim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim1.Init.RepetitionCounter = 0;
  htim1.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
  if (HAL_TIM_Base_Init(&htim1) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim1, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_Init(&htim1) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim1, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCNPolarity = TIM_OCNPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_ENABLE;
  sConfigOC.OCIdleState = TIM_OCIDLESTATE_RESET;
  sConfigOC.OCNIdleState = TIM_OCNIDLESTATE_RESET;
  if (HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_2) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_3) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_4) != HAL_OK)
  {
    Error_Handler();
  }
  sBreakDeadTimeConfig.OffStateRunMode = TIM_OSSR_DISABLE;
  sBreakDeadTimeConfig.OffStateIDLEMode = TIM_OSSI_DISABLE;
  sBreakDeadTimeConfig.LockLevel = TIM_LOCKLEVEL_OFF;
  sBreakDeadTimeConfig.DeadTime = 0;
  sBreakDeadTimeConfig.BreakState = TIM_BREAK_DISABLE;
  sBreakDeadTimeConfig.BreakPolarity = TIM_BREAKPOLARITY_HIGH;
  sBreakDeadTimeConfig.AutomaticOutput = TIM_AUTOMATICOUTPUT_DISABLE;
  if (HAL_TIMEx_ConfigBreakDeadTime(&htim1, &sBreakDeadTimeConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM1_Init 2 */

  /* USER CODE END TIM1_Init 2 */
  HAL_TIM_MspPostInit(&htim1);

}

/**
  * @brief TIM2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM2_Init(void)
{

  /* USER CODE BEGIN TIM2_Init 0 */

  /* USER CODE END TIM2_Init 0 */

  TIM_Encoder_InitTypeDef sConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};

  /* USER CODE BEGIN TIM2_Init 1 */

  /* USER CODE END TIM2_Init 1 */
  htim2.Instance = TIM2;
  htim2.Init.Prescaler = 0;
  htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim2.Init.Period = 60000;
  htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
  sConfig.EncoderMode = TIM_ENCODERMODE_TI12;
  sConfig.IC1Polarity = TIM_ICPOLARITY_RISING;
  sConfig.IC1Selection = TIM_ICSELECTION_DIRECTTI;
  sConfig.IC1Prescaler = TIM_ICPSC_DIV1;
  sConfig.IC1Filter = 0;
  sConfig.IC2Polarity = TIM_ICPOLARITY_RISING;
  sConfig.IC2Selection = TIM_ICSELECTION_DIRECTTI;
  sConfig.IC2Prescaler = TIM_ICPSC_DIV1;
  sConfig.IC2Filter = 0;
  if (HAL_TIM_Encoder_Init(&htim2, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim2, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM2_Init 2 */

  /* USER CODE END TIM2_Init 2 */

}

/**
  * @brief TIM5 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM5_Init(void)
{

  /* USER CODE BEGIN TIM5_Init 0 */

  /* USER CODE END TIM5_Init 0 */

  TIM_Encoder_InitTypeDef sConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};

  /* USER CODE BEGIN TIM5_Init 1 */

  /* USER CODE END TIM5_Init 1 */
  htim5.Instance = TIM5;
  htim5.Init.Prescaler = 0;
  htim5.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim5.Init.Period = 60000;
  htim5.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim5.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
  sConfig.EncoderMode = TIM_ENCODERMODE_TI12;
  sConfig.IC1Polarity = TIM_ICPOLARITY_RISING;
  sConfig.IC1Selection = TIM_ICSELECTION_DIRECTTI;
  sConfig.IC1Prescaler = TIM_ICPSC_DIV1;
  sConfig.IC1Filter = 0;
  sConfig.IC2Polarity = TIM_ICPOLARITY_RISING;
  sConfig.IC2Selection = TIM_ICSELECTION_DIRECTTI;
  sConfig.IC2Prescaler = TIM_ICPSC_DIV1;
  sConfig.IC2Filter = 0;
  if (HAL_TIM_Encoder_Init(&htim5, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim5, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM5_Init 2 */

  /* USER CODE END TIM5_Init 2 */

}

/**
  * @brief TIM7 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM7_Init(void)
{

  /* USER CODE BEGIN TIM7_Init 0 */

  /* USER CODE END TIM7_Init 0 */

  TIM_MasterConfigTypeDef sMasterConfig = {0};

  /* USER CODE BEGIN TIM7_Init 1 */

  /* USER CODE END TIM7_Init 1 */
  htim7.Instance = TIM7;
  htim7.Init.Prescaler = 83;
  htim7.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim7.Init.Period = 9999;
  htim7.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
  if (HAL_TIM_Base_Init(&htim7) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim7, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM7_Init 2 */

  /* USER CODE END TIM7_Init 2 */

}

/**
  * @brief TIM13 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM13_Init(void)
{

  /* USER CODE BEGIN TIM13_Init 0 */

  /* USER CODE END TIM13_Init 0 */

  /* USER CODE BEGIN TIM13_Init 1 */

  /* USER CODE END TIM13_Init 1 */
  htim13.Instance = TIM13;
  htim13.Init.Prescaler = 0;
  htim13.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim13.Init.Period = 839;
  htim13.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim13.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim13) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM13_Init 2 */

  /* USER CODE END TIM13_Init 2 */

}

/**
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 115200;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
/* USER CODE BEGIN MX_GPIO_Init_1 */
/* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOH_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOE_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(LED1_GPIO_Port, LED1_Pin, GPIO_PIN_SET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOA, PWM_SERVO_1_Pin|PWM_SERVO_2_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin : LED1_Pin */
  GPIO_InitStruct.Pin = LED1_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(LED1_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : PWM_SERVO_1_Pin PWM_SERVO_2_Pin */
  GPIO_InitStruct.Pin = PWM_SERVO_1_Pin|PWM_SERVO_2_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

/* USER CODE BEGIN MX_GPIO_Init_2 */
/* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* ===== 串口接收完成回调 ===== */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
  if (huart->Instance != USART1) return;

  static char cmd_buf[32];
  static uint8_t cmd_idx = 0;

  /* 忽略换行符，只用作指令结束标记 */
  if (uart_rx_byte == '\r' || uart_rx_byte == '\n')
  {
    if (cmd_idx > 0)
    {
      cmd_buf[cmd_idx] = '\0';

      /* 指令集: S1/S2=舵机角度 M1/M2=开环PWM V1/V2=PID速度目标
       * KP/KI/KD=全局PID增益 KP1..RAMP2=单电机PID参数
       * RP1/RP2=读回PID参数 RST1/RST2=复位积分
       * 支持 = 或 : 分隔符 */
      char *sep = strchr(cmd_buf, '=');
      if (!sep) sep = strchr(cmd_buf, ':');

      if (sep)
      {
        *sep = '\0';  /* 分割: cmd_buf=指令名, sep+1=参数 */
        if (strcmp(cmd_buf, "S1") == 0)
        {
          float angle = atof(sep + 1);
          Servo_SetAngle(0, angle);
          uart_printf("Servo1 -> %.1f deg\r\n", angle);
        }
        else if (strcmp(cmd_buf, "S2") == 0)
        {
          float angle = atof(sep + 1);
          Servo_SetAngle(1, angle);
          uart_printf("Servo2 -> %.1f deg\r\n", angle);
        }
        else if (strcmp(cmd_buf, "M1") == 0)
        {
          int16_t speed = (int16_t)atoi(sep + 1);
          pid1.enabled = 0;          /* 切换到开环模式 */
          Motor_SetSpeed(0, speed);
          uart_printf("Motor1 -> %d\r\n", speed);
        }
        else if (strcmp(cmd_buf, "M2") == 0)
        {
          int16_t speed = (int16_t)atoi(sep + 1);
          pid2.enabled = 0;          /* 切换到开环模式 */
          Motor_SetSpeed(1, speed);
          uart_printf("Motor2 -> %d\r\n", speed);
        }
        /* ---- 速度闭环(V1/V2) ---- */
        else if (strcmp(cmd_buf, "V1") == 0)
        {
          float target = atof(sep + 1);
          PID_SetTarget(&pid1, target);
          if (target == 0.0f) Motor_SetSpeed(0, 0);
        }
        else if (strcmp(cmd_buf, "V2") == 0)
        {
          float target = atof(sep + 1);
          PID_SetTarget(&pid2, target);
          if (target == 0.0f) Motor_SetSpeed(1, 0);
        }
        /* ---- 全局PID参数(KP/KI/KD) 同时设置两电机 ---- */
        else if (strcmp(cmd_buf, "KP") == 0)
        {
          float v = atof(sep + 1);
          pid1.kp = pid2.kp = v;
          uart_printf("kp=%.3f\r\n", (double)v);
        }
        else if (strcmp(cmd_buf, "KI") == 0)
        {
          float v = atof(sep + 1);
          pid1.ki = pid2.ki = v;
          uart_printf("ki=%.3f\r\n", (double)v);
        }
        else if (strcmp(cmd_buf, "KD") == 0)
        {
          float v = atof(sep + 1);
          pid1.kd = pid2.kd = v;
          uart_printf("kd=%.3f\r\n", (double)v);
        }
        /* ---- 电机1独立PID参数 ---- */
        else if (strcmp(cmd_buf, "KP1") == 0)
        {
          pid1.kp = atof(sep + 1);
          uart_printf("kp1=%.3f\r\n", (double)pid1.kp);
        }
        else if (strcmp(cmd_buf, "KI1") == 0)
        {
          pid1.ki = atof(sep + 1);
          uart_printf("ki1=%.3f\r\n", (double)pid1.ki);
        }
        else if (strcmp(cmd_buf, "KD1") == 0)
        {
          pid1.kd = atof(sep + 1);
          uart_printf("kd1=%.3f\r\n", (double)pid1.kd);
        }
        else if (strcmp(cmd_buf, "IMAX1") == 0)
        {
          pid1.i_limit = atof(sep + 1);
          uart_printf("ilim1=%.1f\r\n", (double)pid1.i_limit);
        }
        else if (strcmp(cmd_buf, "OMAX1") == 0)
        {
          pid1.out_max = atof(sep + 1);
          uart_printf("omax1=%.1f\r\n", (double)pid1.out_max);
        }
        else if (strcmp(cmd_buf, "DB1") == 0)
        {
          pid1.deadband = atof(sep + 1);
          uart_printf("db1=%.1f\r\n", (double)pid1.deadband);
        }
        else if (strcmp(cmd_buf, "RAMP1") == 0)
        {
          pid1.ramp = atof(sep + 1);
          uart_printf("ramp1=%.1f\r\n", (double)pid1.ramp);
        }
        /* ---- 电机2独立PID参数 ---- */
        else if (strcmp(cmd_buf, "KP2") == 0)
        {
          pid2.kp = atof(sep + 1);
          uart_printf("kp2=%.3f\r\n", (double)pid2.kp);
        }
        else if (strcmp(cmd_buf, "KI2") == 0)
        {
          pid2.ki = atof(sep + 1);
          uart_printf("ki2=%.3f\r\n", (double)pid2.ki);
        }
        else if (strcmp(cmd_buf, "KD2") == 0)
        {
          pid2.kd = atof(sep + 1);
          uart_printf("kd2=%.3f\r\n", (double)pid2.kd);
        }
        else if (strcmp(cmd_buf, "IMAX2") == 0)
        {
          pid2.i_limit = atof(sep + 1);
          uart_printf("ilim2=%.1f\r\n", (double)pid2.i_limit);
        }
        else if (strcmp(cmd_buf, "OMAX2") == 0)
        {
          pid2.out_max = atof(sep + 1);
          uart_printf("omax2=%.1f\r\n", (double)pid2.out_max);
        }
        else if (strcmp(cmd_buf, "DB2") == 0)
        {
          pid2.deadband = atof(sep + 1);
          uart_printf("db2=%.1f\r\n", (double)pid2.deadband);
        }
        else if (strcmp(cmd_buf, "RAMP2") == 0)
        {
          pid2.ramp = atof(sep + 1);
          uart_printf("ramp2=%.1f\r\n", (double)pid2.ramp);
        }
        /* ---- 读回全部PID参数(RP1/RP2) ---- */
        else if (strcmp(cmd_buf, "RP1") == 0)
        {
          PID_Report(1, &pid1);
        }
        else if (strcmp(cmd_buf, "RP2") == 0)
        {
          PID_Report(2, &pid2);
        }
        /* ---- 复位积分累加器(RST1/RST2) ---- */
        else if (strcmp(cmd_buf, "RST1") == 0)
        {
          PID_Reset(&pid1);
          uart_printf("PID1 integral reset\r\n");
        }
        else if (strcmp(cmd_buf, "RST2") == 0)
        {
          PID_Reset(&pid2);
          uart_printf("PID2 integral reset\r\n");
        }
        else
        {
          uart_printf("Unknown cmd: %s\r\n", cmd_buf);
        }
      }
      else
      {
        uart_printf("Bad fmt: %s (use S1=90)\r\n", cmd_buf);
      }
      cmd_idx = 0;
    }
  }
  else
  {
    if (cmd_idx < sizeof(cmd_buf) - 1)
      cmd_buf[cmd_idx++] = uart_rx_byte;
    else
      cmd_idx = 0;  /* 溢出重置 */
  }

  /* 重新开启接收 */
  HAL_UART_Receive_IT(&huart1, &uart_rx_byte, 1);
}

/* USER CODE END 4 */

/* USER CODE BEGIN Header_StartDefaultTask */
/**
  * @brief  Function implementing the defaultTask thread.
  * @param  argument: Not used
  * @retval None
  */
/* USER CODE END Header_StartDefaultTask */
void StartDefaultTask(void *argument)
{
  /* USER CODE BEGIN 5 */
  uart_printf("Family Bot Ready!\r\n");

  /* Infinite loop */
  for(;;)
  {
    /* 打印速度和PID状态 */
    /* 格式: E1=实际速度 T1=目标速度 E2=实际速度 T2=目标速度 */
    uart_printf("E1=%ld T1=%.0f | E2=%ld T2=%.0f\r\n",
                (long)encoder1_speed, pid1.target,
                (long)encoder2_speed, pid2.target);
    osDelay(500);
  }
  /* USER CODE END 5 */
}

/* USER CODE BEGIN Header_LED_Task_entry */
/**
* @brief Function implementing the LED_Task thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_LED_Task_entry */
__weak void LED_Task_entry(void *argument)
{
  /* USER CODE BEGIN LED_Task_entry */
  /* Infinite loop */
  for(;;)
  {
	  HAL_GPIO_WritePin(LED1_GPIO_Port, LED1_Pin, GPIO_PIN_SET);
	  osDelay(1000);
	  HAL_GPIO_WritePin(LED1_GPIO_Port, LED1_Pin, GPIO_PIN_RESET);
	  osDelay(500);
  }
  /* USER CODE END LED_Task_entry */
}

/**
  * @brief  Period elapsed callback in non blocking mode
  * @note   This function is called  when TIM14 interrupt took place, inside
  * HAL_TIM_IRQHandler(). It makes a direct call to HAL_IncTick() to increment
  * a global variable "uwTick" used as application time base.
  * @param  htim : TIM handle
  * @retval None
  */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
  /* USER CODE BEGIN Callback 0 */

  /* USER CODE END Callback 0 */
  if (htim->Instance == TIM14) {
    HAL_IncTick();
  }
  /* USER CODE BEGIN Callback 1 */
  if (htim->Instance == TIM7) {
    HAL_TIM_PeriodElapsedCallback_TIM7(htim);
  }
  else if (htim->Instance == TIM13) {
    HAL_TIM_PeriodElapsedCallback_TIM13(htim);
  }
  /* USER CODE END Callback 1 */
}

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
