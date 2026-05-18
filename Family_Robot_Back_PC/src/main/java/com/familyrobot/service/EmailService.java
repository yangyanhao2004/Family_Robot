package com.familyrobot.service;

import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

@Slf4j
@Service
@RequiredArgsConstructor
public class EmailService {

    private static final String FROM = "yangyanhao2004@qq.com";
    private static final String TEMPLATE = """
            <div style="font-family: Arial, sans-serif; max-width: 400px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Family Robot</h2>
                <p>%s</p>
                <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; text-align: center; margin: 16px 0;">
                    <span style="font-size: 28px; font-weight: bold; letter-spacing: 8px; color: #1f2937;">%s</span>
                </div>
                <p style="color: #6b7280; font-size: 13px;">%s</p>
            </div>
            """;

    private final JavaMailSender mailSender;

    public void sendVerificationEmail(String to, String subject, String label, String code) {
        String footer = "This code expires in 5 minutes. If you did not request this, please ignore this email.";
        sendHtmlEmail(to, subject, String.format(TEMPLATE, label, code, footer));
    }

    public void sendReminderEmail(String to, String reminderText, String scheduledTime) {
        String body = String.format("""
                <div style="font-family: Arial, sans-serif; max-width: 400px; margin: 0 auto;">
                    <h2 style="color: #2563eb;">Family Robot - Reminder</h2>
                    <p>You asked me to remind you:</p>
                    <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; margin: 16px 0;">
                        <p style="font-size: 16px; color: #1f2937; margin: 0;">%s</p>
                    </div>
                    <p style="color: #6b7280; font-size: 13px;">Scheduled for: %s</p>
                    <p style="color: #6b7280; font-size: 12px;">- Your Family Robot Jarvis</p>
                </div>
                """, reminderText, scheduledTime);
        sendHtmlEmail(to, "Family Robot - Reminder: " + reminderText, body);
    }

    private void sendHtmlEmail(String to, String subject, String htmlBody) {
        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
            helper.setFrom(FROM);
            helper.setTo(to);
            helper.setSubject(subject);
            helper.setText(htmlBody, true);
            mailSender.send(message);
            log.info("Email sent to {}: {}", to, subject);
        } catch (MessagingException e) {
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR,
                    "Failed to send email: " + e.getMessage());
        }
    }
}
