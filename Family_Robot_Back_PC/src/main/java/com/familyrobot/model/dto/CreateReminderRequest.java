package com.familyrobot.model.dto;

import lombok.Data;

@Data
public class CreateReminderRequest {
    private Long userId;
    private String text;
    private String scheduledTime;
    private String method;
    private String email;
}
