package com.familyrobot.repository;

import com.familyrobot.model.entity.VerificationCode;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDateTime;
import java.util.Optional;

public interface VerificationCodeRepository extends JpaRepository<VerificationCode, Long> {

    Optional<VerificationCode> findTopByEmailAndTypeAndUsedFalseAndExpiresAtAfterOrderByExpiresAtDesc(
            String email, String type, LocalDateTime now);

    void deleteByExpiresAtBefore(LocalDateTime now);
    void deleteAllByEmail(String email);
}
