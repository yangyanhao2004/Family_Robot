package com.familyrobot.service;

import com.familyrobot.model.entity.Robot;
import com.familyrobot.model.entity.User;
import com.familyrobot.repository.RobotRepository;
import com.familyrobot.repository.UserRepository;
import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.util.Random;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Service
@RequiredArgsConstructor
public class VerificationService {

    private final JavaMailSender mailSender;
    private final UserRepository userRepository;
    private final RobotRepository robotRepository;
    private final PasswordEncoder passwordEncoder;

    private final ConcurrentHashMap<String, PendingRegistration> pending = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, LoginCode> loginCodes = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, LoginCode> resetCodes = new ConcurrentHashMap<>();
    private final Random random = new Random();

    private record PendingRegistration(String passwordHash, String serialNumber, String code, LocalDateTime expiresAt) {}
    private record LoginCode(String code, LocalDateTime expiresAt) {}

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

        String code = String.format("%06d", random.nextInt(1000000));
        pending.put(email, new PendingRegistration(
                passwordEncoder.encode(password),
                serialNumber,
                code,
                LocalDateTime.now().plusMinutes(5)
        ));

        sendEmail(email, "Family Robot - Email Verification Code", "Your verification code is:", code);
        log.info("Verification code sent to {}", email);
    }

    public void verify(String email, String code) {
        PendingRegistration entry = pending.get(email);
        if (entry == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "No pending registration or code expired");
        }
        if (entry.expiresAt.isBefore(LocalDateTime.now())) {
            pending.remove(email);
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Verification code expired");
        }
        if (!entry.code.equals(code)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid verification code");
        }

        pending.remove(email);

        User user = User.builder()
                .email(email)
                .passwordHash(entry.passwordHash)
                .name(email.split("@")[0])
                .role("User")
                .build();
        userRepository.save(user);

        Robot robot = robotRepository.findBySerialNumber(entry.serialNumber).orElseThrow();
        robot.setUser(user);
        robotRepository.save(robot);

        log.info("User registered: {} with robot {}", email, entry.serialNumber);
    }

    // ---- Login with code ----

    public void sendLoginCode(String email) {
        userRepository.findByEmail(email)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "该邮箱未注册，请先注册账户"));

        String code = String.format("%06d", random.nextInt(1000000));
        loginCodes.put(email, new LoginCode(code, LocalDateTime.now().plusMinutes(5)));

        sendEmail(email, "Family Robot - Login Verification Code", "Your login verification code is:", code);
        log.info("Login code sent to {}", email);
    }

    public User verifyLoginCode(String email, String code) {
        LoginCode entry = loginCodes.get(email);
        if (entry == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "No pending login code or code expired");
        }
        if (entry.expiresAt.isBefore(LocalDateTime.now())) {
            loginCodes.remove(email);
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Verification code expired");
        }
        if (!entry.code.equals(code)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid verification code");
        }

        loginCodes.remove(email);
        return userRepository.findByEmail(email).orElseThrow();
    }

    // ---- Reset password ----

    public void sendResetPasswordCode(String email) {
        userRepository.findByEmail(email)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "该邮箱未注册"));

        String code = String.format("%06d", random.nextInt(1000000));
        resetCodes.put(email, new LoginCode(code, LocalDateTime.now().plusMinutes(5)));

        sendEmail(email, "Family Robot - Reset Password", "Your password reset code is:", code);
        log.info("Reset password code sent to {}", email);
    }

    public void resetPassword(String email, String code, String newPassword) {
        LoginCode entry = resetCodes.get(email);
        if (entry == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "No pending reset request or code expired");
        }
        if (entry.expiresAt.isBefore(LocalDateTime.now())) {
            resetCodes.remove(email);
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Verification code expired");
        }
        if (!entry.code.equals(code)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid verification code");
        }

        resetCodes.remove(email);

        User user = userRepository.findByEmail(email).orElseThrow();
        user.setPasswordHash(passwordEncoder.encode(newPassword));
        userRepository.save(user);
        log.info("Password reset for {}", email);
    }

    // ---- Shared ----

    private void sendEmail(String to, String subject, String label, String code) {
        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
            helper.setFrom("yangyanhao2004@qq.com");
            helper.setTo(to);
            helper.setSubject(subject);
            helper.setText(String.format("""
                    <div style="font-family: Arial, sans-serif; max-width: 400px; margin: 0 auto;">
                        <h2 style="color: #2563eb;">Family Robot</h2>
                        <p>%s</p>
                        <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; text-align: center; margin: 16px 0;">
                            <span style="font-size: 28px; font-weight: bold; letter-spacing: 8px; color: #1f2937;">%s</span>
                        </div>
                        <p style="color: #6b7280; font-size: 13px;">This code expires in 5 minutes. If you did not request this, please ignore this email.</p>
                    </div>
                    """, label, code), true);
            mailSender.send(message);
        } catch (MessagingException e) {
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Failed to send email: " + e.getMessage());
        }
    }

    @Scheduled(fixedRate = 300_000)
    public void cleanExpired() {
        pending.entrySet().removeIf(e -> e.getValue().expiresAt.isBefore(LocalDateTime.now()));
        loginCodes.entrySet().removeIf(e -> e.getValue().expiresAt.isBefore(LocalDateTime.now()));
        resetCodes.entrySet().removeIf(e -> e.getValue().expiresAt.isBefore(LocalDateTime.now()));
    }
}
