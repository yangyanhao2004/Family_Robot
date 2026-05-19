package com.familyrobot.controller;

import com.familyrobot.model.dto.AdminRobotDto;
import com.familyrobot.model.dto.AdminUserDto;
import com.familyrobot.model.dto.RobotRegistrationRequest;
import com.familyrobot.model.entity.Robot;
import com.familyrobot.model.entity.User;
import com.familyrobot.repository.RobotRepository;
import com.familyrobot.repository.UserRepository;
import com.familyrobot.security.AesPasswordEncoder;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/admin")
@RequiredArgsConstructor
@Slf4j
public class AdminController {

    private final UserRepository userRepository;
    private final RobotRepository robotRepository;
    private final AesPasswordEncoder aesPasswordEncoder;

    private void requireAdmin(User user) {
        if (!"Admin".equals(user.getRole())) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Admin access required");
        }
    }

    @GetMapping("/users")
    @Transactional(readOnly = true)
    public ResponseEntity<List<AdminUserDto>> listUsers(
            @AuthenticationPrincipal User user,
            @RequestParam(required = false) String search) {
        requireAdmin(user);

        List<User> users = (search != null && !search.isBlank())
                ? userRepository.findFilteredUsers(search.trim())
                : userRepository.findAll();
        List<Robot> robots = robotRepository.findAll();

        List<AdminUserDto> dtos = users.stream()
                .map(u -> AdminUserDto.builder()
                        .userId(u.getId())
                        .email(u.getEmail())
                        .name(u.getName())
                        .role(u.getRole())
                        .robotSerialNumbers(robots.stream()
                                .filter(r -> r.getUser() != null && r.getUser().getId().equals(u.getId()))
                                .map(Robot::getSerialNumber)
                                .toList())
                        .build())
                .toList();

        return ResponseEntity.ok(dtos);
    }

    @GetMapping("/users/{userId}/password")
    public ResponseEntity<Map<String, String>> getUserPassword(
            @AuthenticationPrincipal User admin,
            @PathVariable Long userId) {
        requireAdmin(admin);

        User targetUser = userRepository.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "User not found"));

        String plaintext = aesPasswordEncoder.decrypt(targetUser.getPassword());
        log.warn("Admin {} (id={}) viewed plaintext password of user {} (id={})",
                admin.getEmail(), admin.getId(), targetUser.getEmail(), userId);

        return ResponseEntity.ok(Map.of("password", plaintext));
    }

    @GetMapping("/robots")
    @Transactional(readOnly = true)
    public ResponseEntity<List<AdminRobotDto>> listRobots(
            @AuthenticationPrincipal User user,
            @RequestParam(required = false) String search,
            @RequestParam(required = false, defaultValue = "asc") String sortOrder,
            @RequestParam(required = false) String startDate,
            @RequestParam(required = false) String endDate) {
        requireAdmin(user);

        String trimmedSearch = (search != null && !search.isBlank()) ? search.trim() : null;
        LocalDateTime start = parseDateTime(startDate, false);
        LocalDateTime end = parseDateTime(endDate, true);

        List<Robot> robots = (trimmedSearch != null || start != null || end != null)
                ? robotRepository.findFilteredRobots(trimmedSearch, start, end)
                : robotRepository.findAll();

        // Sort
        if ("desc".equalsIgnoreCase(sortOrder)) {
            robots.sort(Comparator.comparing(Robot::getCreatedAt).reversed());
        } else {
            robots.sort(Comparator.comparing(Robot::getCreatedAt));
        }

        List<AdminRobotDto> dtos = robots.stream()
                .map(r -> AdminRobotDto.builder()
                        .id(r.getId())
                        .serialNumber(r.getSerialNumber())
                        .boundUserEmail(r.getUser() != null ? r.getUser().getEmail() : null)
                        .createdAt(r.getCreatedAt())
                        .build())
                .toList();

        return ResponseEntity.ok(dtos);
    }

    @PostMapping("/robots")
    public ResponseEntity<Map<String, String>> registerRobot(
            @AuthenticationPrincipal User user,
            @Valid @RequestBody RobotRegistrationRequest request) {
        requireAdmin(user);

        if (robotRepository.findBySerialNumber(request.getSerialNumber()).isPresent()) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Serial number already exists");
        }

        Robot robot = Robot.builder()
                .serialNumber(request.getSerialNumber())
                .build();
        robotRepository.save(robot);

        return ResponseEntity.ok(Map.of("message", "registered"));
    }

    private LocalDateTime parseDateTime(String value, boolean isEnd) {
        if (value == null || value.isBlank()) return null;
        try {
            if (value.contains("T")) {
                return LocalDateTime.parse(value);
            }
            LocalDate date = LocalDate.parse(value);
            return isEnd ? date.atTime(LocalTime.MAX) : date.atStartOfDay();
        } catch (Exception e) {
            log.warn("Failed to parse date param: {}", value);
            return null;
        }
    }
}
