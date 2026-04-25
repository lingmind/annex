package annex

import (
	"encoding/json"
	"fmt"
	"strconv"
	"time"
)

func mapDevice(raw map[string]any, fallbackProjectCode string) Device {
	return Device{
		ID:          documentID(raw),
		Name:        stringValue(raw, "name"),
		SN:          firstString(raw, "serialNumber", "sn"),
		Type:        stringValue(raw, "deviceType"),
		Vendor:      firstString(raw, "manufacturer", "vendor"),
		Model:       stringValue(raw, "model"),
		ProjectCode: projectCode(raw, fallbackProjectCode),
		EdgeID:      nestedDocumentID(raw, "edge"),
		State:       stringValue(raw, "state"),
		Online:      stringValue(raw, "state") == "online",
		LastSeenAt:  timePtr(raw, "lastSeen"),
		Metadata:    metadata(raw),
	}
}

func mapMission(raw map[string]any, fallbackProjectCode string) Mission {
	return Mission{
		ID:          documentID(raw),
		Name:        stringValue(raw, "name"),
		Type:        stringValue(raw, "taskType"),
		State:       stringValue(raw, "state"),
		ProjectCode: projectCode(raw, fallbackProjectCode),
		DeviceIDs:   relationIDs(raw, "device"),
		StartedAt:   timePtr(raw, "executeTime"),
		EndedAt:     nil,
		CreatedAt:   timeValue(raw, "createdAt"),
		UpdatedAt:   timeValue(raw, "updatedAt"),
		Metadata:    metadata(raw),
	}
}

func mapRawData(raw map[string]any, fallbackProjectCode string) RawData {
	size := int64Ptr(raw, "fileSize")
	return RawData{
		ID:          documentID(raw),
		ProjectCode: projectCode(raw, fallbackProjectCode),
		MissionID:   nestedDocumentID(raw, "mission"),
		DeviceID:    nestedDocumentID(raw, "device"),
		Type:        stringValue(raw, "type"),
		MimeType:    stringValue(raw, "format"),
		SizeBytes:   size,
		DownloadURL: stringValue(raw, "fileUrl"),
		CapturedAt:  timePtr(raw, "captureTime"),
		CreatedAt:   timeValue(raw, "createdAt"),
		Metadata:    metadata(raw),
	}
}

func mapRuleHit(raw map[string]any, fallbackProjectCode string) RuleHit {
	return RuleHit{
		ID:          documentID(raw),
		ProjectCode: projectCode(raw, fallbackProjectCode),
		RuleID:      stringValue(raw, "ruleId"),
		RuleName:    firstString(raw, "ruleName", "ruleCode"),
		Severity:    stringValue(raw, "severity"),
		State:       stringValue(raw, "reviewState"),
		DeviceID:    nestedDocumentID(raw, "device"),
		MissionID:   nestedDocumentID(raw, "mission"),
		RawDataID:   nestedDocumentID(raw, "rawDatum"),
		HitAt:       timeValue(raw, "occurredAt"),
		Evidence:    evidence(raw),
		Metadata:    metadata(raw),
	}
}

func documentID(raw map[string]any) string {
	if value := stringValue(raw, "documentId"); value != "" {
		return value
	}
	return stringValue(raw, "id")
}

func projectCode(raw map[string]any, fallback string) string {
	if project, ok := raw["project"].(map[string]any); ok {
		if code := stringValue(project, "code"); code != "" {
			return code
		}
	}
	if code := stringValue(raw, "projectCode"); code != "" {
		return code
	}
	return fallback
}

func nestedDocumentID(raw map[string]any, key string) string {
	value, ok := raw[key]
	if !ok {
		return ""
	}
	if object, ok := value.(map[string]any); ok {
		return documentID(object)
	}
	return stringify(value)
}

func relationIDs(raw map[string]any, key string) []string {
	value, ok := raw[key]
	if !ok || value == nil {
		return nil
	}
	if object, ok := value.(map[string]any); ok {
		if id := documentID(object); id != "" {
			return []string{id}
		}
	}
	if values, ok := value.([]any); ok {
		ids := make([]string, 0, len(values))
		for _, item := range values {
			if object, ok := item.(map[string]any); ok {
				if id := documentID(object); id != "" {
					ids = append(ids, id)
				}
			}
		}
		return ids
	}
	return nil
}

func evidence(raw map[string]any) []Evidence {
	value, ok := raw["evidence"]
	if !ok || value == nil {
		return nil
	}
	if values, ok := value.([]any); ok {
		out := make([]Evidence, 0, len(values))
		for _, item := range values {
			if object, ok := item.(map[string]any); ok {
				out = append(out, Evidence{
					Type:         firstString(object, "type", "kind"),
					URL:          firstString(object, "url", "fileUrl"),
					ThumbnailURL: stringValue(object, "thumbnailUrl"),
					RawDataID:    stringValue(object, "rawDataId"),
					Metadata:     metadata(object),
				})
			}
		}
		return out
	}
	return []Evidence{{Type: "payload", Metadata: map[string]any{"value": value}}}
}

func metadata(raw map[string]any) map[string]any {
	if raw == nil {
		return nil
	}
	value, ok := raw["metadata"]
	if !ok || value == nil {
		return nil
	}
	object, ok := value.(map[string]any)
	if !ok {
		return map[string]any{"value": value}
	}
	copy := make(map[string]any, len(object))
	for key, value := range object {
		copy[key] = value
	}
	return copy
}

func stringValue(raw map[string]any, key string) string {
	if raw == nil {
		return ""
	}
	return stringify(raw[key])
}

func firstString(raw map[string]any, keys ...string) string {
	for _, key := range keys {
		if value := stringValue(raw, key); value != "" {
			return value
		}
	}
	return ""
}

func stringify(value any) string {
	switch typed := value.(type) {
	case nil:
		return ""
	case string:
		return typed
	case json.Number:
		return typed.String()
	case float64:
		if typed == float64(int64(typed)) {
			return strconv.FormatInt(int64(typed), 10)
		}
		return strconv.FormatFloat(typed, 'f', -1, 64)
	case int:
		return strconv.Itoa(typed)
	case int64:
		return strconv.FormatInt(typed, 10)
	default:
		return fmt.Sprint(typed)
	}
}

func numberValue(raw map[string]any, key string) float64 {
	if raw == nil {
		return 0
	}
	switch typed := raw[key].(type) {
	case float64:
		return typed
	case int:
		return float64(typed)
	case int64:
		return float64(typed)
	case json.Number:
		value, _ := typed.Float64()
		return value
	case string:
		value, _ := strconv.ParseFloat(typed, 64)
		return value
	default:
		return 0
	}
}

func int64Ptr(raw map[string]any, key string) *int64 {
	value := numberValue(raw, key)
	if value == 0 {
		return nil
	}
	out := int64(value)
	return &out
}

func timePtr(raw map[string]any, key string) *time.Time {
	value := timeValue(raw, key)
	if value.IsZero() {
		return nil
	}
	return &value
}

func timeValue(raw map[string]any, key string) time.Time {
	text := stringValue(raw, key)
	if text == "" {
		return time.Time{}
	}
	value, err := time.Parse(time.RFC3339Nano, text)
	if err != nil {
		return time.Time{}
	}
	return value
}

func stringSlice(value any) []string {
	items, ok := value.([]any)
	if !ok {
		return nil
	}
	out := make([]string, 0, len(items))
	for _, item := range items {
		if value := stringify(item); value != "" {
			out = append(out, value)
		}
	}
	return out
}
