package annex

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestListDevicesSendsAuthProjectAndQuery(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/annex/v1/devices" {
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
		if got := r.URL.Query().Get("pageSize"); got != "20" {
			t.Fatalf("unexpected pageSize query: %s", got)
		}
		_ = json.NewEncoder(w).Encode(ListResponse[Device]{
			Data: []Device{{ID: "dev_1", Name: "Camera 1", Type: "camera", State: "online", ProjectCode: "demo", Online: true}},
			Page: PageInfo{Page: 1, PageSize: 20},
		})
	}))
	defer server.Close()

	client, err := NewClient(Config{
		BaseURL:     server.URL + "/api/annex/v1",
		Token:       "token_123",
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

func TestCreateTokenSendsClientCredentialRequest(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Fatalf("unexpected method: %s", r.Method)
		}
		if r.URL.Path != "/auth/token" {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		var request AuthTokenRequest
		if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
			t.Fatal(err)
		}
		if request.GrantType != GrantTypeClientCredentials || request.ClientID != "client_123" || request.ClientSecret != "secret_123" {
			t.Fatalf("unexpected token request: %#v", request)
		}
		_ = json.NewEncoder(w).Encode(AuthTokenResponse{
			AccessToken:  "access_123",
			TokenType:    "Bearer",
			ExpiresIn:    3600,
			RefreshToken: "refresh_123",
			ProjectCode:  "demo",
			Scope:        []string{"device:read"},
		})
	}))
	defer server.Close()

	client, err := NewClient(Config{BaseURL: server.URL})
	if err != nil {
		t.Fatal(err)
	}

	resp, err := client.CreateToken(context.Background(), AuthTokenRequest{
		GrantType:    GrantTypeClientCredentials,
		ClientID:     "client_123",
		ClientSecret: "secret_123",
		ProjectCode:  "demo",
		Scope:        []string{"device:read"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if resp.AccessToken != "access_123" || resp.RefreshToken != "refresh_123" {
		t.Fatalf("unexpected token response: %#v", resp)
	}
}

func TestAuthMeSendsBearerToken(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/auth/me" {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		if got := r.Header.Get("Authorization"); got != "Bearer access_123" {
			t.Fatalf("unexpected authorization header: %s", got)
		}
		_ = json.NewEncoder(w).Encode(AuthSubject{
			ID:          "subject_1",
			Type:        "integration",
			Name:        "demo integration",
			ProjectCode: "demo",
			Scopes:      []string{"device:read"},
		})
	}))
	defer server.Close()

	client, err := NewClient(Config{BaseURL: server.URL, Token: "access_123"})
	if err != nil {
		t.Fatal(err)
	}

	subject, err := client.AuthMe(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if subject.ID != "subject_1" || subject.ProjectCode != "demo" {
		t.Fatalf("unexpected subject: %#v", subject)
	}
}
