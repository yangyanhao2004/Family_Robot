package com.familyrobot.model.dto;

import lombok.Data;

@Data
public class UpdateReminderRequest {
    private String text;
    private String scheduledTime;
    private String method;
    private String email;
    private Boolean enabled;
}
