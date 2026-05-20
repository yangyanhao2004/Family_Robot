package com.familyrobot.repository;

import com.familyrobot.model.entity.Reminder;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface ReminderRepository extends JpaRepository<Reminder, Long> {

    List<Reminder> findByEnabledTrueAndSentFalseAndScheduledTimeBefore(LocalDateTime now);

    List<Reminder> findByUserIdOrderByScheduledTimeDesc(Long userId);

    void deleteByScheduledTimeBefore(LocalDateTime cutoff);
    void deleteAllByUserId(Long userId);
}
