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
	"strconv"
	"strings"
	"text/tabwriter"
	"time"

	"github.com/lingmind/annex/pkg/annex"
	"github.com/lingmind/annex/pkg/webhook"
)

type Command struct {
	Stdout io.Writer
	Stderr io.Writer
	Env    func(string) string
}

type globalOptions struct {
	baseURL     string
	token       string
	apiKey      string
	projectCode string
	format      string
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
	opts := globalOptions{
		baseURL:     c.Env("LM_BASE_URL"),
		token:       c.Env("LM_TOKEN"),
		apiKey:      c.Env("LM_API_KEY"),
		projectCode: c.Env("LM_PROJECT_CODE"),
		format:      "table",
	}

	fs := flag.NewFlagSet("lm", flag.ContinueOnError)
	fs.SetOutput(c.Stderr)
	fs.StringVar(&opts.baseURL, "base-url", opts.baseURL, "Annex API base URL")
	fs.StringVar(&opts.token, "token", opts.token, "Bearer token")
	fs.StringVar(&opts.apiKey, "api-key", opts.apiKey, "API key")
	fs.StringVar(&opts.projectCode, "project", opts.projectCode, "project code")
	fs.StringVar(&opts.format, "format", opts.format, "output format: table or json")
	if err := fs.Parse(args); err != nil {
		return opts, nil, err
	}
	return opts, fs.Args(), nil
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
		params, err := parseDeviceListFlags(args[1:], c.Stderr)
		if err != nil {
			return c.error(err)
		}
		resp, err := client.ListDevices(ctx, params)
		if err != nil {
			return c.error(err)
		}
		return c.printDeviceList(global.format, resp.Data)
	case "get":
		id, ok := firstArg(args[1:])
		if !ok {
			return c.usageError("devices get requires <device-id>")
		}
		resp, err := client.GetDevice(ctx, id)
		if err != nil {
			return c.error(err)
		}
		return c.printDeviceList(global.format, []annex.Device{*resp})
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
		params, err := parseMissionListFlags(args[1:], c.Stderr)
		if err != nil {
			return c.error(err)
		}
		resp, err := client.ListMissions(ctx, params)
		if err != nil {
			return c.error(err)
		}
		return c.printMissionList(global.format, resp.Data)
	case "get":
		id, ok := firstArg(args[1:])
		if !ok {
			return c.usageError("missions get requires <mission-id>")
		}
		resp, err := client.GetMission(ctx, id)
		if err != nil {
			return c.error(err)
		}
		return c.printMissionList(global.format, []annex.Mission{*resp})
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
		params, err := parseRawDataListFlags(args[1:], c.Stderr)
		if err != nil {
			return c.error(err)
		}
		resp, err := client.ListRawData(ctx, params)
		if err != nil {
			return c.error(err)
		}
		return c.printRawDataList(global.format, resp.Data)
	case "get":
		id, ok := firstArg(args[1:])
		if !ok {
			return c.usageError("raw-data get requires <raw-data-id>")
		}
		resp, err := client.GetRawData(ctx, id)
		if err != nil {
			return c.error(err)
		}
		return c.printRawDataList(global.format, []annex.RawData{*resp})
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
		params, err := parseRuleHitListFlags(args[1:], c.Stderr)
		if err != nil {
			return c.error(err)
		}
		resp, err := client.ListRuleHits(ctx, params)
		if err != nil {
			return c.error(err)
		}
		return c.printRuleHitList(global.format, resp.Data)
	case "get":
		id, ok := firstArg(args[1:])
		if !ok {
			return c.usageError("rule-hits get requires <rule-hit-id>")
		}
		resp, err := client.GetRuleHit(ctx, id)
		if err != nil {
			return c.error(err)
		}
		return c.printRuleHitList(global.format, []annex.RuleHit{*resp})
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

func parseDeviceListFlags(args []string, output io.Writer) (annex.ListDevicesParams, error) {
	var params annex.ListDevicesParams
	var updatedAfter, updatedBefore string
	fs := newListFlagSet("devices list", output, &params.ListParams, &updatedAfter, &updatedBefore)
	fs.StringVar(&params.State, "state", "", "device state")
	fs.StringVar(&params.Type, "type", "", "device type")
	if err := fs.Parse(args); err != nil {
		return params, err
	}
	return params, parseListTimes(&params.ListParams, updatedAfter, updatedBefore)
}

func parseMissionListFlags(args []string, output io.Writer) (annex.ListMissionsParams, error) {
	var params annex.ListMissionsParams
	var updatedAfter, updatedBefore string
	fs := newListFlagSet("missions list", output, &params.ListParams, &updatedAfter, &updatedBefore)
	fs.StringVar(&params.State, "state", "", "mission state")
	fs.StringVar(&params.Type, "type", "", "mission type")
	fs.StringVar(&params.DeviceID, "device-id", "", "device ID")
	if err := fs.Parse(args); err != nil {
		return params, err
	}
	return params, parseListTimes(&params.ListParams, updatedAfter, updatedBefore)
}

func parseRawDataListFlags(args []string, output io.Writer) (annex.ListRawDataParams, error) {
	var params annex.ListRawDataParams
	var updatedAfter, updatedBefore string
	fs := newListFlagSet("raw-data list", output, &params.ListParams, &updatedAfter, &updatedBefore)
	fs.StringVar(&params.Type, "type", "", "raw data type")
	fs.StringVar(&params.MissionID, "mission-id", "", "mission ID")
	fs.StringVar(&params.DeviceID, "device-id", "", "device ID")
	var capturedAfter, capturedBefore string
	fs.StringVar(&capturedAfter, "captured-after", "", "captured after RFC3339 timestamp")
	fs.StringVar(&capturedBefore, "captured-before", "", "captured before RFC3339 timestamp")
	if err := fs.Parse(args); err != nil {
		return params, err
	}
	if err := parseListTimes(&params.ListParams, updatedAfter, updatedBefore); err != nil {
		return params, err
	}
	var err error
	params.CapturedAfter, err = parseOptionalTime(capturedAfter)
	if err != nil {
		return params, fmt.Errorf("parse --captured-after: %w", err)
	}
	params.CapturedBefore, err = parseOptionalTime(capturedBefore)
	if err != nil {
		return params, fmt.Errorf("parse --captured-before: %w", err)
	}
	return params, nil
}

func parseRuleHitListFlags(args []string, output io.Writer) (annex.ListRuleHitsParams, error) {
	var params annex.ListRuleHitsParams
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
		return params, err
	}
	if err := parseListTimes(&params.ListParams, updatedAfter, updatedBefore); err != nil {
		return params, err
	}
	var err error
	params.HitAfter, err = parseOptionalTime(hitAfter)
	if err != nil {
		return params, fmt.Errorf("parse --hit-after: %w", err)
	}
	params.HitBefore, err = parseOptionalTime(hitBefore)
	if err != nil {
		return params, fmt.Errorf("parse --hit-before: %w", err)
	}
	return params, nil
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

func (c Command) printDeviceList(format string, values []annex.Device) int {
	if format == "json" {
		return c.printJSON(values)
	}
	tw := tabwriter.NewWriter(c.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(tw, "ID\tNAME\tTYPE\tSTATE\tONLINE\tPROJECT")
	for _, value := range values {
		fmt.Fprintf(tw, "%s\t%s\t%s\t%s\t%s\t%s\n", value.ID, value.Name, value.Type, value.State, boolText(value.Online), value.ProjectCode)
	}
	_ = tw.Flush()
	return 0
}

func (c Command) printMissionList(format string, values []annex.Mission) int {
	if format == "json" {
		return c.printJSON(values)
	}
	tw := tabwriter.NewWriter(c.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(tw, "ID\tNAME\tTYPE\tSTATE\tPROJECT\tUPDATED")
	for _, value := range values {
		fmt.Fprintf(tw, "%s\t%s\t%s\t%s\t%s\t%s\n", value.ID, value.Name, value.Type, value.State, value.ProjectCode, formatTime(value.UpdatedAt))
	}
	_ = tw.Flush()
	return 0
}

func (c Command) printRawDataList(format string, values []annex.RawData) int {
	if format == "json" {
		return c.printJSON(values)
	}
	tw := tabwriter.NewWriter(c.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(tw, "ID\tTYPE\tDEVICE\tMISSION\tSIZE\tPROJECT\tCREATED")
	for _, value := range values {
		fmt.Fprintf(tw, "%s\t%s\t%s\t%s\t%s\t%s\t%s\n", value.ID, value.Type, value.DeviceID, value.MissionID, formatSize(value.SizeBytes), value.ProjectCode, formatTime(value.CreatedAt))
	}
	_ = tw.Flush()
	return 0
}

func (c Command) printRuleHitList(format string, values []annex.RuleHit) int {
	if format == "json" {
		return c.printJSON(values)
	}
	tw := tabwriter.NewWriter(c.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(tw, "ID\tRULE\tSEVERITY\tSTATE\tDEVICE\tMISSION\tHIT_AT")
	for _, value := range values {
		fmt.Fprintf(tw, "%s\t%s\t%s\t%s\t%s\t%s\t%s\n", value.ID, value.RuleName, value.Severity, value.State, value.DeviceID, value.MissionID, formatTime(value.HitAt))
	}
	_ = tw.Flush()
	return 0
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
  --base-url   Annex API base URL, or LM_BASE_URL
  --token      bearer token, or LM_TOKEN
  --api-key    API key, or LM_API_KEY
  --project    project code, or LM_PROJECT_CODE
  --format     table or json`)
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
