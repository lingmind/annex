#!/usr/bin/env python3
"""Generate Annex tool-map snapshots from the Phoenix and Apex source contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE = ROOT.parent
STANDARD_OUTPUT = ROOT / "metadata" / "lingmind-capability-tool-map.v1.json"
OPERATOR_OUTPUT = ROOT / "metadata" / "lingmind-operator-capability-tool-map.v1.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--check", action="store_true", help="Fail when checked-in snapshots differ from source")
    return parser.parse_args()


def run(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed in {cwd}: {' '.join(command)}\n{completed.stdout}{completed.stderr}"
        )
    return completed.stdout + completed.stderr


def quoted_strings(text: str) -> list[str]:
    return re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', text)


def extract_standard_tools(phoenix: Path) -> list[str]:
    output = run(
        [
            "go",
            "test",
            "-count=1",
            "-run",
            "^TestEveryBusinessCapabilityHasExecutableAuthorizationContract$",
            "-v",
            "./internal/mcpserver",
        ],
        phoenix,
    )
    prefix = "=== RUN   TestEveryBusinessCapabilityHasExecutableAuthorizationContract/"
    executable = {line[len(prefix) :].strip() for line in output.splitlines() if line.startswith(prefix)}
    if not executable:
        raise RuntimeError("Phoenix capability contract test did not enumerate any executable tools")

    context: set[str] = set()
    for path in (phoenix / "internal" / "mcpserver").glob("*.go"):
        if path.name.endswith("_test.go"):
            continue
        for block in path.read_text(encoding="utf-8").split("Capability{")[1:]:
            if "ActionContext" not in block:
                continue
            match = re.search(r'ToolName:\s*"([a-z0-9_]+)"', block)
            if match:
                context.add(match.group(1))
    if not context:
        raise RuntimeError("Phoenix source did not expose any context tools")
    return sorted(executable | context)


def extract_business_permissions(phoenix: Path) -> list[str]:
    source = (phoenix / "internal" / "mcpserver" / "permission_inventory.go").read_text(encoding="utf-8")
    match = re.search(r"businessPermissionInventory\s*=\s*\[\]string\s*\{(.*?)\n\}", source, re.DOTALL)
    if not match:
        raise RuntimeError("cannot locate Phoenix businessPermissionInventory")
    permissions = sorted(set(quoted_strings(match.group(1))))
    if not permissions:
        raise RuntimeError("Phoenix businessPermissionInventory is empty")
    return permissions


def extract_standard_release_gate(phoenix: Path) -> dict[str, Any]:
    source = (phoenix / "internal" / "mcpserver" / "capability_registry.go").read_text(encoding="utf-8")
    function = re.search(
        r"func \(r \*CapabilityRegistry\) CoverageReport\([^)]*\) CoverageReport \{(.*?)\n\}",
        source,
        re.DOTALL,
    )
    if not function:
        raise RuntimeError("cannot locate Phoenix CapabilityRegistry.CoverageReport")
    stage = re.search(r'Stage:\s*"([a-z0-9_]+)"', function.group(1))
    ready = re.search(r"PublicReleaseReady:\s*(true|false)", function.group(1))
    write_gate = re.search(r'WriteReleaseGate:\s*"([a-z0-9_]+)"', function.group(1))
    if not stage or not ready or not write_gate:
        raise RuntimeError("cannot extract Phoenix CapabilityRegistry release gate")
    return {
        "stage": stage.group(1),
        "publicReleaseReady": ready.group(1) == "true",
        "writeReleaseGate": write_gate.group(1),
    }


def extract_operator_tools(apex: Path) -> list[str]:
    source = (apex / "internal" / "operator" / "mcp_handler.go").read_text(encoding="utf-8")
    match = re.search(r"func operatorTools\(\) \[\]gin\.H \{(.*)\n\}", source, re.DOTALL)
    if not match:
        raise RuntimeError("cannot locate Apex operatorTools")
    tools = re.findall(r'operatorTool\("([a-z0-9_]+)"', match.group(1))
    if not tools or len(tools) != len(set(tools)):
        raise RuntimeError("Apex operatorTools is empty or contains duplicate names")
    return sorted(tools)


def extract_operator_scopes(apex: Path) -> list[str]:
    source = (apex / "internal" / "operator" / "routes.go").read_text(encoding="utf-8")
    scopes = set(re.findall(r'=\s*"(apex\.[a-z.]+)"', source))
    if not scopes:
        raise RuntimeError("cannot locate Apex Operator OAuth scopes")
    return ["openid", *sorted(scopes)]


def fingerprint(values: list[str]) -> str:
    return "sha256:" + hashlib.sha256(("\n".join(values) + "\n").encode()).hexdigest()


def standard_domain(tool: str) -> str:
    if tool in {"environment_context_get", "projects_list", "profile_get", "profile_update_self", "business_operation_get", "business_action_plan_get", "business_action_plan_cancel"}:
        return "context-and-profile"
    if tool.startswith(("missions_", "waylines_", "in_flight_", "trajectories_")):
        return "missions-and-waylines"
    if tool.startswith(("devices_", "streams_", "stream_", "camera_", "uav_", "nvr_", "led_", "robot_", "speaker_audios_", "resource_shares_")):
        return "devices-media-and-controls"
    if tool.startswith(("alerts_", "events_", "incidents_", "notifications_", "rule_hits_")):
        return "events-and-response"
    if tool.startswith(("ai_models_", "detection_", "inference_", "observations_")):
        return "ai-and-detection"
    if tool.startswith(("data_process", "data_processors_", "schedules_", "schedule_executions_")):
        return "processing-and-schedules"
    if tool.startswith(("raw_data_", "raw_notes_", "spacetime_", "spatial_", "areas_", "landmarks_", "lines_")):
        return "data-and-spatial"
    if tool.startswith(("aerial_videos_", "orthophotos_", "photogrammetry_", "point_clouds_", "reality_models_", "viewpoints_", "camera_calibrations_")):
        return "survey-products"
    return "reports-network-and-other"


def standard_action(tool: str, all_tools: set[str]) -> str:
    if tool in {"projects_list", "business_operation_get", "business_action_plan_get", "business_action_plan_cancel"}:
        return "context"
    if tool.endswith("_plan") or (tool.endswith("_execute") and tool.removesuffix("_execute") + "_plan" in all_tools):
        return "plan-confirm-execute"
    if tool.endswith(("_list", "_get", "_stats", "_status")) or tool in {"nvr_probe", "led_ping", "spacetime_search"}:
        return "read"
    if tool.startswith("raw_data_exports_") or tool in {"data_processes_execute", "data_processes_stop"}:
        return "async-job"
    return "direct-write-or-execute"


def grouped(tools: list[str], classifier: Any) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = {}
    for tool in tools:
        groups.setdefault(classifier(tool), []).append(tool)
    return [{"name": name, "tools": groups[name]} for name in sorted(groups)]


def operator_domain(tool: str) -> str:
    if tool.startswith(("environment", "operator_capabilities")):
        return "environment-discovery"
    if tool.startswith("grant"):
        return "grant-administration"
    if tool.startswith("operator_"):
        return "plan-lifecycle"
    if tool.startswith("k8s_") or tool.startswith("service_status") or tool.startswith("service_diagnostics"):
        return "agent-backed-observe-maintain"
    if tool.startswith("service_"):
        return "service-deployment"
    if tool.startswith(("backup_", "restore_")):
        return "backup-and-restore"
    return "other"


def build_standard(phoenix: Path) -> dict[str, Any]:
    tools = extract_standard_tools(phoenix)
    permissions = extract_business_permissions(phoenix)
    release_gate = extract_standard_release_gate(phoenix)
    all_tools = set(tools)
    return {
        "schemaVersion": "2.0.0",
        "registry": {
            "name": "CapabilityRegistry",
            "service": "phoenix",
            "toolCount": len(tools),
            "businessPermissionCount": len(permissions),
            "primaryPermissionsCovered": len(permissions),
            "releaseStage": release_gate["stage"],
            "publicReleaseReady": release_gate["publicReleaseReady"],
            "productionReady": release_gate["publicReleaseReady"],
            "writeReleaseGate": release_gate["writeReleaseGate"],
        },
        "generatedFrom": {
            "toolContract": "phoenix/internal/mcpserver/capability_registry_test.go#TestEveryBusinessCapabilityHasExecutableAuthorizationContract",
            "permissionContract": "phoenix/internal/mcpserver/permission_inventory.go#businessPermissionInventory",
            "releaseContract": "phoenix/internal/mcpserver/capability_registry.go#CapabilityRegistry.CoverageReport",
            "fingerprint": fingerprint(tools + permissions + [json.dumps(release_gate, sort_keys=True)]),
        },
        "oauthScopes": ["openid", "lingmind.read", "lingmind.write", "lingmind.execute"],
        "domainGroups": grouped(tools, standard_domain),
        "actionGroups": grouped(tools, lambda tool: standard_action(tool, all_tools)),
        "businessPermissions": permissions,
        "safetyContracts": {
            "projectScoped": True,
            "fixedTypedToolsOnly": True,
            "genericTransportExposed": False,
            "durableOperations": True,
            "optimisticConcurrencyForVersionedWrites": True,
            "oneTimePlansForDestructiveOrPhysicalActions": True,
            "acceptsTokenCredentialUrlOrPathInputs": False,
            "runtimeRegistryIsAuthoritative": True,
        },
    }


def build_operator(apex: Path) -> dict[str, Any]:
    tools = extract_operator_tools(apex)
    return {
        "schemaVersion": "2.0.0",
        "registry": {
            "name": "CapabilityRegistry",
            "service": "apex",
            "toolCount": len(tools),
            "connectionCardinality": "single-global-control-plane",
            "releaseStage": "sandbox-development",
            "productionReady": False,
        },
        "generatedFrom": {
            "toolContract": "apex/internal/operator/mcp_handler.go#operatorTools",
            "fingerprint": fingerprint(tools),
        },
        "oauthScopes": extract_operator_scopes(apex),
        "toolGroups": grouped(tools, operator_domain),
        "safetyContracts": {
            "explicitEnvironmentIdPerTargetCall": True,
            "agentOnlyEnvironmentAccess": True,
            "directClusterFallback": False,
            "grantAndAllowlistEnforced": True,
            "mongoPersistedPlans": True,
            "planCancelAndRetention": True,
            "genericTransportExposed": False,
        },
    }


def serialized(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    args = parse_args()
    workspace = args.workspace.resolve()
    outputs = {
        STANDARD_OUTPUT: serialized(build_standard(workspace / "phoenix")),
        OPERATOR_OUTPUT: serialized(build_operator(workspace / "apex")),
    }
    drifted: list[Path] = []
    for path, content in outputs.items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                drifted.append(path.relative_to(ROOT))
        else:
            path.write_text(content, encoding="utf-8")
            print(f"updated {path.relative_to(ROOT)}")
    if drifted:
        print("tool-map drift: " + ", ".join(map(str, drifted)), file=sys.stderr)
        print("run: make sync-plugin-tool-maps", file=sys.stderr)
        return 1
    if args.check:
        print("Agent tool maps match Phoenix and Apex source contracts")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"tool-map sync failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
