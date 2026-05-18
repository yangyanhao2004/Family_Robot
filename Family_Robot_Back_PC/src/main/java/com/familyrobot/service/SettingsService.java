package com.familyrobot.service;

import com.familyrobot.model.dto.SettingsDto;
import com.familyrobot.model.entity.User;
import com.familyrobot.model.entity.UserSettings;
import com.familyrobot.repository.SettingsRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class SettingsService {

    private final SettingsRepository settingsRepository;

    public SettingsDto getSettings(Long userId) {
        UserSettings settings = settingsRepository.findByUserId(userId)
                .orElseGet(() -> createDefault(userId));
        return toDto(settings);
    }

    private UserSettings createDefault(Long userId) {
        UserSettings settings = UserSettings.builder()
                .user(User.builder().id(userId).build())
                .firmwareVersion("v2.4.1 (latest)")
                .serialNumber("RBT-00001")
                .build();
        return settingsRepository.save(settings);
    }

    private SettingsDto toDto(UserSettings s) {
        return SettingsDto.builder()
                .firmwareVersion(s.getFirmwareVersion())
                .serialNumber(s.getSerialNumber())
                .build();
    }
}
