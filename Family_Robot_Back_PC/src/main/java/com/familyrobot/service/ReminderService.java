package com.familyrobot.service;

import com.familyrobot.model.dto.CreateReminderRequest;
import com.familyrobot.model.dto.ReminderDto;
import com.familyrobot.model.dto.UpdateReminderRequest;
import com.familyrobot.model.entity.Reminder;
import com.familyrobot.repository.ReminderRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

@Slf4j
@Service
public class ReminderService {

    private final ReminderRepository reminderRepository;
    private final EmailService emailService;
    private final String pythonBackendUrl;

    @Value("${app.moonshot-api-key:}")
    private String moonshotApiKey;

    private static final Pattern CHINESE_PATTERN = Pattern.compile("[\\u4e00-\\u9fff]");

    public ReminderService(ReminderRepository reminderRepository,
                           EmailService emailService,
                           @Value("${app.python-backend-url:http://localhost:8080}") String pythonBackendUrl) {
        this.reminderRepository = reminderRepository;
        this.emailService = emailService;
        this.pythonBackendUrl = pythonBackendUrl;
    }

    public ReminderDto createReminder(CreateReminderRequest req) {
        if (!"EMAIL".equals(req.getMethod()) && !"VOICE".equals(req.getMethod())) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "method must be EMAIL or VOICE");
        }
        if ("EMAIL".equals(req.getMethod()) && (req.getEmail() == null || req.getEmail().isBlank())) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "email is required for EMAIL method");
        }
        if (req.getText() == null || req.getText().isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "reminder text is required");
        }

        LocalDateTime scheduledTime = parseReminderDateTime(req.getScheduledTime());
        if (scheduledTime.isBefore(LocalDateTime.now().minusSeconds(60))) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "scheduledTime must be in the future");
        }

        // Translate Chinese VOICE reminders to English for Piper TTS compatibility
        String text = req.getText();
        if ("VOICE".equals(req.getMethod()) && CHINESE_PATTERN.matcher(text).find()) {
            text = translateToEnglish(text);
        }

        // Send immediately if the scheduled time is already past or very close,
        // otherwise let the per-minute scheduler pick it up
        boolean sendNow = !scheduledTime.isAfter(LocalDateTime.now().plusSeconds(10));

        Reminder reminder = Reminder.builder()
                .userId(req.getUserId())
                .text(text)
                .scheduledTime(scheduledTime)
                .method(req.getMethod())
                .email(req.getEmail())
                .enabled(true)
                .sent(sendNow)
                .createdAt(LocalDateTime.now())
                .build();

        reminder = reminderRepository.save(reminder);
        log.info("Reminder #{} created: {} ({}) for user {} {}",
                reminder.getId(), reminder.getText(), reminder.getMethod(),
                reminder.getUserId(), sendNow ? "[sent immediately]" : "[scheduled]");

        if (sendNow) {
            try {
                if ("EMAIL".equals(req.getMethod())) {
                    sendEmailReminder(reminder);
                } else if ("VOICE".equals(req.getMethod())) {
                    sendVoiceReminder(reminder);
                }
            } catch (Exception e) {
                log.error("Immediate send failed for reminder #{}: {}", reminder.getId(), e.getMessage());
                reminder.setSent(false);
                reminderRepository.save(reminder);
            }
        }

        return toDto(reminder);
    }

    public ReminderDto updateReminder(Long id, UpdateReminderRequest req, Long requestingUserId) {
        Reminder reminder = reminderRepository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Reminder not found"));

        if (!reminder.getUserId().equals(requestingUserId)) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Not authorized to edit this reminder");
        }

        if (req.getText() != null) reminder.setText(req.getText());
        if (req.getScheduledTime() != null) {
            LocalDateTime newTime = parseReminderDateTime(req.getScheduledTime());
            reminder.setScheduledTime(newTime);
            if (newTime.isAfter(LocalDateTime.now())) {
                reminder.setSent(false);
            }
        }
        if (req.getMethod() != null) reminder.setMethod(req.getMethod());
        if (req.getEmail() != null) reminder.setEmail(req.getEmail());
        if (req.getEnabled() != null) reminder.setEnabled(req.getEnabled());

        reminder = reminderRepository.save(reminder);
        log.info("Reminder #{} updated", id);
        return toDto(reminder);
    }

    public List<ReminderDto> getUserReminders(Long userId) {
        return reminderRepository.findByUserIdOrderByScheduledTimeDesc(userId)
                .stream().map(this::toDto).collect(Collectors.toList());
    }

    public void deleteReminder(Long id, Long requestingUserId) {
        Reminder reminder = reminderRepository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Reminder not found"));
        if (!reminder.getUserId().equals(requestingUserId)) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Not authorized to delete this reminder");
        }
        reminderRepository.delete(reminder);
        log.info("Reminder #{} deleted", id);
    }

    @Scheduled(cron = "0 * * * * *")
    @Transactional
    public void sendDueReminders() {
        LocalDateTime now = LocalDateTime.now();
        List<Reminder> due = reminderRepository
                .findByEnabledTrueAndSentFalseAndScheduledTimeBefore(now);

        for (Reminder r : due) {
            try {
                if ("EMAIL".equals(r.getMethod())) {
                    sendEmailReminder(r);
                } else if ("VOICE".equals(r.getMethod())) {
                    sendVoiceReminder(r);
                }
                r.setSent(true);
                reminderRepository.save(r);
                log.info("Reminder #{} sent via {}", r.getId(), r.getMethod());
            } catch (Exception e) {
                log.error("Failed to send reminder #{}: {}", r.getId(), e.getMessage());
            }
        }
    }

    private void sendEmailReminder(Reminder r) {
        String to = r.getEmail();
        if (to == null || to.isBlank()) {
            log.warn("Reminder #{} has EMAIL method but no email address", r.getId());
            return;
        }
        emailService.sendReminderEmail(to, r.getText(),
                r.getScheduledTime().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm")));
    }

    private static final ObjectMapper objectMapper = new ObjectMapper();

    private void sendVoiceReminder(Reminder r) {
        HttpClient client = HttpClient.newHttpClient();
        try {
            ObjectNode body = objectMapper.createObjectNode();
            body.put("reminderId", r.getId());
            body.put("text", r.getText());
            body.put("userId", r.getUserId());
            String json = objectMapper.writeValueAsString(body);
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(pythonBackendUrl + "/internal/voice-reminder"))
                    .header("Content-Type", "application/json; charset=utf-8")
                    .POST(HttpRequest.BodyPublishers.ofString(json))
                    .timeout(Duration.ofSeconds(10))
                    .build();
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() != 200) {
                log.error("Voice reminder #{} failed: HTTP {}", r.getId(), response.statusCode());
            }
        } catch (Exception e) {
            log.error("Voice reminder #{} failed: {}", r.getId(), e.getMessage());
            throw new RuntimeException(e);
        }
    }

    private static LocalDateTime parseReminderDateTime(String dt) {
        if (dt == null || dt.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "scheduledTime is required");
        }
        // Normalize: HTML datetime-local input omits seconds, append ":00" if missing
        if (dt.matches("\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}")) {
            dt = dt + ":00";
        }
        return LocalDateTime.parse(dt, DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss"));
    }

    private String translateToEnglish(String chineseText) {
        if (moonshotApiKey == null || moonshotApiKey.isBlank()) {
            log.warn("Moonshot API key not configured, storing original text for VOICE reminder");
            return chineseText;
        }
        try {
            ObjectNode body = objectMapper.createObjectNode();
            body.put("model", "moonshot-v1-8k");
            body.put("temperature", 0.3);

            var messages = body.putArray("messages");
            var sysMsg = messages.addObject();
            sysMsg.put("role", "system");
            sysMsg.put("content", "You are a translator. Translate the following Chinese text to English. "
                    + "Output ONLY the English translation, nothing else. Keep it concise and natural.");
            var userMsg = messages.addObject();
            userMsg.put("role", "user");
            userMsg.put("content", chineseText);

            String jsonBody = objectMapper.writeValueAsString(body);

            HttpClient client = HttpClient.newHttpClient();
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create("https://api.moonshot.cn/v1/chat/completions"))
                    .header("Content-Type", "application/json; charset=utf-8")
                    .header("Authorization", "Bearer " + moonshotApiKey)
                    .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
                    .timeout(Duration.ofSeconds(10))
                    .build();
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() == 200) {
                JsonNode root = objectMapper.readTree(response.body());
                String translated = root.path("choices").get(0).path("message").path("content").asText().trim();
                log.info("Translated VOICE reminder: '{}' -> '{}'", chineseText, translated);
                return translated;
            } else {
                log.error("Kimi translation API returned HTTP {}", response.statusCode());
                return chineseText;
            }
        } catch (Exception e) {
            log.error("Translation failed, using original text: {}", e.getMessage());
            return chineseText;
        }
    }

    @Scheduled(cron = "0 0 4 * * *")
    @Transactional
    public void cleanupOldReminders() {
        LocalDateTime cutoff = LocalDateTime.now().minusDays(30);
        reminderRepository.deleteByScheduledTimeBefore(cutoff);
        log.info("[Scheduled] Cleaned up reminders older than 30 days");
    }

    private ReminderDto toDto(Reminder r) {
        DateTimeFormatter fmt = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss");
        return ReminderDto.builder()
                .id(r.getId())
                .text(r.getText())
                .scheduledTime(r.getScheduledTime() != null ? r.getScheduledTime().format(fmt) : null)
                .method(r.getMethod())
                .email(r.getEmail())
                .enabled(r.getEnabled())
                .sent(r.getSent())
                .build();
    }
}
