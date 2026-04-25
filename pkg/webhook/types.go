package webhook

import (
	"encoding/json"
	"time"
)

type Event struct {
	ID          string          `json:"id"`
	Type        string          `json:"type"`
	OccurredAt  time.Time       `json:"occurredAt"`
	ProjectCode string          `json:"projectCode"`
	Data        json.RawMessage `json:"data"`
}

type Handler interface {
	HandleAnnexEvent(event Event) error
}

type HandlerFunc func(event Event) error

func (fn HandlerFunc) HandleAnnexEvent(event Event) error {
	return fn(event)
}
