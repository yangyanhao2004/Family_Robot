package com.familyrobot.controller;

import com.familyrobot.model.dto.CreateReminderRequest;
import com.familyrobot.model.dto.ReminderDto;
import com.familyrobot.model.dto.UpdateReminderRequest;
import com.familyrobot.model.entity.User;
import com.familyrobot.service.ReminderService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/reminders")
@RequiredArgsConstructor
public class ReminderController {

    private final ReminderService reminderService;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ReminderDto create(@RequestBody CreateReminderRequest req) {
        return reminderService.createReminder(req);
    }

    @PutMapping("/{id}")
    public Map<String, String> update(@PathVariable Long id,
                                       @RequestBody UpdateReminderRequest req,
                                       @AuthenticationPrincipal User user) {
        reminderService.updateReminder(id, req, user.getId());
        return Map.of("message", "Reminder updated");
    }

    @GetMapping
    public List<ReminderDto> list(@RequestParam Long userId) {
        return reminderService.getUserReminders(userId);
    }

    @DeleteMapping("/{id}")
    public Map<String, String> delete(@PathVariable Long id,
                                       @AuthenticationPrincipal User user) {
        reminderService.deleteReminder(id, user.getId());
        return Map.of("message", "Reminder deleted");
    }
}
