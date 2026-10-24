"use client";

import * as React from "react";
import Image from "next/image";
import { Download, Sparkles, Eye, ShieldCheck, Check, Layers } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./button";

export interface PosterHeroMatProps {
  posterUrl: string;
  brandName?: string;
  criticScore?: number;
  criticCriteria?: { label: string; score: string }[];
  aspectRatio?: "1:1" | "4:5" | "9:16";
  onDownloadPng?: () => void;
  onCompareDrafts?: () => void;
}

export function PosterHeroMat({
  posterUrl,
  brandName = "Rajkumar's Studio",
  criticScore = 96,
  criticCriteria = [
    { label: "Palette & Contrast", score: "10/10" },
    { label: "Brand Typography", score: "10/10" },
    { label: "Safe Margin Crop", score: "9/10" },
    { label: "Source Facts Check", score: "10/10" },
  ],
  aspectRatio = "1:1",
  onDownloadPng,
  onCompareDrafts,
}: PosterHeroMatProps) {
  const [showSafeZones, setShowSafeZones] = React.useState(false);

  return (
    <div className="rounded-3xl bg-[#1A1816] border border-white/[0.1] p-5 shadow-2xl flex flex-col gap-4">
      {/* Top Meta Bar */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Critic Score: {criticScore} / 100</span>
          </span>
          <span className="text-xs text-stone-400">· 1080×1080 Native High-Res</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSafeZones(!showSafeZones)}
            className={cn(
              "px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors flex items-center gap-1.5",
              showSafeZones
                ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                : "bg-stone-900 border-white/10 text-stone-400 hover:text-stone-200"
            )}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Safe Zones</span>
          </button>

          {onCompareDrafts && (
            <button
              onClick={onCompareDrafts}
              className="px-2.5 py-1 rounded-lg text-xs font-medium bg-stone-900 border border-white/10 text-stone-400 hover:text-stone-200 transition-colors"
            >
              Compare Drafts
            </button>
          )}
        </div>
      </div>

      {/* Poster Canvas Framing (The Mat) */}
      <div className="relative w-full aspect-square rounded-2xl overflow-hidden bg-black/60 border border-white/10 flex items-center justify-center group shadow-inner">
        {/* Poster Image */}
        <img
          src={posterUrl}
          alt={`${brandName} Hero Poster`}
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-[1.01]"
        />

        {/* Safe-Zone Overlays */}
        {showSafeZones && (
          <div className="absolute inset-8 border border-dashed border-amber-400/60 rounded-xl pointer-events-none flex flex-col justify-between p-2">
            <span className="text-[10px] text-amber-300 bg-black/70 px-1.5 py-0.5 rounded self-start font-mono">
              Instagram Feed Safe Zone (4:5)
            </span>
            <span className="text-[10px] text-amber-300 bg-black/70 px-1.5 py-0.5 rounded self-end font-mono">
              Safe Typography Bounds
            </span>
          </div>
        )}
      </div>

      {/* Critic Rubric & Quick Action */}
      <div className="flex items-center justify-between gap-4 pt-1 flex-wrap">
        <div className="flex items-center gap-3 text-xs text-stone-400 flex-wrap">
          {criticCriteria.map((item) => (
            <div key={item.label} className="flex items-center gap-1">
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span>{item.label}:</span>
              <span className="text-stone-200 font-medium">{item.score}</span>
            </div>
          ))}
        </div>

        {onDownloadPng && (
          <Button
            variant="secondary"
            size="sm"
            onClick={onDownloadPng}
            className="flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download PNG</span>
          </Button>
        )}
      </div>
    </div>
  );
}
