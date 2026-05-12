package com.familyrobot.model.dto;

import lombok.Builder;
import lombok.Data;

import java.util.List;

@Data
@Builder
public class AdminUserDto {
    private Long userId;
    private String email;
    private String name;
    private String role;
    private String passwordHash;
    private List<String> robotSerialNumbers;
}
