package com.familyrobot.repository;

import com.familyrobot.model.entity.Robot;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

public interface RobotRepository extends JpaRepository<Robot, Long> {

    Optional<Robot> findBySerialNumber(String serialNumber);

    @Query("SELECT r FROM Robot r LEFT JOIN r.user u WHERE " +
           "(:search IS NULL OR :search = '' OR LOWER(r.serialNumber) LIKE LOWER(CONCAT('%', :search, '%')) OR LOWER(u.email) LIKE LOWER(CONCAT('%', :search, '%'))) " +
           "AND (:start IS NULL OR r.createdAt >= :start) " +
           "AND (:end IS NULL OR r.createdAt <= :end)")
    List<Robot> findFilteredRobots(@Param("search") String search,
                                   @Param("start") LocalDateTime start,
                                   @Param("end") LocalDateTime end);
}
