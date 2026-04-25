package webhook

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"
)

const (
	HeaderEvent     = "X-LM-Event"
	HeaderDelivery  = "X-LM-Delivery"
	HeaderTimestamp = "X-LM-Timestamp"
	HeaderSignature = "X-LM-Signature"
)

var (
	ErrMissingSecret    = errors.New("webhook secret is required")
	ErrMissingTimestamp = errors.New("missing webhook timestamp")
	ErrInvalidTimestamp = errors.New("invalid webhook timestamp")
	ErrTimestampSkew    = errors.New("webhook timestamp outside allowed skew")
	ErrMissingSignature = errors.New("missing webhook signature")
	ErrInvalidSignature = errors.New("invalid webhook signature")
)

type Verifier struct {
	Secret  string
	MaxSkew time.Duration
	Now     func() time.Time
}

func (v Verifier) Verify(header http.Header, body []byte) error {
	if v.Secret == "" {
		return ErrMissingSecret
	}

	timestampValue := header.Get(HeaderTimestamp)
	if timestampValue == "" {
		return ErrMissingTimestamp
	}

	timestampSeconds, err := strconv.ParseInt(timestampValue, 10, 64)
	if err != nil {
		return ErrInvalidTimestamp
	}

	now := time.Now
	if v.Now != nil {
		now = v.Now
	}

	maxSkew := v.MaxSkew
	if maxSkew == 0 {
		maxSkew = 5 * time.Minute
	}

	timestamp := time.Unix(timestampSeconds, 0)
	if delta := now().Sub(timestamp); delta > maxSkew || delta < -maxSkew {
		return ErrTimestampSkew
	}

	signature := header.Get(HeaderSignature)
	if signature == "" {
		return ErrMissingSignature
	}
	actual, err := ParseSignature(signature)
	if err != nil {
		return err
	}

	expected := computeSignatureBytes(v.Secret, timestampValue, body)
	if !hmac.Equal(expected, actual) {
		return ErrInvalidSignature
	}

	return nil
}

func ComputeSignature(secret, timestamp string, body []byte) string {
	return "sha256=" + hex.EncodeToString(computeSignatureBytes(secret, timestamp, body))
}

func computeSignatureBytes(secret, timestamp string, body []byte) []byte {
	mac := hmac.New(sha256.New, []byte(secret))
	_, _ = mac.Write([]byte(timestamp))
	_, _ = mac.Write([]byte("."))
	_, _ = mac.Write(body)
	return mac.Sum(nil)
}

func ParseSignature(signature string) ([]byte, error) {
	raw, ok := strings.CutPrefix(signature, "sha256=")
	if !ok {
		return nil, fmt.Errorf("%w: expected sha256 prefix", ErrInvalidSignature)
	}
	decoded, err := hex.DecodeString(raw)
	if err != nil {
		return nil, fmt.Errorf("%w: %v", ErrInvalidSignature, err)
	}
	return decoded, nil
}
