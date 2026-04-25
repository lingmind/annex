package main

import (
	"encoding/json"
	"log"
	"log/slog"
	"net/http"
	"os"

	"github.com/lingmind/annex/pkg/webhook"
)

func main() {
	secret := os.Getenv("LM_WEBHOOK_SECRET")
	if secret == "" {
		log.Fatal("LM_WEBHOOK_SECRET is required")
	}

	server := webhook.Server{
		Secret: secret,
		Logger: slog.Default(),
		Handler: webhook.HandlerFunc(func(event webhook.Event) error {
			payload, err := json.MarshalIndent(event, "", "  ")
			if err != nil {
				return err
			}
			log.Printf("received Annex event:\n%s", payload)
			return nil
		}),
	}

	log.Fatal(http.ListenAndServe(":8080", server.HandlerFunc()))
}
