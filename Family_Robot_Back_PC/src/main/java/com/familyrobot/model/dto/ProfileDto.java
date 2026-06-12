package com.familyrobot.model.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ProfileDto {
    private String name;
    private String email;
    private String role;
    private String lastLogin;
    private String emergencyContactName;
    private String emergencyContactEmail;
}
