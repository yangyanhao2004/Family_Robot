package com.familyrobot.scheduled;

import com.familyrobot.repository.CommandLogRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

@Slf4j
@Component
@EnableScheduling
@RequiredArgsConstructor
public class ScheduledTasks {

    private final CommandLogRepository commandLogRepository;

    @Scheduled(cron = "0 0 * * * *")
    public void reportHourlyStats() {
        long count = commandLogRepository.countByTimestampAfter(LocalDateTime.now().minusHours(1));
        log.info("[Scheduled] Hourly command stats: {} commands in last hour", count);
    }

    @Scheduled(cron = "0 0 3 * * *")
    @Transactional
    public void cleanupOldLogs() {
        LocalDateTime cutoff = LocalDateTime.now().minusDays(30);
        commandLogRepository.deleteByTimestampBefore(cutoff);
        log.info("[Scheduled] Daily cleanup: deleted command logs older than 30 days");
    }
}
