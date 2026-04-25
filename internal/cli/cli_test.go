package cli

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/lingmind/annex/pkg/annex"
)

func TestDevicesListCommand(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/devices" {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		if got := r.Header.Get("Authorization"); got != "Bearer token_123" {
			t.Fatalf("unexpected authorization header: %s", got)
		}
		if got := r.Header.Get("X-LM-Project-Code"); got != "demo" {
			t.Fatalf("unexpected project header: %s", got)
		}
		if got := r.URL.Query().Get("state"); got != "online" {
			t.Fatalf("unexpected state query: %s", got)
		}

		_ = json.NewEncoder(w).Encode(annex.ListResponse[annex.Device]{
			Data: []annex.Device{{ID: "dev_1", Name: "Camera 1", Type: "camera", State: "online", ProjectCode: "demo", Online: true}},
			Page: annex.PageInfo{Page: 1, PageSize: 50},
		})
	}))
	defer server.Close()

	var stdout, stderr bytes.Buffer
	cmd := Command{
		Stdout: &stdout,
		Stderr: &stderr,
		Env: func(key string) string {
			return ""
		},
	}

	code := cmd.Run(t.Context(), []string{
		"lm",
		"--base-url", server.URL,
		"--token", "token_123",
		"--project", "demo",
		"--format", "json",
		"devices", "list",
		"--state", "online",
	})
	if code != 0 {
		t.Fatalf("unexpected exit code %d, stderr: %s", code, stderr.String())
	}

	if !strings.Contains(stdout.String(), `"id": "dev_1"`) {
		t.Fatalf("unexpected stdout: %s", stdout.String())
	}
}
