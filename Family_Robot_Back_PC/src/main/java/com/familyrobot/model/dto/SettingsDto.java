package com.familyrobot.model.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class SettingsDto {
    private String firmwareVersion;
    private String serialNumber;
    private String emergencyContactName;
    private String emergencyContactEmail;
}
