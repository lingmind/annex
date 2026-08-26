package annex

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestListDevicesSendsAuthProjectAndQuery(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/proxy/radix/api/devices" {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		if got := r.Header.Get("Authorization"); got != "Bearer token_123" {
			t.Fatalf("unexpected authorization header: %s", got)
		}
		if got := r.Header.Get("X-Requested-Project"); got != "project-doc-1" {
			t.Fatalf("unexpected project header: %s", got)
		}
		if got := r.Header.Get("X-Requested-Project-Code"); got != "" {
			t.Fatalf("retired project code header was sent: %s", got)
		}
		if got := r.URL.Query().Get("filters[state][$eq]"); got != "online" {
			t.Fatalf("unexpected state query: %s", got)
		}
		if got := r.URL.Query().Get("pagination[pageSize]"); got != "20" {
			t.Fatalf("unexpected pageSize query: %s", got)
		}
		if got := r.URL.Query().Get("populate"); got != "" {
			t.Fatalf("unexpected populate query: %s", got)
		}
		_ = json.NewEncoder(w).Encode(radixListResponse{
			Data: []map[string]any{{
				"documentId":   "dev_1",
				"name":         "Camera 1",
				"deviceType":   "camera",
				"state":        "online",
				"serialNumber": "sn_1",
			}},
			Meta: struct {
				Pagination struct {
					Page     int `json:"page"`
					PageSize int `json:"pageSize"`
					Total    int `json:"total"`
				} `json:"pagination"`
			}{
				Pagination: struct {
					Page     int `json:"page"`
					PageSize int `json:"pageSize"`
					Total    int `json:"total"`
				}{Page: 1, PageSize: 20, Total: 1},
			},
		})
	}))
	defer server.Close()

	client, err := NewClient(Config{
		BaseURL:     server.URL,
		Token:       "token_123",
		ProjectID:   "project-doc-1",
		ProjectCode: "demo",
	})
	if err != nil {
		t.Fatal(err)
	}

	resp, err := client.ListDevices(context.Background(), ListDevicesParams{
		ListParams: ListParams{PageSize: 20},
		State:      "online",
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(resp.Data) != 1 || resp.Data[0].ID != "dev_1" {
		t.Fatalf("unexpected response: %#v", resp)
	}
	if resp.Data[0].ProjectCode != "demo" {
		t.Fatalf("unexpected project code fallback: %#v", resp.Data[0])
	}
}

func TestAPIErrorIncludesRequestID(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusForbidden)
		_, _ = w.Write([]byte(`{"error":{"code":"permission_denied","message":"missing scope","requestId":"req_123"}}`))
	}))
	defer server.Close()

	client, err := NewClient(Config{BaseURL: server.URL})
	if err != nil {
		t.Fatal(err)
	}

	_, err = client.GetRuleHit(context.Background(), "hit_1")
	if err == nil {
		t.Fatal("expected error")
	}

	apiErr, ok := err.(*APIError)
	if !ok {
		t.Fatalf("expected APIError, got %T", err)
	}
	if apiErr.Code != "permission_denied" || apiErr.RequestID != "req_123" {
		t.Fatalf("unexpected API error: %#v", apiErr)
	}
}

func TestCreateTokenSendsPasswordLoginRequest(t *testing.T) {
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
		if request.Username != "user@example.com" || request.Password != "secret_123" {
			t.Fatalf("unexpected token request: %#v", request)
		}
		_ = json.NewEncoder(w).Encode(AuthTokenResponse{
			AccessToken:  "access_123",
			TokenType:    "Bearer",
			ExpiresIn:    3600,
			RefreshToken: "refresh_123",
			User: &AuthUser{Project: &AuthProject{
				ID:   "project-doc-1",
				Code: "demo",
			}},
			Scope: []string{"device:read"},
		})
	}))
	defer server.Close()

	client, err := NewClient(Config{BaseURL: server.URL})
	if err != nil {
		t.Fatal(err)
	}

	resp, err := client.CreateToken(context.Background(), AuthTokenRequest{
		GrantType:   GrantTypePassword,
		Username:    "user@example.com",
		Password:    "secret_123",
		ProjectCode: "demo",
	})
	if err != nil {
		t.Fatal(err)
	}
	if resp.AccessToken != "access_123" || resp.RefreshToken != "refresh_123" {
		t.Fatalf("unexpected token response: %#v", resp)
	}
	if resp.ProjectID != "project-doc-1" || resp.ProjectCode != "demo" {
		t.Fatalf("unexpected project context: %#v", resp)
	}
}

func TestAuthMeDecodesBearerTokenLocally(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Fatalf("auth me should not call server, got %s", r.URL.Path)
	}))
	defer server.Close()

	token := fakeJWT(map[string]any{
		"sub":                "subject_1",
		"preferred_username": "demo user",
		"email":              "demo@example.com",
		"realm_access":       map[string]any{"roles": []any{"device:read"}},
	})
	client, err := NewClient(Config{BaseURL: server.URL, Token: token})
	if err != nil {
		t.Fatal(err)
	}

	subject, err := client.AuthMe(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if subject.ID != "subject_1" || subject.Email != "demo@example.com" || len(subject.Scopes) != 1 {
		t.Fatalf("unexpected subject: %#v", subject)
	}
}

func fakeJWT(claims map[string]any) string {
	header, _ := json.Marshal(map[string]any{"alg": "none", "typ": "JWT"})
	payload, _ := json.Marshal(claims)
	return base64.RawURLEncoding.EncodeToString(header) + "." + base64.RawURLEncoding.EncodeToString(payload) + "."
}
