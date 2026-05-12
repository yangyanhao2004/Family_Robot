package com.familyrobot.repository;

import com.familyrobot.model.entity.Robot;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface RobotRepository extends JpaRepository<Robot, Long> {

    Optional<Robot> findBySerialNumber(String serialNumber);

    List<Robot> findByUserId(Long userId);
}
