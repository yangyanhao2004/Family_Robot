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
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
public class ReminderService {

    private final ReminderRepository reminderRepository;
    private final EmailService emailService;
    private final String pythonBackendUrl;

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

        LocalDateTime scheduledTime = parseReminderDateTime(req.getScheduledTime());

        Reminder reminder = Reminder.builder()
                .userId(req.getUserId())
                .text(req.getText())
                .scheduledTime(scheduledTime)
                .method(req.getMethod())
                .email(req.getEmail())
                .enabled(true)
                .sent(false)
                .createdAt(LocalDateTime.now())
                .build();

        reminder = reminderRepository.save(reminder);
        log.info("Reminder #{} created: {} ({}) for user {}", reminder.getId(),
                reminder.getText(), reminder.getMethod(), reminder.getUserId());
        return toDto(reminder);
    }

    public ReminderDto updateReminder(Long id, UpdateReminderRequest req) {
        Reminder reminder = reminderRepository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Reminder not found"));

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

    public void deleteReminder(Long id) {
        if (!reminderRepository.existsById(id)) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Reminder not found");
        }
        reminderRepository.deleteById(id);
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
