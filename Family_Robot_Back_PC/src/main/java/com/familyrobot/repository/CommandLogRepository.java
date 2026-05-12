package com.familyrobot.repository;

import com.familyrobot.model.entity.CommandLog;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDateTime;

public interface CommandLogRepository extends JpaRepository<CommandLog, Long> {

    long countByTimestampAfter(LocalDateTime after);

    void deleteByTimestampBefore(LocalDateTime timestamp);
}
