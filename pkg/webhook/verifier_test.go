package webhook

import (
	"errors"
	"net/http"
	"testing"
	"time"
)

func TestVerifierAcceptsValidSignature(t *testing.T) {
	body := []byte(`{"id":"evt_1","type":"rule-hit.created","occurredAt":"2026-04-25T10:00:00Z","projectCode":"demo","data":{}}`)
	now := time.Unix(1777111200, 0)
	timestamp := "1777111200"

	header := http.Header{}
	header.Set(HeaderTimestamp, timestamp)
	header.Set(HeaderSignature, ComputeSignature("secret", timestamp, body))

	err := Verifier{
		Secret: "secret",
		Now:    func() time.Time { return now },
	}.Verify(header, body)
	if err != nil {
		t.Fatal(err)
	}
}

func TestVerifierRejectsInvalidSignature(t *testing.T) {
	body := []byte(`{"id":"evt_1"}`)
	now := time.Unix(1777111200, 0)

	header := http.Header{}
	header.Set(HeaderTimestamp, "1777111200")
	header.Set(HeaderSignature, "sha256=bad")

	err := Verifier{
		Secret: "secret",
		Now:    func() time.Time { return now },
	}.Verify(header, body)
	if !errors.Is(err, ErrInvalidSignature) {
		t.Fatalf("expected ErrInvalidSignature, got %v", err)
	}
}
