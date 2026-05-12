package com.familyrobot.controller;

import com.familyrobot.model.dto.SettingsDto;
import com.familyrobot.model.entity.User;
import com.familyrobot.service.SettingsService;
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

    @PutMapping
    public ResponseEntity<SettingsDto> updateSettings(@AuthenticationPrincipal User user,
                                                       @RequestBody SettingsDto dto) {
        return ResponseEntity.ok(settingsService.updateSettings(user.getId(), dto));
    }
}
