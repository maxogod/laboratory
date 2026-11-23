package main

import (
	"go_websockets/internal/app"
	"go_websockets/internal/config"
	"log"
	"os"
	"os/signal"
	"syscall"
)

// @title			Discordia Chat Service API
// @version		1.0
// @description	REST and WebSocket API for the Discordia chat service.
// @BasePath		/
func main() {
	config, err := config.LoadConfig()
	if err != nil {
		log.Fatalf("There was an error loading the configuration: %v", err)
	}

	app, err := app.NewApp(config)
	if err != nil {
		log.Fatalf("There was an error creating the app: %v", err)
	}

	signalChannel := make(chan os.Signal, 1)
	signal.Notify(signalChannel, syscall.SIGTERM, syscall.SIGINT)

	// server.Shutdown (called from within app.Shutdown) makes the blocking
	// app.Start call below return as soon as the listener closes, well
	// before Shutdown itself has finished draining the DB connection and
	// websocket clients. shutdownDone lets main wait for that cleanup to
	// actually finish instead of exiting the process out from under it.
	shutdownDone := make(chan struct{})
	go func() {
		defer close(shutdownDone)

		<-signalChannel

		if err := app.Shutdown(); err != nil {
			log.Printf("There was an error shutting down the server: %v", err)
		}
	}()

	if err := app.Start(); err != nil {
		log.Fatalf("There was an error running the server: %v", err)
	}

	<-shutdownDone
}
