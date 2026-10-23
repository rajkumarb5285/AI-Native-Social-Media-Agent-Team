"use client";

import * as React from "react";
import { CheckCircle2, Clock, AlertCircle, ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

export interface AgentCardProps {
  id: string;
  name: string;
  role: string;
  avatarIcon: string;
  status: "idle" | "working" | "waiting" | "done" | "error";
  taskSummary: string;
  progressPercent?: number;
  outputPreview?: string;
  sourceFactVerified?: string;
}

export function AgentCard({
  name,
  role,
  avatarIcon,
  status,
  taskSummary,
  progressPercent,
  outputPreview,
  sourceFactVerified,
}: AgentCardProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  const statusConfig = {
    done: {
      badge: "Completed",
      badgeClass: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
      dot: "bg-emerald-500",
      icon: CheckCircle2,
    },
    working: {
      badge: "Active",
      badgeClass: "bg-amber-500/15 text-amber-400 border-amber-500/30",
      dot: "bg-amber-500 animate-pulse",
      icon: Sparkles,
    },
    waiting: {
      badge: "Waiting",
      badgeClass: "bg-stone-500/15 text-stone-400 border-stone-500/30",
      dot: "bg-stone-500",
      icon: Clock,
    },
    idle: {
      badge: "Idle",
      badgeClass: "bg-stone-800 text-stone-400 border-stone-700",
      dot: "bg-stone-600",
      icon: Clock,
    },
    error: {
      badge: "Blocked",
      badgeClass: "bg-rose-500/15 text-rose-400 border-rose-500/30",
      dot: "bg-rose-500",
      icon: AlertCircle,
    },
  };

  const currentStatus = statusConfig[status];

  return (
    <div className="relative rounded-2xl bg-[#1A1816] border border-white/[0.08] p-4.5 hover:border-white/15 transition-all shadow-sm">
      <div className="flex items-start justify-between gap-3">
        {/* Avatar & Role Info */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-stone-900 border border-white/10 flex items-center justify-center text-lg select-none">
            {avatarIcon}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-stone-100 text-sm">{name}</span>
              <span className="text-xs text-stone-400">· {role}</span>
            </div>
            <p className="text-xs text-stone-300 mt-0.5 line-clamp-1">{taskSummary}</p>
          </div>
        </div>

        {/* Status Pill */}
        <span
          className={cn(
            "px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide border flex items-center gap-1.5",
            currentStatus.badgeClass
          )}
        >
          <span className={cn("w-1.5 h-1.5 rounded-full", currentStatus.dot)} />
          {currentStatus.badge}
        </span>
      </div>

      {/* Progress Bar (if working) */}
      {status === "working" && progressPercent !== undefined && (
        <div className="mt-3 w-full bg-stone-800/80 rounded-full h-1.5 overflow-hidden">
          <div
            className="bg-amber-500 h-full rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      )}

      {/* Verified Source Fact Proof */}
      {sourceFactVerified && (
        <div className="mt-3 pt-2.5 border-t border-white/[0.06] flex items-center gap-2 text-[11px] text-stone-400">
          <span className="text-emerald-400">✓ Sourced:</span>
          <span className="truncate text-stone-300 font-mono text-[10px]">{sourceFactVerified}</span>
        </div>
      )}

      {/* Expandable Reasoning Drawer */}
      {outputPreview && (
        <div className="mt-2.5">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 text-[11px] font-medium text-amber-500/80 hover:text-amber-400 transition-colors"
          >
            <span>{isExpanded ? "Hide Agent Reasoning" : "Inspect Agent Reasoning"}</span>
            {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
          {isExpanded && (
            <div className="mt-2 p-3 rounded-xl bg-stone-900/90 border border-white/5 font-mono text-xs text-stone-300 leading-relaxed whitespace-pre-wrap">
              {outputPreview}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
