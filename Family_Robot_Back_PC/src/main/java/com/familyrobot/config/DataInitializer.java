package com.familyrobot.config;

import com.familyrobot.model.entity.User;
import com.familyrobot.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    public void run(String... args) {
        if (userRepository.findByEmail("admin@family-robot.local").isEmpty()) {
            User admin = User.builder()
                    .email("admin@family-robot.local")
                    .password(passwordEncoder.encode("admin123"))
                    .name("Admin")
                    .role("Admin")
                    .build();
            userRepository.save(admin);
            log.info("Admin user seeded");
        }
    }
}
