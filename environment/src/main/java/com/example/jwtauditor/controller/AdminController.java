package com.example.jwtauditor.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/admin")
public class AdminController {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @GetMapping("/clients")
    public List<Map<String, Object>> getClients() {
        String sql = "SELECT c.client_id, c.client_name, c.redirect_uri, c.status AS client_status, " +
                     "k.key_id, k.key_type, k.status AS key_status " +
                     "FROM registered_clients c " +
                     "LEFT JOIN signing_keys k ON c.client_id = k.client_id";
        return jdbcTemplate.queryForList(sql);
    }
}
