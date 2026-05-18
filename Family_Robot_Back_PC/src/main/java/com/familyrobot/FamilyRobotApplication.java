package com.familyrobot;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class FamilyRobotApplication {

    public static void main(String[] args) {
        SpringApplication.run(FamilyRobotApplication.class, args);
    }
}
