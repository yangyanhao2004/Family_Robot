package com.familyrobot.model.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * Records every robot command for analytics and auditing.
 * Java's scheduling layer can aggregate this into daily reports.
 */
@Entity
@Table(name = "command_logs")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CommandLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 30)
    private String command;

    @Column(length = 20)
    private String source; // "web", "voice", "auto"

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    @Column(nullable = false)
    @Builder.Default
    private LocalDateTime timestamp = LocalDateTime.now();
}
