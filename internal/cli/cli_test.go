package cli

import (
	"bytes"
	"encoding/base64"
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
		if r.URL.Path != "/proxy/radix/api/devices" {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		if got := r.Header.Get("Authorization"); got != "Bearer token_123" {
			t.Fatalf("unexpected authorization header: %s", got)
		}
		if got := r.Header.Get("X-Requested-Project-Code"); got != "demo" {
			t.Fatalf("unexpected project header: %s", got)
		}
		if got := r.URL.Query().Get("filters[state][$eq]"); got != "online" {
			t.Fatalf("unexpected state query: %s", got)
		}
		if got := r.URL.Query().Get("populate"); got != "" {
			t.Fatalf("unexpected populate query: %s", got)
		}

		_ = json.NewEncoder(w).Encode(map[string]any{
			"data": []map[string]any{{
				"documentId": "dev_1",
				"name":       "Camera 1",
				"deviceType": "camera",
				"state":      "online",
			}},
			"meta": map[string]any{
				"pagination": map[string]any{
					"page":     1,
					"pageSize": 50,
					"total":    1,
				},
			},
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

func TestDevicesGetCommandAcceptsFormatAfterID(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/proxy/radix/api/devices/dev_1" {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{
			"data": map[string]any{
				"documentId": "dev_1",
				"name":       "Camera 1",
				"deviceType": "camera",
				"state":      "online",
			},
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
		"devices", "get", "dev_1",
		"--format", "json",
	})
	if code != 0 {
		t.Fatalf("unexpected exit code %d, stderr: %s", code, stderr.String())
	}
	if !strings.Contains(stdout.String(), `"id": "dev_1"`) {
		t.Fatalf("unexpected stdout: %s", stdout.String())
	}
}

func TestRenderTableDrawsBordersAndAlignsWideCells(t *testing.T) {
	var output bytes.Buffer
	renderTable(&output, []string{"ID", "NAME"}, [][]string{
		{"d1", "摄像头"},
		{"device-long", "Camera"},
	})

	expected := strings.Join([]string{
		"+-------------+--------+\n",
		"| ID          | NAME   |\n",
		"+-------------+--------+\n",
		"| d1          | 摄像头 |\n",
		"| device-long | Camera |\n",
		"+-------------+--------+\n",
	}, "")
	if output.String() != expected {
		t.Fatalf("unexpected table:\n%s", output.String())
	}
}

func TestAuthLoginSavesConfig(t *testing.T) {
	home := t.TempDir()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Fatalf("unexpected method: %s", r.Method)
		}
		if r.URL.Path != "/api/auth/login" {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		var request struct {
			Username string `json:"username"`
			Password string `json:"password"`
		}
		if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
			t.Fatal(err)
		}
		if request.Username != "demo@example.com" || request.Password != "secret_123" {
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
		"--username", "demo@example.com",
		"--password", "secret_123",
		"--project", "demo",
	})
	if code != 0 {
		t.Fatalf("unexpected exit code %d, stderr: %s", code, stderr.String())
	}
	if !strings.Contains(stdout.String(), `"access_token": "access_123456"`) {
		t.Fatalf("expected JSON token response in stdout, got: %s", stdout.String())
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
		t.Fatalf("auth me should not call server, got %s", r.URL.Path)
	}))
	defer server.Close()

	config := storedConfig{
		BaseURL:     server.URL,
		Token:       fakeJWT(map[string]any{"sub": "subject_1", "preferred_username": "demo integration"}),
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

	code := cmd.Run(t.Context(), []string{"lm", "auth", "me", "--format", "json"})
	if code != 0 {
		t.Fatalf("unexpected exit code %d, stderr: %s", code, stderr.String())
	}
	if !strings.Contains(stdout.String(), `"id": "subject_1"`) {
		t.Fatalf("unexpected stdout: %s", stdout.String())
	}
}

func fakeJWT(claims map[string]any) string {
	header, _ := json.Marshal(map[string]any{"alg": "none", "typ": "JWT"})
	payload, _ := json.Marshal(claims)
	return base64.RawURLEncoding.EncodeToString(header) + "." + base64.RawURLEncoding.EncodeToString(payload) + "."
}
