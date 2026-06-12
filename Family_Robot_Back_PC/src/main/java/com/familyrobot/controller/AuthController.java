package com.familyrobot.controller;

import com.familyrobot.model.dto.LoginRequest;
import com.familyrobot.model.dto.LoginResponse;
import com.familyrobot.model.dto.RegisterRequest;
import com.familyrobot.model.dto.VerifyRequest;
import com.familyrobot.model.entity.User;
import com.familyrobot.security.JwtTokenProvider;
import com.familyrobot.service.AuthService;
import com.familyrobot.service.VerificationService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;
    private final VerificationService verificationService;
    private final JwtTokenProvider tokenProvider;

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        return ResponseEntity.ok(authService.login(request));
    }

    @PostMapping("/register")
    public ResponseEntity<Map<String, String>> register(@Valid @RequestBody RegisterRequest request) {
        verificationService.sendVerificationCode(
                request.getEmail(), request.getPassword(), request.getSerialNumber(),
                request.getEmergencyContactName(), request.getEmergencyContactEmail());
        return ResponseEntity.ok(Map.of("message", "verification code sent"));
    }

    @PostMapping("/verify")
    public ResponseEntity<Map<String, String>> verify(@Valid @RequestBody VerifyRequest request) {
        verificationService.verify(request.getEmail(), request.getCode());
        return ResponseEntity.ok(Map.of("message", "verified"));
    }

    @PostMapping("/login-code/send")
    public ResponseEntity<Map<String, String>> sendLoginCode(@Valid @RequestBody SendLoginCodeRequest request) {
        verificationService.sendLoginCode(request.getEmail());
        return ResponseEntity.ok(Map.of("message", "verification code sent"));
    }

    @PostMapping("/login-code/verify")
    public ResponseEntity<LoginResponse> verifyLoginCode(@Valid @RequestBody VerifyLoginCodeRequest request) {
        User user = verificationService.verifyLoginCode(request.getEmail(), request.getCode());
        String token = tokenProvider.generateToken(user.getId(), user.getEmail());
        return ResponseEntity.ok(new LoginResponse(token, user.getRole()));
    }

    @PostMapping("/reset-password/send")
    public ResponseEntity<Map<String, String>> sendResetPasswordCode(@Valid @RequestBody SendLoginCodeRequest request) {
        verificationService.sendResetPasswordCode(request.getEmail());
        return ResponseEntity.ok(Map.of("message", "verification code sent"));
    }

    @PostMapping("/reset-password/verify")
    public ResponseEntity<Map<String, String>> resetPassword(@Valid @RequestBody ResetPasswordRequest request) {
        verificationService.resetPassword(request.getEmail(), request.getCode(), request.getNewPassword());
        return ResponseEntity.ok(Map.of("message", "password reset successfully"));
    }

    @Data
    private static class SendLoginCodeRequest {
        @NotBlank private String email;
    }

    @Data
    private static class VerifyLoginCodeRequest {
        @NotBlank private String email;
        @NotBlank private String code;
    }

    @Data
    private static class ResetPasswordRequest {
        @NotBlank private String email;
        @NotBlank private String code;
        @NotBlank private String newPassword;
    }
}
