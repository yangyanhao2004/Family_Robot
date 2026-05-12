package com.familyrobot.model.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class AddPhotoRequest {
    @NotBlank
    private String url;

    @NotBlank
    private String filename;
}
