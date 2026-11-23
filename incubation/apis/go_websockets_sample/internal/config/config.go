package config

import (
	"errors"
	"os"
	"strconv"
)

type EnvironmentType int

const (
	Development EnvironmentType = iota
	Production
)

type Config struct {
	Port        int
	Host        string
	Environment EnvironmentType

	DatabaseURL string

	WSMaxConnections           int
	WSMaxConnectionsPerChannel int
}

func LoadConfig() (*Config, error) {
	port, err := strconv.Atoi(getEnvOrDefault("PORT", "8080"))
	if err != nil {
		return nil, err
	}

	databaseURL := os.Getenv("DATABASE_URL")
	if databaseURL == "" {
		return nil, errors.New("DATABASE_URL environment variable is required")
	}

	wsMaxConnections, err := strconv.Atoi(getEnvOrDefault("WS_MAX_CONNECTIONS", "10000"))
	if err != nil {
		return nil, err
	}

	wsMaxConnectionsPerChannel, err := strconv.Atoi(getEnvOrDefault("WS_MAX_CONNECTIONS_PER_CHANNEL", "1000"))
	if err != nil {
		return nil, err
	}

	var environment EnvironmentType
	switch os.Getenv("ENVIRONMENT") {
	case "development":
		environment = Development
	default:
		environment = Production
	}

	return &Config{
		Port:        port,
		Host:        getEnvOrDefault("HOST", "0.0.0.0"),
		Environment: environment,

		DatabaseURL: databaseURL,

		WSMaxConnections:           wsMaxConnections,
		WSMaxConnectionsPerChannel: wsMaxConnectionsPerChannel,
	}, nil
}

func getEnvOrDefault(key string, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}
