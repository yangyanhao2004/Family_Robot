package com.familyrobot.model.dto;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
public class AdminRobotDto {
    private Long id;
    private String serialNumber;
    private String boundUserEmail;
    private LocalDateTime createdAt;
}
