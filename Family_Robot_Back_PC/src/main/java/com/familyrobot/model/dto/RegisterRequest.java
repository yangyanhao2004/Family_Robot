package com.familyrobot.model.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class RegisterRequest {
    @NotBlank @Email
    private String email;

    @NotBlank
    private String password;

    @NotBlank
    private String serialNumber;

    private String emergencyContactName;

    private String emergencyContactEmail;
}
