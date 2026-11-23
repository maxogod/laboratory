package com.testing.test.controllers;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HelloController {

    private static final String template = "Hello, %s!";

    @GetMapping("/{personName}")
    public ResponseEntity<String> hello(@PathVariable String personName) {
        return ResponseEntity.ok(String.format(template, personName));
    }
}
