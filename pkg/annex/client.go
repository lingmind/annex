package annex

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"path"
	"strconv"
	"strings"
	"time"
)

const defaultUserAgent = "lingmind-annex-go/0.1.0"

type Config struct {
	BaseURL     string
	Token       string
	APIKey      string
	ProjectID   string
	ProjectCode string
	UserAgent   string
	HTTPClient  *http.Client
}

type Client struct {
	baseURL     *url.URL
	token       string
	apiKey      string
	projectID   string
	projectCode string
	userAgent   string
	httpClient  *http.Client
}

func NewClient(cfg Config) (*Client, error) {
	if strings.TrimSpace(cfg.BaseURL) == "" {
		return nil, errors.New("base URL is required")
	}

	baseURL, err := url.Parse(strings.TrimRight(cfg.BaseURL, "/"))
	if err != nil {
		return nil, fmt.Errorf("parse base URL: %w", err)
	}
	if baseURL.Scheme == "" || baseURL.Host == "" {
		return nil, errors.New("base URL must include scheme and host")
	}

	httpClient := cfg.HTTPClient
	if httpClient == nil {
		httpClient = http.DefaultClient
	}

	userAgent := cfg.UserAgent
	if strings.TrimSpace(userAgent) == "" {
		userAgent = defaultUserAgent
	}

	return &Client{
		baseURL:     baseURL,
		token:       cfg.Token,
		apiKey:      cfg.APIKey,
		projectID:   strings.TrimSpace(cfg.ProjectID),
		projectCode: cfg.ProjectCode,
		userAgent:   userAgent,
		httpClient:  httpClient,
	}, nil
}

func (c *Client) ListDevices(ctx context.Context, params ListDevicesParams) (*ListResponse[Device], error) {
	query := listValues(params.ListParams)
	addFilter(query, "state", params.State)
	addFilter(query, "deviceType", params.Type)

	return getRadixList(ctx, c, "/proxy/radix/api/devices", query, mapDevice)
}

func (c *Client) GetDevice(ctx context.Context, id string) (*Device, error) {
	return getRadixItem(ctx, c, "/proxy/radix/api/devices/"+url.PathEscape(id), nil, mapDevice)
}

func (c *Client) CreateToken(ctx context.Context, request AuthTokenRequest) (*AuthTokenResponse, error) {
	if request.GrantType == "" {
		request.GrantType = GrantTypePassword
	}
	if request.GrantType == GrantTypeRefreshToken {
		return c.RefreshToken(ctx, AuthRefreshRequest{RefreshToken: request.RefreshToken, ProjectCode: request.ProjectCode})
	}

	var out AuthTokenResponse
	body := struct {
		Username string `json:"username"`
		Password string `json:"password"`
	}{
		Username: request.Username,
		Password: request.Password,
	}
	if err := c.post(ctx, "/api/auth/login", body, &out); err != nil {
		return nil, err
	}
	normalizeAuthResponse(&out)
	if out.ProjectCode == "" {
		out.ProjectCode = request.ProjectCode
	}
	return &out, nil
}

func (c *Client) RefreshToken(ctx context.Context, request AuthRefreshRequest) (*AuthTokenResponse, error) {
	var out AuthTokenResponse
	if err := c.post(ctx, "/api/auth/refresh", request, &out); err != nil {
		return nil, err
	}
	normalizeAuthResponse(&out)
	if out.ProjectCode == "" {
		out.ProjectCode = request.ProjectCode
	}
	return &out, nil
}

func (c *Client) AuthMe(ctx context.Context) (*AuthSubject, error) {
	if strings.TrimSpace(c.token) == "" {
		return nil, errors.New("bearer token is required")
	}
	return subjectFromJWT(c.token), nil
}

func (c *Client) RevokeToken(ctx context.Context, request AuthRevokeRequest) error {
	token := strings.TrimSpace(request.Token)
	if token == "" {
		token = c.token
	}
	return c.post(ctx, "/api/auth/logout", AuthRevokeRequest{Token: token}, nil)
}

func (c *Client) ListMissions(ctx context.Context, params ListMissionsParams) (*ListResponse[Mission], error) {
	query := listValues(params.ListParams)
	addFilter(query, "state", params.State)
	addFilter(query, "taskType", params.Type)
	addRelationFilter(query, "device", params.DeviceID)

	return getRadixList(ctx, c, "/proxy/radix/api/missions", query, mapMission)
}

func (c *Client) GetMission(ctx context.Context, id string) (*Mission, error) {
	return getRadixItem(ctx, c, "/proxy/radix/api/missions/"+url.PathEscape(id), nil, mapMission)
}

func (c *Client) ListRawData(ctx context.Context, params ListRawDataParams) (*ListResponse[RawData], error) {
	query := listValues(params.ListParams)
	addFilter(query, "type", params.Type)
	addRelationFilter(query, "mission", params.MissionID)
	addRelationFilter(query, "device", params.DeviceID)
	addFilterTime(query, "captureTime", "$gte", params.CapturedAfter)
	addFilterTime(query, "captureTime", "$lte", params.CapturedBefore)

	return getRadixList(ctx, c, "/proxy/radix/api/raw-data", query, mapRawData)
}

func (c *Client) GetRawData(ctx context.Context, id string) (*RawData, error) {
	return getRadixItem(ctx, c, "/proxy/radix/api/raw-data/"+url.PathEscape(id), nil, mapRawData)
}

func (c *Client) ListRuleHits(ctx context.Context, params ListRuleHitsParams) (*ListResponse[RuleHit], error) {
	query := listValues(params.ListParams)
	addFilter(query, "reviewState", params.State)
	addFilter(query, "severity", params.Severity)
	addFilter(query, "ruleId", params.RuleID)
	addRelationFilter(query, "mission", params.MissionID)
	addRelationFilter(query, "device", params.DeviceID)
	addFilterTime(query, "occurredAt", "$gte", params.HitAfter)
	addFilterTime(query, "occurredAt", "$lte", params.HitBefore)

	return getRadixList(ctx, c, "/proxy/radix/api/rule-hits", query, mapRuleHit)
}

func (c *Client) GetRuleHit(ctx context.Context, id string) (*RuleHit, error) {
	return getRadixItem(ctx, c, "/proxy/radix/api/rule-hits/"+url.PathEscape(id), nil, mapRuleHit)
}

func (c *Client) get(ctx context.Context, endpoint string, query url.Values, out any) error {
	return c.do(ctx, http.MethodGet, endpoint, query, nil, out)
}

func (c *Client) post(ctx context.Context, endpoint string, body any, out any) error {
	return c.do(ctx, http.MethodPost, endpoint, nil, body, out)
}

func (c *Client) do(ctx context.Context, method, endpoint string, query url.Values, body any, out any) error {
	u := *c.baseURL
	u.Path = joinURLPath(c.baseURL.Path, endpoint)
	if len(query) > 0 {
		u.RawQuery = query.Encode()
	}

	var reader io.Reader
	if body != nil {
		payload, err := json.Marshal(body)
		if err != nil {
			return fmt.Errorf("marshal request body: %w", err)
		}
		reader = bytes.NewReader(payload)
	}

	req, err := http.NewRequestWithContext(ctx, method, u.String(), reader)
	if err != nil {
		return fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Accept", "application/json")
	req.Header.Set("User-Agent", c.userAgent)
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	if c.token != "" {
		req.Header.Set("Authorization", "Bearer "+c.token)
	}
	if c.apiKey != "" {
		req.Header.Set("X-LM-API-Key", c.apiKey)
	}
	if c.projectID != "" {
		req.Header.Set("X-Requested-Project", c.projectID)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return decodeAPIError(resp)
	}
	if out == nil || resp.StatusCode == http.StatusNoContent {
		return nil
	}
	if err := json.NewDecoder(resp.Body).Decode(out); err != nil {
		return fmt.Errorf("decode response: %w", err)
	}
	return nil
}

func decodeAPIError(resp *http.Response) error {
	var payload struct {
		Error struct {
			Code      string `json:"code"`
			Message   string `json:"message"`
			RequestID string `json:"requestId"`
		} `json:"error"`
	}

	body, _ := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if len(body) > 0 {
		_ = json.Unmarshal(body, &payload)
		if payload.Error.Code == "" {
			var phoenixError map[string]string
			if err := json.Unmarshal(body, &phoenixError); err == nil {
				payload.Error.Message = phoenixError["error"]
			}
		}
	}

	apiErr := &APIError{
		StatusCode: resp.StatusCode,
		Code:       payload.Error.Code,
		Message:    payload.Error.Message,
		RequestID:  payload.Error.RequestID,
	}
	if apiErr.Code == "" {
		apiErr.Code = strings.ToLower(strings.ReplaceAll(http.StatusText(resp.StatusCode), " ", "_"))
	}
	if apiErr.Message == "" {
		apiErr.Message = strings.TrimSpace(string(body))
	}
	if apiErr.Message == "" {
		apiErr.Message = http.StatusText(resp.StatusCode)
	}
	if apiErr.RequestID == "" {
		apiErr.RequestID = resp.Header.Get("X-Request-ID")
	}
	return apiErr
}

func listValues(params ListParams) url.Values {
	values := url.Values{}
	if params.Page > 0 {
		values.Set("pagination[page]", strconv.Itoa(params.Page))
	}
	if params.PageSize > 0 {
		values.Set("pagination[pageSize]", strconv.Itoa(params.PageSize))
	}
	addFilterTime(values, "updatedAt", "$gte", params.UpdatedAfter)
	addFilterTime(values, "updatedAt", "$lte", params.UpdatedBefore)
	return values
}

func addFilter(values url.Values, field, value string) {
	if strings.TrimSpace(value) != "" {
		values.Set("filters["+field+"]["+"$eq"+"]", value)
	}
}

func addRelationFilter(values url.Values, relation, documentID string) {
	if strings.TrimSpace(documentID) != "" {
		values.Set("filters["+relation+"][documentId][$eq]", documentID)
	}
}

func addFilterTime(values url.Values, field, op string, value *time.Time) {
	if value != nil {
		values.Set("filters["+field+"]["+op+"]", value.UTC().Format(time.RFC3339Nano))
	}
}

func joinURLPath(basePath, endpoint string) string {
	if basePath == "" {
		basePath = "/"
	}
	return path.Join(basePath, endpoint)
}

type radixListResponse struct {
	Data []map[string]any `json:"data"`
	Meta struct {
		Pagination struct {
			Page     int `json:"page"`
			PageSize int `json:"pageSize"`
			Total    int `json:"total"`
		} `json:"pagination"`
	} `json:"meta"`
}

type radixItemResponse struct {
	Data map[string]any `json:"data"`
}

func getRadixList[T any](ctx context.Context, client *Client, endpoint string, query url.Values, mapper func(map[string]any, string) T) (*ListResponse[T], error) {
	var raw radixListResponse
	if err := client.get(ctx, endpoint, query, &raw); err != nil {
		return nil, err
	}

	items := make([]T, 0, len(raw.Data))
	for _, item := range raw.Data {
		items = append(items, mapper(item, client.projectCode))
	}

	total := raw.Meta.Pagination.Total
	return &ListResponse[T]{
		Data: items,
		Page: PageInfo{
			Page:     raw.Meta.Pagination.Page,
			PageSize: raw.Meta.Pagination.PageSize,
			Total:    &total,
		},
	}, nil
}

func getRadixItem[T any](ctx context.Context, client *Client, endpoint string, query url.Values, mapper func(map[string]any, string) T) (*T, error) {
	var raw radixItemResponse
	if err := client.get(ctx, endpoint, query, &raw); err != nil {
		return nil, err
	}
	item := mapper(raw.Data, client.projectCode)
	return &item, nil
}

func normalizeAuthResponse(response *AuthTokenResponse) {
	if response == nil {
		return
	}
	if response.TokenType == "" {
		response.TokenType = "Bearer"
	}
	if response.Subject == nil {
		response.Subject = subjectFromJWT(response.AccessToken)
	}
	if response.ProjectCode == "" && response.Subject != nil {
		response.ProjectCode = response.Subject.ProjectCode
	}
	if response.ProjectID == "" && response.Subject != nil {
		response.ProjectID = response.Subject.ProjectID
	}
	if response.User != nil && response.User.Project != nil {
		if response.ProjectID == "" {
			response.ProjectID = response.User.Project.ID
		}
		if response.ProjectCode == "" {
			response.ProjectCode = response.User.Project.Code
		}
	}
}

func subjectFromJWT(token string) *AuthSubject {
	parts := strings.Split(token, ".")
	if len(parts) < 2 {
		return &AuthSubject{Type: "bearer"}
	}
	payload, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return &AuthSubject{Type: "bearer"}
	}
	var claims map[string]any
	if err := json.Unmarshal(payload, &claims); err != nil {
		return &AuthSubject{Type: "bearer"}
	}
	subject := &AuthSubject{
		ID:    stringValue(claims, "sub"),
		Type:  "user",
		Name:  firstString(claims, "name", "preferred_username"),
		Email: stringValue(claims, "email"),
	}
	if exp := numberValue(claims, "exp"); exp > 0 {
		expiresAt := time.Unix(int64(exp), 0).UTC()
		subject.ExpiresAt = &expiresAt
	}
	if realmAccess, ok := claims["realm_access"].(map[string]any); ok {
		subject.Scopes = stringSlice(realmAccess["roles"])
	}
	return subject
}
