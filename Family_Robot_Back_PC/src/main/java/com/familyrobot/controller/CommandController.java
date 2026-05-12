package com.familyrobot.controller;

import com.familyrobot.model.dto.CommandLogRequest;
import com.familyrobot.model.entity.CommandLog;
import com.familyrobot.model.entity.User;
import com.familyrobot.repository.CommandLogRepository;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/commands")
@RequiredArgsConstructor
public class CommandController {

    private final CommandLogRepository commandLogRepository;

    @PostMapping
    public ResponseEntity<Map<String, String>> logCommand(
            @AuthenticationPrincipal User user,
            @Valid @RequestBody CommandLogRequest request) {
        CommandLog log = CommandLog.builder()
                .command(request.getCommand())
                .source(request.getSource())
                .user(user)
                .build();
        commandLogRepository.save(log);
        return ResponseEntity.ok(Map.of("message", "logged"));
    }
}
