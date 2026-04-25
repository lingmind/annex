package webhook

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"log/slog"
	"net/http"
	"strings"
	"time"
)

type Server struct {
	Secret  string
	Path    string
	MaxSkew time.Duration
	Handler Handler
	Logger  *slog.Logger
	Now     func() time.Time
}

func (s Server) HandlerFunc() http.Handler {
	path := s.Path
	if path == "" {
		path = "/lingmind/webhook"
	}

	mux := http.NewServeMux()
	mux.HandleFunc(path, s.handle)
	return mux
}

func (s Server) handle(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		w.Header().Set("Allow", http.MethodPost)
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	body, err := io.ReadAll(io.LimitReader(r.Body, 10<<20))
	if err != nil {
		http.Error(w, "read body", http.StatusBadRequest)
		return
	}

	if s.Secret != "" {
		verifier := Verifier{Secret: s.Secret, MaxSkew: s.MaxSkew, Now: s.Now}
		if err := verifier.Verify(r.Header, body); err != nil {
			http.Error(w, "invalid signature", http.StatusUnauthorized)
			s.logWarn("webhook signature rejected", "error", err)
			return
		}
	}

	var event Event
	if err := json.Unmarshal(body, &event); err != nil {
		http.Error(w, "invalid event body", http.StatusBadRequest)
		return
	}
	if strings.TrimSpace(event.ID) == "" || strings.TrimSpace(event.Type) == "" {
		http.Error(w, "event id and type are required", http.StatusBadRequest)
		return
	}

	if s.Handler != nil {
		if err := s.Handler.HandleAnnexEvent(event); err != nil {
			status := http.StatusInternalServerError
			if errors.Is(err, context.Canceled) {
				status = http.StatusServiceUnavailable
			}
			http.Error(w, "handle event", status)
			s.logWarn("webhook handler failed", "event_id", event.ID, "event_type", event.Type, "error", err)
			return
		}
	}

	w.WriteHeader(http.StatusNoContent)
}

func (s Server) logWarn(msg string, args ...any) {
	if s.Logger != nil {
		s.Logger.Warn(msg, args...)
	}
}
