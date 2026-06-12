package com.familyrobot.service;

import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

@Slf4j
@Service
public class EmailService {

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
    private final String from;

    public EmailService(JavaMailSender mailSender,
                        @Value("${spring.mail.username}") String from) {
        this.mailSender = mailSender;
        this.from = from;
    }

    public void sendVerificationEmail(String to, String subject, String label, String code) {
        String footer = "This code expires in 5 minutes. If you did not request this, please ignore this email.";
        sendHtmlEmail(to, subject, String.format(TEMPLATE, label, code, footer));
    }

    public void sendEmergencyEmail(String to, String userName, String time, String contactName) {
        String body = String.format("""
                <div style="font-family: Arial, sans-serif; max-width: 400px; margin: 0 auto;">
                    <div style="background: #dc2626; padding: 16px; border-radius: 12px 12px 0 0;">
                        <h1 style="color: white; margin: 0; font-size: 20px;">⚠️ 紧急摔倒告警</h1>
                    </div>
                    <div style="background: #fef2f2; padding: 20px; border: 1px solid #fecaca; border-radius: 0 0 12px 12px;">
                        <p style="font-size: 16px; color: #991b1b; margin: 0 0 12px;">Family Robot 检测到 %s 可能发生摔倒事件。</p>
                        <p style="color: #7f1d1d;">检测时间：%s</p>
                        <p style="color: #7f1d1d;">紧急联系人：%s</p>
                        <hr style="border-color: #fecaca; margin: 16px 0;">
                        <p style="color: #991b1b; font-weight: bold;">请尽快联系确认安全！</p>
                        <p style="color: #6b7280; font-size: 12px; margin-top: 16px;">此邮件由 Family Robot 自动发送</p>
                    </div>
                </div>
                """, userName, time, contactName);
        sendHtmlEmail(to, "⚠️ 紧急告警 — Family Robot 检测到摔倒事件", body);
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
            helper.setFrom(from);
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
