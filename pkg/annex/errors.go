package annex

import "fmt"

type APIError struct {
	StatusCode int
	Code       string
	Message    string
	RequestID  string
}

func (e *APIError) Error() string {
	if e == nil {
		return "<nil>"
	}
	if e.RequestID != "" {
		return fmt.Sprintf("annex API error: status=%d code=%s message=%q request_id=%s", e.StatusCode, e.Code, e.Message, e.RequestID)
	}
	return fmt.Sprintf("annex API error: status=%d code=%s message=%q", e.StatusCode, e.Code, e.Message)
}
