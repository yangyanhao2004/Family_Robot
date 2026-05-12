package com.familyrobot.controller;

import com.familyrobot.model.dto.AddPhotoRequest;
import com.familyrobot.model.dto.PhotoDto;
import com.familyrobot.model.entity.User;
import com.familyrobot.service.AlbumService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/albums")
@RequiredArgsConstructor
public class AlbumController {

    private final AlbumService albumService;

    @GetMapping
    public ResponseEntity<List<PhotoDto>> getPhotos(@AuthenticationPrincipal User user) {
        return ResponseEntity.ok(albumService.getPhotos(user.getId()));
    }

    @PostMapping
    public ResponseEntity<Map<String, String>> addPhoto(@Valid @RequestBody AddPhotoRequest request,
                                                         @AuthenticationPrincipal User user) {
        albumService.addPhoto(user, request.getUrl(), request.getFilename());
        return ResponseEntity.ok(Map.of("message", "ok"));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Map<String, String>> deletePhoto(@PathVariable Long id,
                                                           @AuthenticationPrincipal User user) {
        albumService.deletePhoto(id, user.getId());
        return ResponseEntity.ok(Map.of("message", "ok"));
    }
}
