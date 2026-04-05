import { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  IconShield, IconRefresh, IconPlus, IconX, IconTrash,
  IconChevronDown, IconChevronRight, IconClock, IconSave, IconAlertCircle,
} from "../icons";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

type SecurityViewProps = {
  apiBaseUrl: string;
  serviceRunning: boolean;
};

type ZoneConfig = {
  workspace: string[];
  controlled: string[];
  protected: string[];
  forbidden: string[];
  default_zone?: string;
};

type CommandConfig = {
  custom_critical: string[];
  custom_high: string[];
  excluded_patterns: string[];
  blocked_commands: string[];
};

type SandboxConfig = {
  enabled: boolean;
  backend: string;
  sandbox_risk_levels: string[];
  exempt_commands: string[];
};

type AuditEntry = {
  ts: number;
  tool: string;
  decision: string;
  reason: string;
  policy: string;
};

type CheckpointEntry = {
  checkpoint_id: string;
  timestamp: number;
  tool_name: string;
  description: string;
  file_count: number;
};

const ZONE_META: Record<string, { color: string }> = {
  workspace: { color: "#22c55e" },
  controlled: { color: "#3b82f6" },
  protected: { color: "#f59e0b" },
  forbidden: { color: "#ef4444" },
};

const BACKEND_OPTIONS = [
  { value: "auto", label: "Auto" },
  { value: "low_integrity", label: "Low Integrity (Windows)" },
  { value: "bubblewrap", label: "Bubblewrap (Linux)" },
  { value: "seatbelt", label: "Seatbelt (macOS)" },
  { value: "docker", label: "Docker" },
  { value: "none", label: "None (Disabled)" },
];

type TabId = "zones" | "commands" | "sandbox" | "audit" | "checkpoints";

export default function SecurityView({ apiBaseUrl, serviceRunning }: SecurityViewProps) {
  const { t } = useTranslation();

  const [tab, setTab] = useState<TabId>("zones");
  const [zones, setZones] = useState<ZoneConfig>({ workspace: [], controlled: [], protected: [], forbidden: [] });
  const [commands, setCommands] = useState<CommandConfig>({ custom_critical: [], custom_high: [], excluded_patterns: [], blocked_commands: [] });
  const [sandbox, setSandbox] = useState<SandboxConfig>({ enabled: true, backend: "auto", sandbox_risk_levels: ["HIGH"], exempt_commands: [] });
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [checkpoints, setCheckpoints] = useState<CheckpointEntry[]>([]);
  const [saving, setSaving] = useState(false);

  const api = useCallback(async (path: string, method = "GET", body?: unknown) => {
    const opts: RequestInit = { method, headers: { "Content-Type": "application/json" } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${apiBaseUrl}${path}`, opts);
    return res.json();
  }, [apiBaseUrl]);

  const load = useCallback(async () => {
    if (!serviceRunning) return;
    try {
      const [zRes, cRes, sRes] = await Promise.all([
        api("/api/config/security/zones"),
        api("/api/config/security/commands"),
        api("/api/config/security/sandbox"),
      ]);
      setZones(zRes);
      setCommands(cRes);
      setSandbox(sRes);
    } catch { /* ignore */ }
  }, [api, serviceRunning]);

  useEffect(() => { load(); }, [load]);

  const loadAudit = useCallback(async () => {
    if (!serviceRunning) return;
    try {
      const res = await api("/api/config/security/audit");
      setAudit(res.entries || []);
    } catch { /* ignore */ }
  }, [api, serviceRunning]);

  const loadCheckpoints = useCallback(async () => {
    if (!serviceRunning) return;
    try {
      const res = await api("/api/config/security/checkpoints");
      setCheckpoints(res.checkpoints || []);
    } catch { /* ignore */ }
  }, [api, serviceRunning]);

  useEffect(() => {
    if (tab === "audit") loadAudit();
    if (tab === "checkpoints") loadCheckpoints();
  }, [tab, loadAudit, loadCheckpoints]);

  const doSave = async (endpoint: string, body: unknown, successKey: string) => {
    setSaving(true);
    try {
      await api(endpoint, "POST", body);
      toast.success(t(`security.${successKey}`));
    } catch {
      toast.error(t("security.saveFailed"));
    }
    setSaving(false);
  };

  const rewindCheckpoint = async (id: string) => {
    if (!confirm(t("security.rewindConfirm", { id }))) return;
    try {
      await api("/api/config/security/checkpoint/rewind", "POST", { checkpoint_id: id });
      toast.success(t("security.rewound"));
      loadCheckpoints();
    } catch { /* ignore */ }
  };

  if (!serviceRunning) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
        <IconAlertCircle size={32} className="mb-3 opacity-50" />
        <p className="text-sm">{t("security.backendOff")}</p>
      </div>
    );
  }

  const TABS: { id: TabId; labelKey: string }[] = [
    { id: "zones", labelKey: "security.zones" },
    { id: "commands", labelKey: "security.commands" },
    { id: "sandbox", labelKey: "security.sandbox" },
    { id: "audit", labelKey: "security.audit" },
    { id: "checkpoints", labelKey: "security.checkpoints" },
  ];

  return (
    <div className="mx-auto max-w-[900px]">
      <div className="mb-4">
        <h2 className="text-lg font-semibold">{t("security.title")}</h2>
        <p className="text-sm text-muted-foreground">{t("security.desc")}</p>
      </div>

      {/* Tab bar */}
      <div style={{ display: "flex", borderBottom: "1px solid var(--line)", marginBottom: 16 }}>
        {TABS.map((tb) => {
          const active = tab === tb.id;
          return (
            <button
              key={tb.id}
              onClick={() => setTab(tb.id)}
              className="text-sm font-medium transition-colors"
              style={{
                padding: "8px 16px",
                borderBottom: active ? "2px solid var(--accent, #3b82f6)" : "2px solid transparent",
                color: active ? "var(--accent, #3b82f6)" : "var(--muted)",
                marginBottom: -1,
                background: "none",
                border: "none",
                borderBottomWidth: 2,
                borderBottomStyle: "solid",
                borderBottomColor: active ? "var(--accent, #3b82f6)" : "transparent",
                cursor: "pointer",
              }}
            >
              {t(tb.labelKey)}
            </button>
          );
        })}
      </div>

      {/* Zones */}
      {tab === "zones" && (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">{t("security.zonesDesc")}</p>
          {(["workspace", "controlled", "protected", "forbidden"] as const).map((zone) => (
            <ZonePanel
              key={zone}
              zone={zone}
              color={ZONE_META[zone].color}
              paths={zones[zone] || []}
              onChange={(paths) => setZones((prev) => ({ ...prev, [zone]: paths }))}
            />
          ))}
          <Button onClick={() => doSave("/api/config/security/zones", zones, "zonesSaved")} disabled={saving}>
            {saving ? <Loader2 className="size-4 animate-spin" /> : <IconSave size={14} />}
            {t("security.save")}
          </Button>
        </div>
      )}

      {/* Commands */}
      {tab === "commands" && (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">{t("security.commandsDesc")}</p>
          <TagEditor
            label={t("security.criticalPatterns")}
            items={commands.custom_critical}
            onChange={(v) => setCommands((p) => ({ ...p, custom_critical: v }))}
            placeholder={`e.g. rm\\s+-rf\\s+/`}
          />
          <TagEditor
            label={t("security.highPatterns")}
            items={commands.custom_high}
            onChange={(v) => setCommands((p) => ({ ...p, custom_high: v }))}
            placeholder="e.g. Remove-Item.*-Recurse"
          />
          <TagEditor
            label={t("security.excludedPatterns")}
            items={commands.excluded_patterns}
            onChange={(v) => setCommands((p) => ({ ...p, excluded_patterns: v }))}
            placeholder={t("security.excludedPh")}
          />
          <TagEditor
            label={t("security.blockedCommands")}
            items={commands.blocked_commands}
            onChange={(v) => setCommands((p) => ({ ...p, blocked_commands: v }))}
            placeholder="e.g. diskpart"
          />
          <Button onClick={() => doSave("/api/config/security/commands", commands, "commandsSaved")} disabled={saving}>
            {saving ? <Loader2 className="size-4 animate-spin" /> : <IconSave size={14} />}
            {t("security.save")}
          </Button>
        </div>
      )}

      {/* Sandbox */}
      {tab === "sandbox" && (
        <div className="space-y-5">
          <p className="text-sm text-muted-foreground">{t("security.sandboxDesc")}</p>
          <div className="flex items-center gap-3">
            <Switch
              checked={sandbox.enabled}
              onCheckedChange={(v) => setSandbox((p) => ({ ...p, enabled: v }))}
            />
            <Label className="text-sm">{t("security.sandboxEnabled")}</Label>
          </div>
          <div className="space-y-1.5">
            <Label className="text-sm">{t("security.sandboxBackend")}</Label>
            <Select
              value={sandbox.backend}
              onValueChange={(v) => setSandbox((p) => ({ ...p, backend: v }))}
            >
              <SelectTrigger className="w-[260px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {BACKEND_OPTIONS.map((o) => (
                  <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button onClick={() => doSave("/api/config/security/sandbox", sandbox, "sandboxSaved")} disabled={saving}>
            {saving ? <Loader2 className="size-4 animate-spin" /> : <IconSave size={14} />}
            {t("security.save")}
          </Button>
        </div>
      )}

      {/* Audit */}
      {tab === "audit" && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              {t("security.auditCount", { count: audit.length })}
            </span>
            <Button variant="outline" size="sm" onClick={loadAudit}>
              <IconRefresh size={14} /> {t("security.refresh")}
            </Button>
          </div>
          {audit.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground text-sm">
              <IconShield size={28} className="mx-auto mb-2 opacity-30" />
              {t("security.noAudit")}
            </div>
          ) : (
            <div className="rounded-md border max-h-[420px] overflow-auto">
              {[...audit].reverse().map((e, i) => (
                <div key={i} className="flex items-start gap-2.5 px-3 py-2.5 border-b last:border-b-0 text-sm">
                  <DecisionBadge decision={e.decision} />
                  <div className="flex-1 min-w-0">
                    <span className="font-medium">{e.tool}</span>
                    <span className="ml-2 text-muted-foreground text-xs">{e.reason}</span>
                  </div>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {new Date(e.ts * 1000).toLocaleTimeString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Checkpoints */}
      {tab === "checkpoints" && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              {t("security.checkpointCount", { count: checkpoints.length })}
            </span>
            <Button variant="outline" size="sm" onClick={loadCheckpoints}>
              <IconRefresh size={14} /> {t("security.refresh")}
            </Button>
          </div>
          {checkpoints.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground text-sm">
              <IconClock size={28} className="mx-auto mb-2 opacity-30" />
              {t("security.noCheckpoints")}
            </div>
          ) : (
            <div className="rounded-md border">
              {checkpoints.map((cp) => (
                <div key={cp.checkpoint_id} className="flex items-center gap-3 px-3 py-2.5 border-b last:border-b-0">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium font-mono truncate">{cp.checkpoint_id}</div>
                    <div className="text-xs text-muted-foreground">
                      {cp.tool_name} — {cp.file_count} {t("security.files")}
                      <span className="ml-2">{new Date(cp.timestamp * 1000).toLocaleString()}</span>
                    </div>
                  </div>
                  <Button variant="outline" size="xs" onClick={() => rewindCheckpoint(cp.checkpoint_id)}>
                    {t("security.rewind")}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ─── Sub-components ─── */

function DecisionBadge({ decision }: { decision: string }) {
  const variant = decision === "deny" ? "destructive" : decision === "confirm" ? "outline" : "secondary";
  return (
    <Badge variant={variant} className="text-[11px] uppercase shrink-0">
      {decision}
    </Badge>
  );
}

function ZonePanel({ zone, color, paths, onChange }: {
  zone: string; color: string;
  paths: string[]; onChange: (v: string[]) => void;
}) {
  const { t } = useTranslation();
  const [input, setInput] = useState("");
  const [expanded, setExpanded] = useState(zone === "workspace" || zone === "controlled");

  const add = () => {
    const v = input.trim();
    if (v && !paths.includes(v)) onChange([...paths, v]);
    setInput("");
  };

  return (
    <div className="rounded-lg border overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left hover:bg-accent/50 transition-colors"
      >
        <span className="size-2.5 rounded-full shrink-0" style={{ background: color }} />
        <span className="flex-1 text-sm font-semibold">{t(`security.zone_${zone}`)}</span>
        <span className="text-xs text-muted-foreground">{paths.length}</span>
        {expanded ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />}
      </button>
      {expanded && (
        <div className="px-3.5 pb-3 pt-1 space-y-1.5">
          {paths.map((p, i) => (
            <div key={i} className="flex items-center gap-1.5 group">
              <code className="flex-1 text-xs px-2 py-1 bg-muted rounded">{p}</code>
              <Button
                variant="ghost" size="icon-xs"
                className="opacity-0 group-hover:opacity-100 text-destructive"
                onClick={() => onChange(paths.filter((_, j) => j !== i))}
              >
                <IconX size={12} />
              </Button>
            </div>
          ))}
          <div className="flex gap-1.5 mt-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && add()}
              placeholder="D:/path/to/dir/**"
              className="h-7 text-xs"
            />
            <Button variant="outline" size="xs" onClick={add}>
              <IconPlus size={12} />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

function TagEditor({ label, items, onChange, placeholder }: {
  label: string; items: string[]; onChange: (v: string[]) => void; placeholder?: string;
}) {
  const [input, setInput] = useState("");

  const add = () => {
    const v = input.trim();
    if (v && !items.includes(v)) onChange([...items, v]);
    setInput("");
  };

  return (
    <div className="space-y-2">
      <Label className="text-sm">{label}</Label>
      {items.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {items.map((item, i) => (
            <Badge key={i} variant="secondary" className="gap-1 pr-1 font-mono text-xs">
              {item}
              <button
                onClick={() => onChange(items.filter((_, j) => j !== i))}
                className="ml-0.5 rounded-sm hover:bg-destructive/20 transition-colors"
              >
                <IconX size={10} className="text-muted-foreground hover:text-destructive" />
              </button>
            </Badge>
          ))}
        </div>
      )}
      <div className="flex gap-1.5">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder={placeholder}
          className="h-8 text-xs"
        />
        <Button variant="outline" size="sm" onClick={add}>
          <IconPlus size={12} />
        </Button>
      </div>
    </div>
  );
}
