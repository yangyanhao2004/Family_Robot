package com.familyrobot.controller;

import com.familyrobot.model.dto.AdminRobotDto;
import com.familyrobot.model.dto.AdminUserDto;
import com.familyrobot.model.dto.RobotRegistrationRequest;
import com.familyrobot.model.entity.Robot;
import com.familyrobot.model.entity.User;
import com.familyrobot.repository.*;
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
    private final PhotoRepository photoRepository;
    private final CommandLogRepository commandLogRepository;
    private final VerificationCodeRepository verificationCodeRepository;
    private final SettingsRepository settingsRepository;
    private final ReminderRepository reminderRepository;
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
                : userRepository.findAllByRoleNot("Admin");
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

    @DeleteMapping("/users/{userId}")
    @Transactional
    public ResponseEntity<Map<String, String>> deleteUser(
            @AuthenticationPrincipal User admin,
            @PathVariable Long userId) {
        requireAdmin(admin);

        User target = userRepository.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "User not found"));

        if (target.getId().equals(admin.getId())) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Cannot delete your own admin account");
        }

        String email = target.getEmail();
        log.warn("Admin {} (id={}) is deleting user {} (id={}, email={}) and all related data",
                admin.getEmail(), admin.getId(), target.getName(), userId, email);

        // Cascade delete all related data (order matters due to FK constraints)
        robotRepository.deleteAllByUserId(userId);
        photoRepository.deleteAllByUserId(userId);
        commandLogRepository.deleteAllByUserId(userId);
        settingsRepository.deleteByUserId(userId);
        reminderRepository.deleteAllByUserId(userId);
        verificationCodeRepository.deleteAllByEmail(email);
        userRepository.delete(target);

        log.info("User {} and all related data deleted successfully", userId);
        return ResponseEntity.ok(Map.of("message", "User and all related data deleted"));
    }

    @DeleteMapping("/robots/{robotId}")
    @Transactional
    public ResponseEntity<Map<String, String>> deleteRobot(
            @AuthenticationPrincipal User admin,
            @PathVariable Long robotId) {
        requireAdmin(admin);

        Robot target = robotRepository.findById(robotId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Robot not found"));

        User boundUser = target.getUser();
        log.warn("Admin {} (id={}) is deleting robot #{} (serial={})",
                admin.getEmail(), admin.getId(), robotId, target.getSerialNumber());

        // Delete robot first, then cascade-delete bound user if exists
        robotRepository.delete(target);

        if (boundUser != null) {
            Long userId = boundUser.getId();
            String email = boundUser.getEmail();
            log.warn("Cascade-deleting bound user {} (id={}, email={})", boundUser.getName(), userId, email);

            robotRepository.deleteAllByUserId(userId);
            photoRepository.deleteAllByUserId(userId);
            commandLogRepository.deleteAllByUserId(userId);
            settingsRepository.deleteByUserId(userId);
            reminderRepository.deleteAllByUserId(userId);
            verificationCodeRepository.deleteAllByEmail(email);
            userRepository.delete(boundUser);

            log.info("Robot #{} and bound user {} deleted successfully", robotId, userId);
            return ResponseEntity.ok(Map.of("message", "Robot and bound user deleted"));
        }

        log.info("Robot #{} (unbound) deleted successfully", robotId);
        return ResponseEntity.ok(Map.of("message", "Robot deleted"));
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
