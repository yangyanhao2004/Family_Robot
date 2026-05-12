package com.familyrobot.model.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class CommandLogRequest {
    @NotBlank
    private String command;

    private String source;
}
