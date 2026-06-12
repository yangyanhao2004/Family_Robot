package com.familyrobot.controller;

import com.familyrobot.model.entity.User;
import com.familyrobot.repository.UserRepository;
import com.familyrobot.service.EmailService;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@Slf4j
@RestController
@RequestMapping("/api/emergency")
@RequiredArgsConstructor
public class EmergencyController {

    private final EmailService emailService;
    private final UserRepository userRepository;

    @PostMapping("/send-mail")
    public ResponseEntity<?> sendEmergencyMail(@RequestBody EmergencyMailRequest request) {
        User user = userRepository.findById(request.getUserId())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "User not found"));

        String contactName = user.getEmergencyContactName();
        String contactEmail = user.getEmergencyContactEmail();

        if (contactEmail == null || contactEmail.isBlank()) {
            return ResponseEntity.badRequest().body("No emergency contact email configured");
        }

        String time = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        String displayName = contactName != null && !contactName.isBlank() ? contactName : contactEmail;

        emailService.sendEmergencyEmail(contactEmail, user.getName(), time, displayName);
        log.info("Emergency mail sent to {} for user {} (detected at {})", contactEmail, user.getId(), time);

        return ResponseEntity.ok(new EmergencyMailResponse(contactName, contactEmail, time));
    }

    @Data
    private static class EmergencyMailRequest {
        private Long userId;
    }

    @Data
    @AllArgsConstructor
    private static class EmergencyMailResponse {
        private String contactName;
        private String contactEmail;
        private String time;
    }
}
