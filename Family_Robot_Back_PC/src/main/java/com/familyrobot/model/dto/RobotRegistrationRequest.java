package com.familyrobot.model.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class RobotRegistrationRequest {
    @NotBlank
    private String serialNumber;
}
