package com.familyrobot.service;

import com.familyrobot.model.entity.Robot;
import com.familyrobot.model.entity.User;
import com.familyrobot.model.entity.VerificationCode;
import com.familyrobot.repository.RobotRepository;
import com.familyrobot.repository.UserRepository;
import com.familyrobot.repository.VerificationCodeRepository;
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

    private final JavaMailSender mailSender;
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

        sendEmail(email, "Family Robot - Email Verification Code", "Your verification code is:", code);
        log.info("Verification code sent to {}", email);
    }

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

        sendEmail(email, "Family Robot - Login Verification Code", "Your login verification code is:", code);
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

        sendEmail(email, "Family Robot - Reset Password", "Your password reset code is:", code);
        log.info("Reset password code sent to {}", email);
    }

    public void resetPassword(String email, String code, String newPassword) {
        findAndValidate(email, TYPE_RESET_PASSWORD, code);

        User user = userRepository.findByEmail(email).orElseThrow();
        user.setPassword(passwordEncoder.encode(newPassword));
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
    @Transactional
    public void cleanExpired() {
        codeRepository.deleteByExpiresAtBefore(LocalDateTime.now());
    }
}
