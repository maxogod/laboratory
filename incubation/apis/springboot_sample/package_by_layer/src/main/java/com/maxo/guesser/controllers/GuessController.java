package com.maxo.guesser.controllers;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.http.ResponseEntity;
import com.maxo.guesser.services.GuessService;
import org.springframework.beans.factory.annotation.Autowired;

@RestController
public class GuessController {

    @Autowired
    private final GuessService guessService;

    public GuessController(GuessService guessService) {
        this.guessService = guessService;
    }

    @GetMapping("/guess/{user_guess}")
    public ResponseEntity<String> guess(@PathVariable String user_guess) {

        if (user_guess == null) {
            return ResponseEntity.badRequest().body("You must provide a guess!");
        }

        if (guessService.guess(user_guess)) {
            return ResponseEntity.ok("You guessed it!");
        } else {
            return ResponseEntity.ok("Try again!");
        }
    }
}
