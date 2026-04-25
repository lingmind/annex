package cli

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
	"unicode"

	"github.com/lingmind/annex/pkg/annex"
	"github.com/lingmind/annex/pkg/webhook"
)

type Command struct {
	Stdout io.Writer
	Stderr io.Writer
	Env    func(string) string
}

type globalOptions struct {
	baseURL      string
	token        string
	apiKey       string
	refreshToken string
	projectCode  string
	format       string
}

type storedConfig struct {
	BaseURL      string     `json:"baseUrl,omitempty"`
	Token        string     `json:"token,omitempty"`
	RefreshToken string     `json:"refreshToken,omitempty"`
	ProjectCode  string     `json:"projectCode,omitempty"`
	ExpiresAt    *time.Time `json:"expiresAt,omitempty"`
}

func Main(args []string) int {
	cmd := Command{
		Stdout: os.Stdout,
		Stderr: os.Stderr,
		Env:    os.Getenv,
	}
	return cmd.Run(context.Background(), args)
}

func (c Command) Run(ctx context.Context, args []string) int {
	if c.Stdout == nil {
		c.Stdout = io.Discard
	}
	if c.Stderr == nil {
		c.Stderr = io.Discard
	}
	if c.Env == nil {
		c.Env = os.Getenv
	}

	if len(args) == 0 {
		args = []string{"lm"}
	}

	global, rest, err := c.parseGlobal(args[1:])
	if err != nil {
		fmt.Fprintln(c.Stderr, err)
		return 2
	}
	if len(rest) == 0 || rest[0] == "help" || rest[0] == "-h" || rest[0] == "--help" {
		c.printUsage()
		return 0
	}

	switch rest[0] {
	case "auth":
		return c.runAuth(ctx, global, rest[1:])
	case "devices":
		return c.runDevices(ctx, global, rest[1:])
	case "missions":
		return c.runMissions(ctx, global, rest[1:])
	case "raw-data":
		return c.runRawData(ctx, global, rest[1:])
	case "rule-hits":
		return c.runRuleHits(ctx, global, rest[1:])
	case "serve":
		return c.runServe(rest[1:])
	default:
		fmt.Fprintf(c.Stderr, "unknown command %q\n\n", rest[0])
		c.printUsage()
		return 2
	}
}

func (c Command) parseGlobal(args []string) (globalOptions, []string, error) {
	config, err := c.loadConfig()
	if err != nil {
		return globalOptions{}, nil, err
	}

	opts := globalOptions{
		baseURL:      config.BaseURL,
		token:        config.Token,
		refreshToken: config.RefreshToken,
		projectCode:  config.ProjectCode,
		format:       "json",
	}
	overrideString(&opts.baseURL, c.Env("LM_BASE_URL"))
	overrideString(&opts.token, c.Env("LM_TOKEN"))
	overrideString(&opts.refreshToken, c.Env("LM_REFRESH_TOKEN"))
	overrideString(&opts.projectCode, c.Env("LM_PROJECT_CODE"))
	opts.apiKey = c.Env("LM_API_KEY")
	if format := c.Env("LM_FORMAT"); strings.TrimSpace(format) != "" {
		opts.format = format
	}

	fs := flag.NewFlagSet("lm", flag.ContinueOnError)
	fs.SetOutput(c.Stderr)
	fs.StringVar(&opts.baseURL, "base-url", opts.baseURL, "Annex API base URL")
	fs.StringVar(&opts.token, "token", opts.token, "Bearer token")
	fs.StringVar(&opts.apiKey, "api-key", opts.apiKey, "API key")
	fs.StringVar(&opts.refreshToken, "refresh-token", opts.refreshToken, "refresh token")
	fs.StringVar(&opts.projectCode, "project", opts.projectCode, "project code")
	fs.StringVar(&opts.format, "format", opts.format, "output format: json, table, or env")
	if err := fs.Parse(args); err != nil {
		return opts, nil, err
	}
	return opts, fs.Args(), nil
}

func overrideString(target *string, value string) {
	if strings.TrimSpace(value) != "" {
		*target = value
	}
}

func (c Command) loadConfig() (storedConfig, error) {
	path, err := c.configPath()
	if err != nil {
		return storedConfig{}, nil
	}

	file, err := os.Open(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return storedConfig{}, nil
		}
		return storedConfig{}, fmt.Errorf("读取配置文件失败: %w", err)
	}
	defer file.Close()

	var config storedConfig
	if err := json.NewDecoder(file).Decode(&config); err != nil {
		return storedConfig{}, fmt.Errorf("解析配置文件失败: %w", err)
	}
	return config, nil
}

func (c Command) saveConfig(config storedConfig) (string, error) {
	path, err := c.configPath()
	if err != nil {
		return "", err
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return "", fmt.Errorf("创建配置目录失败: %w", err)
	}

	file, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0o600)
	if err != nil {
		return "", fmt.Errorf("写入配置文件失败: %w", err)
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(config); err != nil {
		return "", fmt.Errorf("编码配置文件失败: %w", err)
	}
	return path, nil
}

func (c Command) configPath() (string, error) {
	if path := strings.TrimSpace(c.Env("LM_CONFIG")); path != "" {
		return path, nil
	}
	if home := strings.TrimSpace(c.Env("HOME")); home != "" {
		return filepath.Join(home, ".lm", "config.json"), nil
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("无法确定配置文件路径: %w", err)
	}
	return filepath.Join(home, ".lm", "config.json"), nil
}

func (c Command) configForToken(global globalOptions, response *annex.AuthTokenResponse) storedConfig {
	config := storedConfig{
		BaseURL:      global.baseURL,
		Token:        response.AccessToken,
		RefreshToken: response.RefreshToken,
		ProjectCode:  response.ProjectCode,
	}
	if config.ProjectCode == "" {
		config.ProjectCode = global.projectCode
	}
	if response.ExpiresIn > 0 {
		expiresAt := time.Now().Add(time.Duration(response.ExpiresIn) * time.Second)
		config.ExpiresAt = &expiresAt
	}
	return config
}

func (c Command) runAuth(ctx context.Context, global globalOptions, args []string) int {
	if len(args) == 0 {
		return c.usageError("auth requires login, refresh, me, or revoke")
	}

	switch args[0] {
	case "login":
		return c.runAuthLogin(ctx, global, args[1:])
	case "refresh":
		return c.runAuthRefresh(ctx, global, args[1:])
	case "me":
		return c.runAuthMe(ctx, global, args[1:])
	case "revoke":
		return c.runAuthRevoke(ctx, global, args[1:])
	default:
		return c.usageError("auth requires login, refresh, me, or revoke")
	}
}

func (c Command) runAuthLogin(ctx context.Context, global globalOptions, args []string) int {
	username := c.Env("LM_USERNAME")
	password := c.Env("LM_PASSWORD")
	projectCode := global.projectCode
	format := global.format
	save := true

	fs := flag.NewFlagSet("auth login", flag.ContinueOnError)
	fs.SetOutput(c.Stderr)
	fs.StringVar(&username, "username", username, "LingMind username")
	fs.StringVar(&password, "password", password, "LingMind password")
	fs.StringVar(&projectCode, "project", projectCode, "project code")
	fs.StringVar(&format, "format", format, "output format: json, table, or env")
	fs.BoolVar(&save, "save", save, "save token to local config")
	if err := fs.Parse(args); err != nil {
		return c.error(err)
	}
	if strings.TrimSpace(username) == "" {
		return c.usageError("auth login requires --username or LM_USERNAME")
	}
	if strings.TrimSpace(password) == "" {
		return c.usageError("auth login requires --password or LM_PASSWORD")
	}

	client, err := c.anonymousClient(global)
	if err != nil {
		return c.error(err)
	}
	response, err := client.CreateToken(ctx, annex.AuthTokenRequest{
		GrantType:   annex.GrantTypePassword,
		Username:    username,
		Password:    password,
		ProjectCode: projectCode,
	})
	if err != nil {
		return c.error(err)
	}

	savedPath := ""
	if save {
		savedPath, err = c.saveConfig(c.configForToken(global, response))
		if err != nil {
			return c.error(err)
		}
	}
	return c.printTokenResponse(format, response, savedPath)
}

func (c Command) runAuthRefresh(ctx context.Context, global globalOptions, args []string) int {
	refreshToken := global.refreshToken
	projectCode := global.projectCode
	format := global.format
	save := true

	fs := flag.NewFlagSet("auth refresh", flag.ContinueOnError)
	fs.SetOutput(c.Stderr)
	fs.StringVar(&refreshToken, "refresh-token", refreshToken, "refresh token")
	fs.StringVar(&projectCode, "project", projectCode, "project code")
	fs.StringVar(&format, "format", format, "output format: json, table, or env")
	fs.BoolVar(&save, "save", save, "save refreshed token to local config")
	if err := fs.Parse(args); err != nil {
		return c.error(err)
	}
	if strings.TrimSpace(refreshToken) == "" {
		return c.usageError("auth refresh requires --refresh-token, LM_REFRESH_TOKEN, or saved config")
	}

	client, err := c.anonymousClient(global)
	if err != nil {
		return c.error(err)
	}
	response, err := client.RefreshToken(ctx, annex.AuthRefreshRequest{
		RefreshToken: refreshToken,
		ProjectCode:  projectCode,
	})
	if err != nil {
		return c.error(err)
	}
	if response.RefreshToken == "" {
		response.RefreshToken = refreshToken
	}

	savedPath := ""
	if save {
		savedPath, err = c.saveConfig(c.configForToken(global, response))
		if err != nil {
			return c.error(err)
		}
	}
	return c.printTokenResponse(format, response, savedPath)
}

func (c Command) runAuthMe(ctx context.Context, global globalOptions, args []string) int {
	args, format, err := extractFormatFlag(args, global.format)
	if err != nil {
		return c.error(err)
	}
	if len(args) > 0 {
		return c.usageError("auth me accepts only --format")
	}

	client, err := c.client(global)
	if err != nil {
		return c.error(err)
	}
	subject, err := client.AuthMe(ctx)
	if err != nil {
		return c.error(err)
	}
	return c.printAuthSubject(format, subject)
}

func (c Command) runAuthRevoke(ctx context.Context, global globalOptions, args []string) int {
	token := global.token

	fs := flag.NewFlagSet("auth revoke", flag.ContinueOnError)
	fs.SetOutput(c.Stderr)
	fs.StringVar(&token, "token", token, "token to revoke")
	if err := fs.Parse(args); err != nil {
		return c.error(err)
	}
	if strings.TrimSpace(token) == "" {
		return c.usageError("auth revoke requires --token, LM_TOKEN, or saved config")
	}

	authGlobal := global
	if authGlobal.token == "" {
		authGlobal.token = token
	}
	client, err := c.client(authGlobal)
	if err != nil {
		return c.error(err)
	}
	if err := client.RevokeToken(ctx, annex.AuthRevokeRequest{Token: token}); err != nil {
		return c.error(err)
	}

	config, _ := c.loadConfig()
	if token == config.Token {
		config.Token = ""
		config.ExpiresAt = nil
		_, _ = c.saveConfig(config)
	}
	if token == config.RefreshToken {
		config.RefreshToken = ""
		_, _ = c.saveConfig(config)
	}
	fmt.Fprintln(c.Stdout, "token revoked")
	return 0
}

func (c Command) client(opts globalOptions) (*annex.Client, error) {
	if strings.TrimSpace(opts.baseURL) == "" {
		return nil, errors.New("base URL is required; set --base-url or LM_BASE_URL")
	}
	return annex.NewClient(annex.Config{
		BaseURL:     opts.baseURL,
		Token:       opts.token,
		APIKey:      opts.apiKey,
		ProjectCode: opts.projectCode,
	})
}

func (c Command) anonymousClient(opts globalOptions) (*annex.Client, error) {
	if strings.TrimSpace(opts.baseURL) == "" {
		return nil, errors.New("base URL is required; set --base-url or LM_BASE_URL")
	}
	return annex.NewClient(annex.Config{BaseURL: opts.baseURL, ProjectCode: opts.projectCode})
}

func (c Command) runDevices(ctx context.Context, global globalOptions, args []string) int {
	if len(args) == 0 {
		return c.usageError("devices requires list or get")
	}
	client, err := c.client(global)
	if err != nil {
		return c.error(err)
	}

	switch args[0] {
	case "list":
		params, format, err := parseDeviceListFlags(args[1:], c.Stderr, global.format)
		if err != nil {
			return c.error(err)
		}
		resp, err := client.ListDevices(ctx, params)
		if err != nil {
			return c.error(err)
		}
		return c.printDeviceList(format, resp.Data)
	case "get":
		id, format, err := parseGetArgs("devices get", args[1:], global.format)
		if err != nil {
			return c.usageError("devices get requires <device-id>")
		}
		resp, err := client.GetDevice(ctx, id)
		if err != nil {
			return c.error(err)
		}
		return c.printDeviceList(format, []annex.Device{*resp})
	default:
		return c.usageError("devices requires list or get")
	}
}

func (c Command) runMissions(ctx context.Context, global globalOptions, args []string) int {
	if len(args) == 0 {
		return c.usageError("missions requires list or get")
	}
	client, err := c.client(global)
	if err != nil {
		return c.error(err)
	}

	switch args[0] {
	case "list":
		params, format, err := parseMissionListFlags(args[1:], c.Stderr, global.format)
		if err != nil {
			return c.error(err)
		}
		resp, err := client.ListMissions(ctx, params)
		if err != nil {
			return c.error(err)
		}
		return c.printMissionList(format, resp.Data)
	case "get":
		id, format, err := parseGetArgs("missions get", args[1:], global.format)
		if err != nil {
			return c.usageError("missions get requires <mission-id>")
		}
		resp, err := client.GetMission(ctx, id)
		if err != nil {
			return c.error(err)
		}
		return c.printMissionList(format, []annex.Mission{*resp})
	default:
		return c.usageError("missions requires list or get")
	}
}

func (c Command) runRawData(ctx context.Context, global globalOptions, args []string) int {
	if len(args) == 0 {
		return c.usageError("raw-data requires list or get")
	}
	client, err := c.client(global)
	if err != nil {
		return c.error(err)
	}

	switch args[0] {
	case "list":
		params, format, err := parseRawDataListFlags(args[1:], c.Stderr, global.format)
		if err != nil {
			return c.error(err)
		}
		resp, err := client.ListRawData(ctx, params)
		if err != nil {
			return c.error(err)
		}
		return c.printRawDataList(format, resp.Data)
	case "get":
		id, format, err := parseGetArgs("raw-data get", args[1:], global.format)
		if err != nil {
			return c.usageError("raw-data get requires <raw-data-id>")
		}
		resp, err := client.GetRawData(ctx, id)
		if err != nil {
			return c.error(err)
		}
		return c.printRawDataList(format, []annex.RawData{*resp})
	default:
		return c.usageError("raw-data requires list or get")
	}
}

func (c Command) runRuleHits(ctx context.Context, global globalOptions, args []string) int {
	if len(args) == 0 {
		return c.usageError("rule-hits requires list or get")
	}
	client, err := c.client(global)
	if err != nil {
		return c.error(err)
	}

	switch args[0] {
	case "list":
		params, format, err := parseRuleHitListFlags(args[1:], c.Stderr, global.format)
		if err != nil {
			return c.error(err)
		}
		resp, err := client.ListRuleHits(ctx, params)
		if err != nil {
			return c.error(err)
		}
		return c.printRuleHitList(format, resp.Data)
	case "get":
		id, format, err := parseGetArgs("rule-hits get", args[1:], global.format)
		if err != nil {
			return c.usageError("rule-hits get requires <rule-hit-id>")
		}
		resp, err := client.GetRuleHit(ctx, id)
		if err != nil {
			return c.error(err)
		}
		return c.printRuleHitList(format, []annex.RuleHit{*resp})
	default:
		return c.usageError("rule-hits requires list or get")
	}
}

func (c Command) runServe(args []string) int {
	secret := c.Env("LM_WEBHOOK_SECRET")
	addr := ":8080"
	path := "/lingmind/webhook"

	fs := flag.NewFlagSet("serve", flag.ContinueOnError)
	fs.SetOutput(c.Stderr)
	fs.StringVar(&addr, "addr", addr, "listen address")
	fs.StringVar(&path, "path", path, "webhook path")
	fs.StringVar(&secret, "secret", secret, "webhook secret")
	if err := fs.Parse(args); err != nil {
		return c.error(err)
	}

	logger := slog.New(slog.NewTextHandler(c.Stderr, nil))
	server := webhook.Server{
		Secret: secret,
		Path:   path,
		Logger: logger,
		Handler: webhook.HandlerFunc(func(event webhook.Event) error {
			payload, err := json.Marshal(event)
			if err != nil {
				return err
			}
			fmt.Fprintln(c.Stdout, string(payload))
			return nil
		}),
	}

	if secret == "" {
		logger.Warn("webhook secret is empty; signature verification is disabled")
	}

	logger.Info("listening for LingMind Annex webhooks", "addr", addr, "path", path)
	if err := http.ListenAndServe(addr, server.HandlerFunc()); err != nil {
		return c.error(err)
	}
	return 0
}

func parseDeviceListFlags(args []string, output io.Writer, defaultFormat string) (annex.ListDevicesParams, string, error) {
	var params annex.ListDevicesParams
	args, format, err := extractFormatFlag(args, defaultFormat)
	if err != nil {
		return params, "", err
	}

	var updatedAfter, updatedBefore string
	fs := newListFlagSet("devices list", output, &params.ListParams, &updatedAfter, &updatedBefore)
	fs.StringVar(&params.State, "state", "", "device state")
	fs.StringVar(&params.Type, "type", "", "device type")
	if err := fs.Parse(args); err != nil {
		return params, "", err
	}
	return params, format, parseListTimes(&params.ListParams, updatedAfter, updatedBefore)
}

func parseMissionListFlags(args []string, output io.Writer, defaultFormat string) (annex.ListMissionsParams, string, error) {
	var params annex.ListMissionsParams
	args, format, err := extractFormatFlag(args, defaultFormat)
	if err != nil {
		return params, "", err
	}

	var updatedAfter, updatedBefore string
	fs := newListFlagSet("missions list", output, &params.ListParams, &updatedAfter, &updatedBefore)
	fs.StringVar(&params.State, "state", "", "mission state")
	fs.StringVar(&params.Type, "type", "", "mission type")
	fs.StringVar(&params.DeviceID, "device-id", "", "device ID")
	if err := fs.Parse(args); err != nil {
		return params, "", err
	}
	return params, format, parseListTimes(&params.ListParams, updatedAfter, updatedBefore)
}

func parseRawDataListFlags(args []string, output io.Writer, defaultFormat string) (annex.ListRawDataParams, string, error) {
	var params annex.ListRawDataParams
	args, format, err := extractFormatFlag(args, defaultFormat)
	if err != nil {
		return params, "", err
	}

	var updatedAfter, updatedBefore string
	fs := newListFlagSet("raw-data list", output, &params.ListParams, &updatedAfter, &updatedBefore)
	fs.StringVar(&params.Type, "type", "", "raw data type")
	fs.StringVar(&params.MissionID, "mission-id", "", "mission ID")
	fs.StringVar(&params.DeviceID, "device-id", "", "device ID")
	var capturedAfter, capturedBefore string
	fs.StringVar(&capturedAfter, "captured-after", "", "captured after RFC3339 timestamp")
	fs.StringVar(&capturedBefore, "captured-before", "", "captured before RFC3339 timestamp")
	if err := fs.Parse(args); err != nil {
		return params, "", err
	}
	if err := parseListTimes(&params.ListParams, updatedAfter, updatedBefore); err != nil {
		return params, "", err
	}
	params.CapturedAfter, err = parseOptionalTime(capturedAfter)
	if err != nil {
		return params, "", fmt.Errorf("parse --captured-after: %w", err)
	}
	params.CapturedBefore, err = parseOptionalTime(capturedBefore)
	if err != nil {
		return params, "", fmt.Errorf("parse --captured-before: %w", err)
	}
	return params, format, nil
}

func parseRuleHitListFlags(args []string, output io.Writer, defaultFormat string) (annex.ListRuleHitsParams, string, error) {
	var params annex.ListRuleHitsParams
	args, format, err := extractFormatFlag(args, defaultFormat)
	if err != nil {
		return params, "", err
	}

	var updatedAfter, updatedBefore string
	fs := newListFlagSet("rule-hits list", output, &params.ListParams, &updatedAfter, &updatedBefore)
	fs.StringVar(&params.State, "state", "", "rule hit state")
	fs.StringVar(&params.Severity, "severity", "", "severity")
	fs.StringVar(&params.RuleID, "rule-id", "", "rule ID")
	fs.StringVar(&params.MissionID, "mission-id", "", "mission ID")
	fs.StringVar(&params.DeviceID, "device-id", "", "device ID")
	var hitAfter, hitBefore string
	fs.StringVar(&hitAfter, "hit-after", "", "hit after RFC3339 timestamp")
	fs.StringVar(&hitBefore, "hit-before", "", "hit before RFC3339 timestamp")
	if err := fs.Parse(args); err != nil {
		return params, "", err
	}
	if err := parseListTimes(&params.ListParams, updatedAfter, updatedBefore); err != nil {
		return params, "", err
	}
	params.HitAfter, err = parseOptionalTime(hitAfter)
	if err != nil {
		return params, "", fmt.Errorf("parse --hit-after: %w", err)
	}
	params.HitBefore, err = parseOptionalTime(hitBefore)
	if err != nil {
		return params, "", fmt.Errorf("parse --hit-before: %w", err)
	}
	return params, format, nil
}

func parseGetArgs(name string, args []string, defaultFormat string) (string, string, error) {
	args, format, err := extractFormatFlag(args, defaultFormat)
	if err != nil {
		return "", "", err
	}
	id, ok := firstArg(args)
	if !ok {
		return "", "", fmt.Errorf("%s requires an id", name)
	}
	if len(args) > 1 {
		return "", "", fmt.Errorf("%s accepts only one id", name)
	}
	return id, format, nil
}

func extractFormatFlag(args []string, defaultFormat string) ([]string, string, error) {
	format := defaultFormat
	filtered := make([]string, 0, len(args))

	for i := 0; i < len(args); i++ {
		arg := args[i]
		switch {
		case arg == "--format" || arg == "-format":
			if i+1 >= len(args) || strings.HasPrefix(args[i+1], "-") {
				return nil, "", fmt.Errorf("%s requires a value", arg)
			}
			format = args[i+1]
			i++
		case strings.HasPrefix(arg, "--format="):
			format = strings.TrimPrefix(arg, "--format=")
		case strings.HasPrefix(arg, "-format="):
			format = strings.TrimPrefix(arg, "-format=")
		default:
			filtered = append(filtered, arg)
		}
	}
	return filtered, format, nil
}

func newListFlagSet(name string, output io.Writer, params *annex.ListParams, updatedAfter *string, updatedBefore *string) *flag.FlagSet {
	fs := flag.NewFlagSet(name, flag.ContinueOnError)
	fs.SetOutput(output)
	fs.IntVar(&params.Page, "page", 0, "page number")
	fs.IntVar(&params.PageSize, "page-size", 0, "page size")
	fs.StringVar(updatedAfter, "updated-after", "", "updated after RFC3339 timestamp")
	fs.StringVar(updatedBefore, "updated-before", "", "updated before RFC3339 timestamp")
	return fs
}

func parseListTimes(params *annex.ListParams, updatedAfter string, updatedBefore string) error {
	var err error
	params.UpdatedAfter, err = parseOptionalTime(updatedAfter)
	if err != nil {
		return fmt.Errorf("parse --updated-after: %w", err)
	}
	params.UpdatedBefore, err = parseOptionalTime(updatedBefore)
	if err != nil {
		return fmt.Errorf("parse --updated-before: %w", err)
	}
	return nil
}

func parseOptionalTime(value string) (*time.Time, error) {
	if strings.TrimSpace(value) == "" {
		return nil, nil
	}
	parsed, err := time.Parse(time.RFC3339, value)
	if err != nil {
		return nil, err
	}
	return &parsed, nil
}

func (c Command) printTokenResponse(format string, response *annex.AuthTokenResponse, savedPath string) int {
	switch format {
	case "json":
		return c.printJSON(response)
	case "env":
		fmt.Fprintf(c.Stdout, "export LM_TOKEN=%s\n", shellQuote(response.AccessToken))
		if response.RefreshToken != "" {
			fmt.Fprintf(c.Stdout, "export LM_REFRESH_TOKEN=%s\n", shellQuote(response.RefreshToken))
		}
		if response.ProjectCode != "" {
			fmt.Fprintf(c.Stdout, "export LM_PROJECT_CODE=%s\n", shellQuote(response.ProjectCode))
		}
		return 0
	default:
		rows := [][]string{
			{"accessToken", maskToken(response.AccessToken)},
			{"tokenType", valueOrDash(response.TokenType)},
			{"expiresIn", strconv.Itoa(response.ExpiresIn)},
		}
		if response.RefreshToken != "" {
			rows = append(rows, []string{"refreshToken", maskToken(response.RefreshToken)})
		}
		if response.ProjectCode != "" {
			rows = append(rows, []string{"projectCode", response.ProjectCode})
		}
		if len(response.Scope) > 0 {
			rows = append(rows, []string{"scope", strings.Join(response.Scope, ",")})
		}
		if savedPath != "" {
			rows = append(rows, []string{"config", savedPath})
		}
		renderTable(c.Stdout, []string{"FIELD", "VALUE"}, rows)
		return 0
	}
}

func (c Command) printAuthSubject(format string, subject *annex.AuthSubject) int {
	if format == "json" {
		return c.printJSON(subject)
	}

	rows := [][]string{
		{"id", valueOrDash(subject.ID)},
		{"type", valueOrDash(subject.Type)},
		{"name", valueOrDash(subject.Name)},
		{"email", valueOrDash(subject.Email)},
		{"projectCode", valueOrDash(subject.ProjectCode)},
	}
	if len(subject.Scopes) > 0 {
		rows = append(rows, []string{"scopes", strings.Join(subject.Scopes, ",")})
	}
	if subject.ExpiresAt != nil {
		rows = append(rows, []string{"expiresAt", subject.ExpiresAt.Format(time.RFC3339)})
	}
	renderTable(c.Stdout, []string{"FIELD", "VALUE"}, rows)
	return 0
}

func (c Command) printDeviceList(format string, values []annex.Device) int {
	if format == "json" {
		return c.printJSON(values)
	}
	rows := make([][]string, 0, len(values))
	for _, value := range values {
		rows = append(rows, []string{
			valueOrDash(value.ID),
			valueOrDash(value.Name),
			valueOrDash(value.Type),
			valueOrDash(value.State),
			boolText(value.Online),
			valueOrDash(value.ProjectCode),
		})
	}
	renderTable(c.Stdout, []string{"ID", "NAME", "TYPE", "STATE", "ONLINE", "PROJECT"}, rows)
	return 0
}

func (c Command) printMissionList(format string, values []annex.Mission) int {
	if format == "json" {
		return c.printJSON(values)
	}
	rows := make([][]string, 0, len(values))
	for _, value := range values {
		rows = append(rows, []string{
			valueOrDash(value.ID),
			valueOrDash(value.Name),
			valueOrDash(value.Type),
			valueOrDash(value.State),
			valueOrDash(value.ProjectCode),
			formatTime(value.UpdatedAt),
		})
	}
	renderTable(c.Stdout, []string{"ID", "NAME", "TYPE", "STATE", "PROJECT", "UPDATED"}, rows)
	return 0
}

func (c Command) printRawDataList(format string, values []annex.RawData) int {
	if format == "json" {
		return c.printJSON(values)
	}
	rows := make([][]string, 0, len(values))
	for _, value := range values {
		rows = append(rows, []string{
			valueOrDash(value.ID),
			valueOrDash(value.Type),
			valueOrDash(value.DeviceID),
			valueOrDash(value.MissionID),
			formatSize(value.SizeBytes),
			valueOrDash(value.ProjectCode),
			formatTime(value.CreatedAt),
		})
	}
	renderTable(c.Stdout, []string{"ID", "TYPE", "DEVICE", "MISSION", "SIZE", "PROJECT", "CREATED"}, rows)
	return 0
}

func (c Command) printRuleHitList(format string, values []annex.RuleHit) int {
	if format == "json" {
		return c.printJSON(values)
	}
	rows := make([][]string, 0, len(values))
	for _, value := range values {
		rows = append(rows, []string{
			valueOrDash(value.ID),
			valueOrDash(value.RuleName),
			valueOrDash(value.Severity),
			valueOrDash(value.State),
			valueOrDash(value.DeviceID),
			valueOrDash(value.MissionID),
			formatTime(value.HitAt),
		})
	}
	renderTable(c.Stdout, []string{"ID", "RULE", "SEVERITY", "STATE", "DEVICE", "MISSION", "HIT_AT"}, rows)
	return 0
}

func renderTable(output io.Writer, headers []string, rows [][]string) {
	widths := make([]int, len(headers))
	cleanHeaders := normalizeRow(headers, len(headers))
	for i, header := range cleanHeaders {
		widths[i] = displayWidth(header)
	}

	cleanRows := make([][]string, 0, len(rows))
	for _, row := range rows {
		cleanRow := normalizeRow(row, len(headers))
		for i, value := range cleanRow {
			if width := displayWidth(value); width > widths[i] {
				widths[i] = width
			}
		}
		cleanRows = append(cleanRows, cleanRow)
	}

	writeBorder := func() {
		for _, width := range widths {
			fmt.Fprint(output, "+")
			fmt.Fprint(output, strings.Repeat("-", width+2))
		}
		fmt.Fprintln(output, "+")
	}
	writeRow := func(values []string) {
		for i, value := range values {
			fmt.Fprintf(output, "| %s%s ", value, strings.Repeat(" ", widths[i]-displayWidth(value)))
		}
		fmt.Fprintln(output, "|")
	}

	writeBorder()
	writeRow(cleanHeaders)
	writeBorder()
	for _, row := range cleanRows {
		writeRow(row)
	}
	writeBorder()
}

func normalizeRow(values []string, length int) []string {
	row := make([]string, length)
	for i := range row {
		if i < len(values) {
			row[i] = tableCell(values[i])
		}
	}
	return row
}

func tableCell(value string) string {
	value = strings.TrimSpace(value)
	value = strings.ReplaceAll(value, "\t", " ")
	value = strings.ReplaceAll(value, "\r", " ")
	value = strings.ReplaceAll(value, "\n", " ")
	if value == "" {
		return "-"
	}
	return value
}

func displayWidth(value string) int {
	width := 0
	for _, r := range value {
		switch {
		case r == 0 || r == '\t' || r == '\n' || r == '\r':
			continue
		case r < 0x20 || (r >= 0x7f && r < 0xa0):
			continue
		case r == 0x200d || unicode.Is(unicode.Mn, r) || unicode.Is(unicode.Me, r):
			continue
		case isWideRune(r):
			width += 2
		default:
			width++
		}
	}
	return width
}

func isWideRune(r rune) bool {
	return r >= 0x1100 && (r <= 0x115f ||
		r == 0x2329 ||
		r == 0x232a ||
		(r >= 0x2e80 && r <= 0xa4cf && r != 0x303f) ||
		(r >= 0xac00 && r <= 0xd7a3) ||
		(r >= 0xf900 && r <= 0xfaff) ||
		(r >= 0xfe10 && r <= 0xfe19) ||
		(r >= 0xfe30 && r <= 0xfe6f) ||
		(r >= 0xff00 && r <= 0xff60) ||
		(r >= 0xffe0 && r <= 0xffe6) ||
		(r >= 0x1f300 && r <= 0x1faff))
}

func (c Command) printJSON(value any) int {
	encoder := json.NewEncoder(c.Stdout)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(value); err != nil {
		return c.error(err)
	}
	return 0
}

func (c Command) printUsage() {
	fmt.Fprintln(c.Stdout, `Usage:
  lm [global flags] auth login --username <user> --password <password>
  lm [global flags] auth refresh
  lm [global flags] auth me
  lm [global flags] auth revoke
  lm [global flags] devices list [flags]
  lm [global flags] devices get <device-id>
  lm [global flags] missions list [flags]
  lm [global flags] missions get <mission-id>
  lm [global flags] raw-data list [flags]
  lm [global flags] raw-data get <raw-data-id>
  lm [global flags] rule-hits list [flags]
  lm [global flags] rule-hits get <rule-hit-id>
  lm serve [--addr :8080] [--path /lingmind/webhook]

Global flags:
  --base-url   Phoenix gateway base URL, or LM_BASE_URL
  --token      bearer token, or LM_TOKEN
  --api-key    API key, or LM_API_KEY
  --refresh-token
               refresh token, or LM_REFRESH_TOKEN
  --project    project code, or LM_PROJECT_CODE
  --format     json, table, or env; default json`)
}

func (c Command) usageError(message string) int {
	fmt.Fprintln(c.Stderr, message)
	return 2
}

func (c Command) error(err error) int {
	fmt.Fprintln(c.Stderr, err)
	return 1
}

func firstArg(args []string) (string, bool) {
	if len(args) == 0 || strings.TrimSpace(args[0]) == "" {
		return "", false
	}
	return args[0], true
}

func boolText(value bool) string {
	if value {
		return "yes"
	}
	return "no"
}

func formatTime(value time.Time) string {
	if value.IsZero() {
		return "-"
	}
	return value.Format(time.RFC3339)
}

func formatSize(value *int64) string {
	if value == nil {
		return "-"
	}
	return strconv.FormatInt(*value, 10)
}

func valueOrDash(value string) string {
	if strings.TrimSpace(value) == "" {
		return "-"
	}
	return value
}

func maskToken(value string) string {
	if value == "" {
		return "-"
	}
	if len(value) <= 12 {
		return "****"
	}
	return value[:6] + "..." + value[len(value)-4:]
}

func shellQuote(value string) string {
	return "'" + strings.ReplaceAll(value, "'", "'\"'\"'") + "'"
}
