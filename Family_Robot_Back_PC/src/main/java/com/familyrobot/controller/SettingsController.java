package com.familyrobot.controller;

import com.familyrobot.model.dto.SettingsDto;
import com.familyrobot.model.entity.User;
import com.familyrobot.service.SettingsService;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/settings")
@RequiredArgsConstructor
public class SettingsController {

    private final SettingsService settingsService;

    @GetMapping
    public ResponseEntity<SettingsDto> getSettings(@AuthenticationPrincipal User user) {
        return ResponseEntity.ok(settingsService.getSettings(user.getId()));
    }

    @PutMapping("/emergency-contact")
    public ResponseEntity<SettingsDto> updateEmergencyContact(
            @AuthenticationPrincipal User user,
            @RequestBody UpdateEmergencyContactRequest request) {
        return ResponseEntity.ok(
                settingsService.updateEmergencyContact(user.getId(),
                        request.getName(), request.getEmail()));
    }

    @Data
    private static class UpdateEmergencyContactRequest {
        private String name;
        private String email;
    }
}
