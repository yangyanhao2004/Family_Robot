package com.familyrobot.repository;

import com.familyrobot.model.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);

    List<User> findAllByRoleNot(String role);

    @Query("SELECT DISTINCT u FROM User u LEFT JOIN Robot r ON r.user.id = u.id WHERE " +
           "u.role <> 'Admin' AND " +
           "(:search IS NULL OR :search = '' OR LOWER(u.name) LIKE LOWER(CONCAT('%', :search, '%')) OR LOWER(u.email) LIKE LOWER(CONCAT('%', :search, '%')) OR LOWER(r.serialNumber) LIKE LOWER(CONCAT('%', :search, '%')))")
    List<User> findFilteredUsers(@Param("search") String search);
}
