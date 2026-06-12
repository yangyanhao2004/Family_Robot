package com.familyrobot.service;

import com.familyrobot.model.dto.ProfileDto;
import com.familyrobot.model.entity.User;
import com.familyrobot.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.format.DateTimeFormatter;

@Service
@RequiredArgsConstructor
public class UserService {

    public ProfileDto getProfile(User user) {
        return ProfileDto.builder()
                .name(user.getName())
                .email(user.getEmail())
                .role(user.getRole())
                .lastLogin(user.getLastLogin() != null
                        ? user.getLastLogin().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))
                        : "N/A")
                .emergencyContactName(user.getEmergencyContactName())
                .emergencyContactEmail(user.getEmergencyContactEmail())
                .build();
    }
}
