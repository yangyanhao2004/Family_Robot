package com.familyrobot.model.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ReminderDto {
    private Long id;
    private String text;
    private String scheduledTime;
    private String method;
    private String email;
    private Boolean enabled;
    private Boolean sent;
}
