package com.familyrobot.service;

import com.familyrobot.model.dto.PhotoDto;
import com.familyrobot.model.entity.Photo;
import com.familyrobot.model.entity.User;
import com.familyrobot.repository.PhotoRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@Service
@RequiredArgsConstructor
public class AlbumService {

    private final PhotoRepository photoRepository;

    public List<PhotoDto> getPhotos(Long userId) {
        return photoRepository.findByUserIdOrderByDateDesc(userId)
                .stream()
                .map(this::toDto)
                .toList();
    }

    public void addPhoto(User user, String url, String filename) {
        Photo photo = Photo.builder()
                .url(url)
                .filename(filename)
                .user(user)
                .build();
        photoRepository.save(photo);
    }

    public void deletePhoto(Long photoId, Long userId) {
        Photo photo = photoRepository.findById(photoId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Photo not found"));
        if (!photo.getUser().getId().equals(userId)) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Not authorized to delete this photo");
        }
        photoRepository.delete(photo);
    }

    private PhotoDto toDto(Photo photo) {
        return PhotoDto.builder()
                .id(String.valueOf(photo.getId()))
                .url(photo.getUrl())
                .date(photo.getDate().toString())
                .build();
    }
}
