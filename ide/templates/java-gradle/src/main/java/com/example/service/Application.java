package com.example.service;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class Application {
    @GetMapping("/status")
    public String status() {
        return "hello from your spring celaut service";
    }

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
