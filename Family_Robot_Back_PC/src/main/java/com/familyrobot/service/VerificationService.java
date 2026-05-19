package com.familyrobot.service;

import com.familyrobot.model.entity.Robot;
import com.familyrobot.model.entity.User;
import com.familyrobot.model.entity.VerificationCode;
import com.familyrobot.repository.RobotRepository;
import com.familyrobot.repository.UserRepository;
import com.familyrobot.repository.VerificationCodeRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.util.Random;

@Slf4j
@Service
@RequiredArgsConstructor
public class VerificationService {

    private static final String TYPE_REGISTER = "REGISTER";
    private static final String TYPE_LOGIN = "LOGIN";
    private static final String TYPE_RESET_PASSWORD = "RESET_PASSWORD";

    private final EmailService emailService;
    private final UserRepository userRepository;
    private final RobotRepository robotRepository;
    private final VerificationCodeRepository codeRepository;
    private final PasswordEncoder passwordEncoder;
    private final Random random = new Random();

    private String newCode() {
        return String.format("%06d", random.nextInt(1000000));
    }

    private VerificationCode saveCode(String email, String type, String code, String extraData) {
        VerificationCode vc = VerificationCode.builder()
                .email(email)
                .type(type)
                .code(code)
                .extraData(extraData)
                .expiresAt(LocalDateTime.now().plusMinutes(5))
                .build();
        return codeRepository.save(vc);
    }

    private VerificationCode findAndValidate(String email, String type, String code) {
        VerificationCode vc = codeRepository
                .findTopByEmailAndTypeAndUsedFalseAndExpiresAtAfterOrderByExpiresAtDesc(
                        email, type, LocalDateTime.now())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.BAD_REQUEST,
                        "No pending code or code expired"));

        if (!vc.getCode().equals(code)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid verification code");
        }

        vc.setUsed(true);
        codeRepository.save(vc);
        return vc;
    }

    // ---- Registration ----

    public void sendVerificationCode(String email, String password, String serialNumber) {
        if (userRepository.findByEmail(email).isPresent()) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Email already registered");
        }

        Robot robot = robotRepository.findBySerialNumber(serialNumber)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Serial number not found"));

        if (robot.getUser() != null) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "This robot is already bound to another account");
        }

        String code = newCode();
        // Store encrypted password + serialNumber as extraData
        saveCode(email, TYPE_REGISTER, code,
                passwordEncoder.encode(password) + "|" + serialNumber);

        emailService.sendVerificationEmail(email, "Family Robot - Email Verification Code", "Your verification code is:", code);
        log.info("Verification code sent to {}", email);
    }

    @Transactional
    public void verify(String email, String code) {
        VerificationCode vc = findAndValidate(email, TYPE_REGISTER, code);

        String[] parts = vc.getExtraData().split("\\|", 2);
        String encodedPassword = parts[0];
        String serialNumber = parts[1];

        User user = User.builder()
                .email(email)
                .password(encodedPassword)
                .name(email.split("@")[0])
                .role("User")
                .build();
        userRepository.save(user);

        Robot robot = robotRepository.findBySerialNumber(serialNumber).orElseThrow();
        robot.setUser(user);
        robotRepository.save(robot);

        log.info("User registered: {} with robot {}", email, serialNumber);
    }

    // ---- Login with code ----

    public void sendLoginCode(String email) {
        userRepository.findByEmail(email)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "该邮箱未注册，请先注册账户"));

        String code = newCode();
        saveCode(email, TYPE_LOGIN, code, null);

        emailService.sendVerificationEmail(email, "Family Robot - Login Verification Code", "Your login verification code is:", code);
        log.info("Login code sent to {}", email);
    }

    public User verifyLoginCode(String email, String code) {
        findAndValidate(email, TYPE_LOGIN, code);
        return userRepository.findByEmail(email).orElseThrow();
    }

    // ---- Reset password ----

    public void sendResetPasswordCode(String email) {
        userRepository.findByEmail(email)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "该邮箱未注册"));

        String code = newCode();
        saveCode(email, TYPE_RESET_PASSWORD, code, null);

        emailService.sendVerificationEmail(email, "Family Robot - Reset Password", "Your password reset code is:", code);
        log.info("Reset password code sent to {}", email);
    }

    public void resetPassword(String email, String code, String newPassword) {
        findAndValidate(email, TYPE_RESET_PASSWORD, code);

        User user = userRepository.findByEmail(email).orElseThrow();
        user.setPassword(passwordEncoder.encode(newPassword));
        userRepository.save(user);
        log.info("Password reset for {}", email);
    }

    @Scheduled(fixedRate = 300_000)
    @Transactional
    public void cleanExpired() {
        codeRepository.deleteByExpiresAtBefore(LocalDateTime.now());
    }
}
