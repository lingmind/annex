package annex

import (
	"bytes"
	"context"
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
	ProjectCode string
	UserAgent   string
	HTTPClient  *http.Client
}

type Client struct {
	baseURL     *url.URL
	token       string
	apiKey      string
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
		projectCode: cfg.ProjectCode,
		userAgent:   userAgent,
		httpClient:  httpClient,
	}, nil
}

func (c *Client) ListDevices(ctx context.Context, params ListDevicesParams) (*ListResponse[Device], error) {
	query := listValues(params.ListParams)
	addString(query, "state", params.State)
	addString(query, "type", params.Type)

	var out ListResponse[Device]
	if err := c.get(ctx, "/devices", query, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

func (c *Client) GetDevice(ctx context.Context, id string) (*Device, error) {
	var out Device
	if err := c.get(ctx, "/devices/"+url.PathEscape(id), nil, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

func (c *Client) ListMissions(ctx context.Context, params ListMissionsParams) (*ListResponse[Mission], error) {
	query := listValues(params.ListParams)
	addString(query, "state", params.State)
	addString(query, "type", params.Type)
	addString(query, "deviceId", params.DeviceID)

	var out ListResponse[Mission]
	if err := c.get(ctx, "/missions", query, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

func (c *Client) GetMission(ctx context.Context, id string) (*Mission, error) {
	var out Mission
	if err := c.get(ctx, "/missions/"+url.PathEscape(id), nil, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

func (c *Client) ListRawData(ctx context.Context, params ListRawDataParams) (*ListResponse[RawData], error) {
	query := listValues(params.ListParams)
	addString(query, "type", params.Type)
	addString(query, "missionId", params.MissionID)
	addString(query, "deviceId", params.DeviceID)
	addTime(query, "capturedAfter", params.CapturedAfter)
	addTime(query, "capturedBefore", params.CapturedBefore)

	var out ListResponse[RawData]
	if err := c.get(ctx, "/raw-data", query, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

func (c *Client) GetRawData(ctx context.Context, id string) (*RawData, error) {
	var out RawData
	if err := c.get(ctx, "/raw-data/"+url.PathEscape(id), nil, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

func (c *Client) ListRuleHits(ctx context.Context, params ListRuleHitsParams) (*ListResponse[RuleHit], error) {
	query := listValues(params.ListParams)
	addString(query, "state", params.State)
	addString(query, "severity", params.Severity)
	addString(query, "ruleId", params.RuleID)
	addString(query, "missionId", params.MissionID)
	addString(query, "deviceId", params.DeviceID)
	addTime(query, "hitAfter", params.HitAfter)
	addTime(query, "hitBefore", params.HitBefore)

	var out ListResponse[RuleHit]
	if err := c.get(ctx, "/rule-hits", query, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

func (c *Client) GetRuleHit(ctx context.Context, id string) (*RuleHit, error) {
	var out RuleHit
	if err := c.get(ctx, "/rule-hits/"+url.PathEscape(id), nil, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

func (c *Client) get(ctx context.Context, endpoint string, query url.Values, out any) error {
	return c.do(ctx, http.MethodGet, endpoint, query, nil, out)
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
	if c.projectCode != "" {
		req.Header.Set("X-LM-Project-Code", c.projectCode)
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
		values.Set("page", strconv.Itoa(params.Page))
	}
	if params.PageSize > 0 {
		values.Set("pageSize", strconv.Itoa(params.PageSize))
	}
	addTime(values, "updatedAfter", params.UpdatedAfter)
	addTime(values, "updatedBefore", params.UpdatedBefore)
	return values
}

func addString(values url.Values, key, value string) {
	if strings.TrimSpace(value) != "" {
		values.Set(key, value)
	}
}

func addTime(values url.Values, key string, value *time.Time) {
	if value != nil {
		values.Set(key, value.UTC().Format(time.RFC3339Nano))
	}
}

func joinURLPath(basePath, endpoint string) string {
	if basePath == "" {
		basePath = "/"
	}
	return path.Join(basePath, endpoint)
}
