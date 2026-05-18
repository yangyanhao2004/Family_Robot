package com.familyrobot.service;

import com.familyrobot.model.dto.CreateReminderRequest;
import com.familyrobot.model.dto.ReminderDto;
import com.familyrobot.model.dto.UpdateReminderRequest;
import com.familyrobot.model.entity.Reminder;
import com.familyrobot.repository.ReminderRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

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
@RequiredArgsConstructor
public class ReminderService {

    private final ReminderRepository reminderRepository;
    private final EmailService emailService;

    public ReminderDto createReminder(CreateReminderRequest req) {
        if (!"EMAIL".equals(req.getMethod()) && !"VOICE".equals(req.getMethod())) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "method must be EMAIL or VOICE");
        }
        if ("EMAIL".equals(req.getMethod()) && (req.getEmail() == null || req.getEmail().isBlank())) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "email is required for EMAIL method");
        }

        LocalDateTime scheduledTime = LocalDateTime.parse(req.getScheduledTime(),
                DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss"));

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
            reminder.setScheduledTime(LocalDateTime.parse(req.getScheduledTime(),
                    DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss")));
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

    private void sendVoiceReminder(Reminder r) {
        String pythonBackend = System.getenv().getOrDefault("PYTHON_BACKEND_URL", "http://localhost:8080");
        HttpClient client = HttpClient.newHttpClient();
        try {
            String body = String.format("{\"reminderId\":%d,\"text\":\"%s\",\"userId\":%d}",
                    r.getId(), r.getText(), r.getUserId());
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(pythonBackend + "/internal/voice-reminder"))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(body))
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
