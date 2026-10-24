"use client";

import * as React from "react";
import { CheckCircle2, AlertTriangle, AlertCircle, RefreshCw, Unplug, Shield } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./button";

export interface PlatformCardProps {
  platformId: "instagram" | "gmb" | "facebook" | "youtube" | "x";
  platformName: string;
  accountHandle?: string;
  avatarUrl?: string;
  status: "connected" | "needs_reconnect" | "not_connected" | "limited" | "connecting";
  tokenHealthDays?: number;
  lastSyncedText?: string;
  permissionsGranted?: string[];
  benefitText?: string;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onTestHandshake?: () => void;
}

export function PlatformCard({
  platformName,
  accountHandle,
  status,
  tokenHealthDays = 60,
  lastSyncedText = "Just now",
  permissionsGranted = ["Direct Publishing", "Analytics Sync"],
  benefitText = "Unlocks scheduled in-feed & story publishing",
  onConnect,
  onDisconnect,
  onTestHandshake,
}: PlatformCardProps) {
  const isConnected = status === "connected";
  const needsReconnect = status === "needs_reconnect";

  return (
    <div
      className={cn(
        "rounded-2xl border p-5 transition-all flex flex-col justify-between gap-4",
        isConnected
          ? "bg-[#1A1816] border-white/10 hover:border-white/20 shadow-md"
          : needsReconnect
          ? "bg-amber-950/10 border-amber-500/30"
          : "bg-stone-900/40 border-dashed border-white/15"
      )}
    >
      <div>
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-stone-100 text-base">{platformName}</span>
              {isConnected && (
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-[11px] font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  Active
                </span>
              )}
              {needsReconnect && (
                <span className="px-2 py-0.5 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-400 text-[11px] font-semibold flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  Token Expired
                </span>
              )}
              {!isConnected && !needsReconnect && (
                <span className="px-2 py-0.5 rounded-full bg-stone-800 text-stone-400 text-[11px] font-medium">
                  Not Connected
                </span>
              )}
            </div>

            {accountHandle ? (
              <p className="text-xs text-amber-400 font-mono mt-0.5">{accountHandle}</p>
            ) : (
              <p className="text-xs text-stone-400 mt-1">{benefitText}</p>
            )}
          </div>
        </div>

        {/* Telemetry Details */}
        {isConnected && (
          <div className="mt-4 pt-3 border-t border-white/[0.08] space-y-1.5 text-xs text-stone-300">
            <div className="flex items-center justify-between text-stone-400">
              <span>Token Health:</span>
              <span className="text-stone-200 font-medium">{tokenHealthDays} Days Valid</span>
            </div>
            <div className="flex items-center justify-between text-stone-400">
              <span>Last Handshake:</span>
              <span className="text-stone-200 font-medium">{lastSyncedText}</span>
            </div>
            <div className="flex items-center justify-between text-stone-400">
              <span>Permissions:</span>
              <span className="text-emerald-400 text-[11px] truncate max-w-[180px]">
                {permissionsGranted.join(", ")}
              </span>
            </div>
          </div>
        )}

        {needsReconnect && (
          <div className="mt-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200 leading-relaxed">
            Meta / Google session was revoked. Scheduled posts are safely paused. Click below to refresh OAuth in 1 tap.
          </div>
        )}
      </div>

      {/* Action Controls */}
      <div className="pt-2 flex items-center justify-between gap-3 flex-wrap">
        {isConnected ? (
          <>
            <button
              onClick={onDisconnect}
              className="text-xs text-rose-400 hover:text-rose-300 transition-colors flex items-center gap-1"
            >
              <Unplug className="w-3.5 h-3.5" />
              <span>Disconnect</span>
            </button>

            {onTestHandshake && (
              <Button variant="secondary" size="sm" onClick={onTestHandshake}>
                Test Handshake ⚡
              </Button>
            )}
          </>
        ) : needsReconnect ? (
          <Button variant="primary" size="sm" onClick={onConnect} className="w-full">
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
            Reconnect Account (1-Tap)
          </Button>
        ) : (
          <Button variant="primary" size="sm" onClick={onConnect} className="w-full">
            Connect Account
          </Button>
        )}
      </div>
    </div>
  );
}
