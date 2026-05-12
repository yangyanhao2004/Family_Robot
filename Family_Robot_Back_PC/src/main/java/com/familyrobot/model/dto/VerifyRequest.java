package com.familyrobot.model.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class VerifyRequest {
    @NotBlank
    private String email;

    @NotBlank
    private String code;
}
