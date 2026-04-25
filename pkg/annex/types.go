package annex

import "time"

const (
	GrantTypeClientCredentials = "client_credentials"
	GrantTypeRefreshToken      = "refresh_token"
)

type PageInfo struct {
	Page     int  `json:"page"`
	PageSize int  `json:"pageSize"`
	Total    *int `json:"total,omitempty"`
}

type ListResponse[T any] struct {
	Data []T      `json:"data"`
	Page PageInfo `json:"page"`
}

type AuthTokenRequest struct {
	GrantType    string   `json:"grantType"`
	ClientID     string   `json:"clientId,omitempty"`
	ClientSecret string   `json:"clientSecret,omitempty"`
	RefreshToken string   `json:"refreshToken,omitempty"`
	ProjectCode  string   `json:"projectCode,omitempty"`
	Scope        []string `json:"scope,omitempty"`
}

type AuthRefreshRequest struct {
	RefreshToken string `json:"refreshToken"`
	ProjectCode  string `json:"projectCode,omitempty"`
}

type AuthRevokeRequest struct {
	Token         string `json:"token"`
	TokenTypeHint string `json:"tokenTypeHint,omitempty"`
}

type AuthTokenResponse struct {
	AccessToken      string          `json:"accessToken"`
	TokenType        string          `json:"tokenType"`
	ExpiresIn        int             `json:"expiresIn"`
	RefreshToken     string          `json:"refreshToken,omitempty"`
	RefreshExpiresIn int             `json:"refreshExpiresIn,omitempty"`
	Scope            []string        `json:"scope,omitempty"`
	ProjectCode      string          `json:"projectCode,omitempty"`
	Projects         []ProjectAccess `json:"projects,omitempty"`
	Subject          *AuthSubject    `json:"subject,omitempty"`
}

type AuthSubject struct {
	ID          string          `json:"id"`
	Type        string          `json:"type"`
	Name        string          `json:"name,omitempty"`
	Email       string          `json:"email,omitempty"`
	ProjectCode string          `json:"projectCode,omitempty"`
	Projects    []ProjectAccess `json:"projects,omitempty"`
	Scopes      []string        `json:"scopes,omitempty"`
	ExpiresAt   *time.Time      `json:"expiresAt,omitempty"`
}

type ProjectAccess struct {
	ProjectCode string   `json:"projectCode"`
	Name        string   `json:"name,omitempty"`
	Scopes      []string `json:"scopes,omitempty"`
}

type Device struct {
	ID          string         `json:"id"`
	Name        string         `json:"name"`
	SN          string         `json:"sn,omitempty"`
	Type        string         `json:"type"`
	Vendor      string         `json:"vendor,omitempty"`
	Model       string         `json:"model,omitempty"`
	ProjectCode string         `json:"projectCode"`
	EdgeID      string         `json:"edgeId,omitempty"`
	State       string         `json:"state"`
	Online      bool           `json:"online"`
	LastSeenAt  *time.Time     `json:"lastSeenAt,omitempty"`
	Metadata    map[string]any `json:"metadata,omitempty"`
}

type Mission struct {
	ID          string         `json:"id"`
	Name        string         `json:"name"`
	Type        string         `json:"type"`
	State       string         `json:"state"`
	ProjectCode string         `json:"projectCode"`
	DeviceIDs   []string       `json:"deviceIds,omitempty"`
	StartedAt   *time.Time     `json:"startedAt,omitempty"`
	EndedAt     *time.Time     `json:"endedAt,omitempty"`
	CreatedAt   time.Time      `json:"createdAt"`
	UpdatedAt   time.Time      `json:"updatedAt"`
	Metadata    map[string]any `json:"metadata,omitempty"`
}

type RawData struct {
	ID          string         `json:"id"`
	ProjectCode string         `json:"projectCode"`
	MissionID   string         `json:"missionId,omitempty"`
	DeviceID    string         `json:"deviceId,omitempty"`
	Type        string         `json:"type"`
	MimeType    string         `json:"mimeType,omitempty"`
	SizeBytes   *int64         `json:"sizeBytes,omitempty"`
	DownloadURL string         `json:"downloadUrl,omitempty"`
	CapturedAt  *time.Time     `json:"capturedAt,omitempty"`
	CreatedAt   time.Time      `json:"createdAt"`
	Metadata    map[string]any `json:"metadata,omitempty"`
}

type RuleHit struct {
	ID          string         `json:"id"`
	ProjectCode string         `json:"projectCode"`
	RuleID      string         `json:"ruleId"`
	RuleName    string         `json:"ruleName"`
	Severity    string         `json:"severity"`
	State       string         `json:"state"`
	DeviceID    string         `json:"deviceId,omitempty"`
	MissionID   string         `json:"missionId,omitempty"`
	RawDataID   string         `json:"rawDataId,omitempty"`
	HitAt       time.Time      `json:"hitAt"`
	Evidence    []Evidence     `json:"evidence,omitempty"`
	Metadata    map[string]any `json:"metadata,omitempty"`
}

type Evidence struct {
	Type         string         `json:"type"`
	URL          string         `json:"url,omitempty"`
	ThumbnailURL string         `json:"thumbnailUrl,omitempty"`
	RawDataID    string         `json:"rawDataId,omitempty"`
	BBox         []float64      `json:"bbox,omitempty"`
	Metadata     map[string]any `json:"metadata,omitempty"`
}

type ListDevicesParams struct {
	ListParams
	State string
	Type  string
}

type ListMissionsParams struct {
	ListParams
	State    string
	Type     string
	DeviceID string
}

type ListRawDataParams struct {
	ListParams
	Type           string
	MissionID      string
	DeviceID       string
	CapturedAfter  *time.Time
	CapturedBefore *time.Time
}

type ListRuleHitsParams struct {
	ListParams
	State     string
	Severity  string
	RuleID    string
	MissionID string
	DeviceID  string
	HitAfter  *time.Time
	HitBefore *time.Time
}

type ListParams struct {
	Page          int
	PageSize      int
	UpdatedAfter  *time.Time
	UpdatedBefore *time.Time
}
