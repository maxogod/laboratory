package com.maxo.guesser.services;

import com.maxo.guesser.repositories.GuessRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.Optional;

@Service
public class GuessService {
    
    @Autowired
    private final GuessRepository guessRepository;

    public GuessService(GuessRepository guessRepository) {
        this.guessRepository = guessRepository;
    }

    public boolean guess(String user_guess) {
        if (user_guess.equals(guessRepository.getSecret())) {
            return true;
        } else {
            return false;
        }
    }
}

