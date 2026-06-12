package com.familyrobot.service;

import com.familyrobot.model.dto.SettingsDto;
import com.familyrobot.model.entity.User;
import com.familyrobot.model.entity.UserSettings;
import com.familyrobot.repository.SettingsRepository;
import com.familyrobot.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

@Service
@RequiredArgsConstructor
public class SettingsService {

    private final SettingsRepository settingsRepository;
    private final UserRepository userRepository;

    public SettingsDto getSettings(Long userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "User not found"));
        UserSettings settings = settingsRepository.findByUserId(userId)
                .orElseGet(() -> createDefault(userId));
        return toDto(settings, user);
    }

    public SettingsDto updateEmergencyContact(Long userId, String name, String email) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "User not found"));
        user.setEmergencyContactName(name);
        user.setEmergencyContactEmail(email);
        userRepository.save(user);
        UserSettings settings = settingsRepository.findByUserId(userId)
                .orElseGet(() -> createDefault(userId));
        return toDto(settings, user);
    }

    private UserSettings createDefault(Long userId) {
        UserSettings settings = UserSettings.builder()
                .user(User.builder().id(userId).build())
                .firmwareVersion("v2.4.1 (latest)")
                .serialNumber("RBT-00001")
                .build();
        return settingsRepository.save(settings);
    }

    private SettingsDto toDto(UserSettings s, User user) {
        return SettingsDto.builder()
                .firmwareVersion(s.getFirmwareVersion())
                .serialNumber(s.getSerialNumber())
                .emergencyContactName(user.getEmergencyContactName())
                .emergencyContactEmail(user.getEmergencyContactEmail())
                .build();
    }
}
