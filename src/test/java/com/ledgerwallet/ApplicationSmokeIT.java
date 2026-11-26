package com.ledgerwallet;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.context.annotation.Import;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.test.web.servlet.assertj.MockMvcTester;

/**
 * Boots the whole application against an isolated PostgreSQL container and checks that the database
 * and the read-only health endpoint (used by the local-check skill) are working.
 */
@SpringBootTest
@AutoConfigureMockMvc
@Import(TestcontainersConfiguration.class)
class ApplicationSmokeIT {

  @Autowired JdbcClient jdbc;

  @Autowired MockMvcTester mvc;

  @Test
  void connectsToPostgres() {
    String version = jdbc.sql("select version()").query(String.class).single();

    assertThat(version).startsWith("PostgreSQL");
  }

  @Test
  void healthEndpointReportsUp() {
    assertThat(mvc.get().uri("/actuator/health"))
        .hasStatusOk()
        .bodyJson()
        .extractingPath("$.status")
        .isEqualTo("UP");
  }
}
