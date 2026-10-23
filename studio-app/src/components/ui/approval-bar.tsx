"use client";

import * as React from "react";
import { Check, Edit3, X, ShieldCheck } from "lucide-react";
import { Button } from "./button";

export interface ApprovalBarProps {
  onApprove: () => void;
  onRequestChanges: (instruction: string) => void;
  onReject: () => void;
  isPassedQualityGate?: boolean;
  score?: number;
}

export function ApprovalBar({
  onApprove,
  onRequestChanges,
  onReject,
  isPassedQualityGate = true,
  score = 96,
}: ApprovalBarProps) {
  const [showRequestInput, setShowRequestInput] = React.useState(false);
  const [changeText, setChangeText] = React.useState("");

  const handleSubmitChange = (e: React.FormEvent) => {
    e.preventDefault();
    if (changeText.trim()) {
      onRequestChanges(changeText.trim());
      setShowRequestInput(false);
      setChangeText("");
    }
  };

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-[94%] max-w-4xl">
      <div className="rounded-2xl bg-[#1A1816]/95 border border-white/15 p-3.5 shadow-2xl backdrop-blur-xl flex flex-col gap-3">
        {/* Main Action Bar */}
        <div className="flex items-center justify-between gap-4 flex-wrap">
          {/* Quality Gate Status */}
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-stone-100 text-xs sm:text-sm">
                  Quality Gate: Verified
                </span>
                <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px] font-mono font-bold">
                  Score {score}/100
                </span>
              </div>
              <p className="text-[11px] text-stone-400 hidden sm:block">
                All claims matched with verified Source Facts
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5 ml-auto">
            <Button
              variant="ghost"
              size="sm"
              onClick={onReject}
              className="text-stone-400 hover:text-rose-400"
            >
              <X className="w-3.5 h-3.5 mr-1" />
              <span>Reject</span>
            </Button>

            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowRequestInput(!showRequestInput)}
            >
              <Edit3 className="w-3.5 h-3.5 mr-1" />
              <span>Request Changes</span>
            </Button>

            <Button
              variant="primary"
              size="md"
              onClick={onApprove}
              className="px-5 shadow-lg shadow-amber-500/20"
            >
              <Check className="w-4 h-4 mr-1.5 stroke-[2.5]" />
              <span>Approve & Schedule</span>
            </Button>
          </div>
        </div>

        {/* Inline Request Changes Form */}
        {showRequestInput && (
          <form
            onSubmit={handleSubmitChange}
            className="pt-2 border-t border-white/10 flex items-center gap-2 animate-in fade-in-50"
          >
            <input
              type="text"
              value={changeText}
              onChange={(e) => setChangeText(e.target.value)}
              placeholder="Tell the crew what to tweak (e.g., 'Make the headline 20% bolder and mention free delivery')..."
              className="flex-1 bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2 text-xs text-stone-100 placeholder:text-stone-500 focus:outline-none focus:border-amber-500"
              autoFocus
            />
            <Button type="submit" variant="secondary" size="sm">
              Send to Crew ⚡
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}
