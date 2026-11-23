package com.maxo.guesser.repositories;

import org.springframework.stereotype.Repository;

@Repository
public class GuessRepository {
    
    private final String secret = "pokemon!";

    public String getSecret() {
        return secret;
    }
}
