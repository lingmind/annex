package cli

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
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

func TestAuthLoginSavesConfig(t *testing.T) {
	home := t.TempDir()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Fatalf("unexpected method: %s", r.Method)
		}
		if r.URL.Path != "/auth/token" {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		var request annex.AuthTokenRequest
		if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
			t.Fatal(err)
		}
		if request.ClientID != "client_123" || request.ClientSecret != "secret_123" || request.ProjectCode != "demo" {
			t.Fatalf("unexpected auth request: %#v", request)
		}
		_ = json.NewEncoder(w).Encode(annex.AuthTokenResponse{
			AccessToken:  "access_123456",
			TokenType:    "Bearer",
			ExpiresIn:    3600,
			RefreshToken: "refresh_123456",
			ProjectCode:  "demo",
			Scope:        []string{"device:read"},
		})
	}))
	defer server.Close()

	var stdout, stderr bytes.Buffer
	cmd := Command{
		Stdout: &stdout,
		Stderr: &stderr,
		Env: func(key string) string {
			if key == "HOME" {
				return home
			}
			return ""
		},
	}

	code := cmd.Run(t.Context(), []string{
		"lm",
		"--base-url", server.URL,
		"auth", "login",
		"--client-id", "client_123",
		"--client-secret", "secret_123",
		"--project", "demo",
	})
	if code != 0 {
		t.Fatalf("unexpected exit code %d, stderr: %s", code, stderr.String())
	}
	if !strings.Contains(stdout.String(), "config") {
		t.Fatalf("expected config path in stdout, got: %s", stdout.String())
	}

	payload, err := os.ReadFile(filepath.Join(home, ".lm", "config.json"))
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(payload), `"token": "access_123456"`) {
		t.Fatalf("config did not store access token: %s", string(payload))
	}
	if !strings.Contains(string(payload), `"refreshToken": "refresh_123456"`) {
		t.Fatalf("config did not store refresh token: %s", string(payload))
	}
}

func TestAuthMeUsesSavedConfig(t *testing.T) {
	home := t.TempDir()
	configDir := filepath.Join(home, ".lm")
	if err := os.MkdirAll(configDir, 0o700); err != nil {
		t.Fatal(err)
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/auth/me" {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		if got := r.Header.Get("Authorization"); got != "Bearer access_123" {
			t.Fatalf("unexpected authorization header: %s", got)
		}
		_ = json.NewEncoder(w).Encode(annex.AuthSubject{
			ID:          "subject_1",
			Type:        "integration",
			Name:        "demo integration",
			ProjectCode: "demo",
			Scopes:      []string{"device:read"},
		})
	}))
	defer server.Close()

	config := storedConfig{
		BaseURL:     server.URL,
		Token:       "access_123",
		ProjectCode: "demo",
	}
	configFile, err := os.Create(filepath.Join(configDir, "config.json"))
	if err != nil {
		t.Fatal(err)
	}
	if err := json.NewEncoder(configFile).Encode(config); err != nil {
		t.Fatal(err)
	}
	if err := configFile.Close(); err != nil {
		t.Fatal(err)
	}

	var stdout, stderr bytes.Buffer
	cmd := Command{
		Stdout: &stdout,
		Stderr: &stderr,
		Env: func(key string) string {
			if key == "HOME" {
				return home
			}
			return ""
		},
	}

	code := cmd.Run(t.Context(), []string{"lm", "auth", "me"})
	if code != 0 {
		t.Fatalf("unexpected exit code %d, stderr: %s", code, stderr.String())
	}
	if !strings.Contains(stdout.String(), "subject_1") {
		t.Fatalf("unexpected stdout: %s", stdout.String())
	}
}
