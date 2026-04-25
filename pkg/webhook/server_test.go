package webhook

import (
	"bytes"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestServerVerifiesSignatureAndDispatchesEvent(t *testing.T) {
	body := []byte(`{"id":"evt_1","type":"rule-hit.created","occurredAt":"2026-04-25T10:00:00Z","projectCode":"demo","data":{"id":"hit_1"}}`)
	timestamp := "1777111200"
	var received Event

	server := Server{
		Secret: "secret",
		Now:    func() time.Time { return time.Unix(1777111200, 0) },
		Handler: HandlerFunc(func(event Event) error {
			received = event
			return nil
		}),
	}

	req := httptest.NewRequest(http.MethodPost, "/lingmind/webhook", bytes.NewReader(body))
	req.Header.Set(HeaderTimestamp, timestamp)
	req.Header.Set(HeaderSignature, ComputeSignature("secret", timestamp, body))
	recorder := httptest.NewRecorder()

	server.HandlerFunc().ServeHTTP(recorder, req)

	if recorder.Code != http.StatusNoContent {
		t.Fatalf("unexpected status: %d body: %s", recorder.Code, recorder.Body.String())
	}
	if received.ID != "evt_1" || received.Type != "rule-hit.created" {
		t.Fatalf("unexpected event: %#v", received)
	}
}
