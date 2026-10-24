"use client";

import * as React from "react";
import Link from "next/link";
import { Header } from "@/components/ui/header";
import { Button } from "@/components/ui/button";
import { Sparkles, Calendar, ArrowRight, CheckCircle2, TrendingUp, Users, MapPin, Eye } from "lucide-react";
import { campaignService } from "@/lib/api";

export default function MissionControlPage() {
  const [isApproved, setIsApproved] = React.useState(false);

  const handleQuickApprove = async () => {
    setIsApproved(true);
    try {
      await campaignService.approveRun("ae438190-9546-4604-b942-55fe5d7afbbc");
      await campaignService.publishRun("ae438190-9546-4604-b942-55fe5d7afbbc");
    } catch (_) {}
  };

  return (
    <div className="min-h-screen bg-[#121110] text-stone-100 flex flex-col">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8 space-y-8">
        {/* Section 1: Hero Editorial Priority */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-amber-500 font-mono">
              Editorial Priority · Attention Required
            </span>
            <span className="text-xs text-stone-400">Run ID #DF72-2026</span>
          </div>

          <div className="rounded-3xl bg-[#1A1816] border border-white/[0.1] p-6 lg:p-8 shadow-2xl relative overflow-hidden">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              {/* Hero Poster Mat Frame (Left) */}
              <div className="lg:col-span-5 flex flex-col items-center">
                <div className="relative w-full max-w-[340px] aspect-square rounded-2xl overflow-hidden border border-white/10 shadow-xl bg-black">
                  <img
                    src="http://127.0.0.1:8000/static/generated/posters/66f4e5ff-eb1f-4147-b171-2e6481b01163.png"
                    alt="Diwali Festive Offer Poster"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      // Fallback if local backend poster isn't fetched
                      (e.target as HTMLImageElement).src =
                        "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=800&auto=format&fit=crop&q=80";
                    }}
                  />
                  <div className="absolute top-3 left-3 px-2 py-0.5 rounded-full bg-black/70 backdrop-blur-md border border-white/20 text-[10px] font-mono text-amber-400">
                    ★ 5.0 GMB Verified
                  </div>
                </div>
              </div>

              {/* Narrative & 1-Tap Actions (Right) */}
              <div className="lg:col-span-7 flex flex-col justify-between space-y-5">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="px-2.5 py-0.5 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-400 text-xs font-medium">
                      🪔 Diwali Special (Verified Calendar)
                    </span>
                    <span className="text-xs text-stone-400">Oct 28 · 6:00 PM IST</span>
                  </div>

                  <h1 className="font-display text-2xl lg:text-3xl font-semibold text-[#FDFCFB] tracking-tight leading-snug">
                    Diwali Festive Special: Cold Brew Gift Reserve
                  </h1>

                  <p className="text-sm text-stone-300 mt-3 leading-relaxed">
                    Targeted across <strong>Instagram Feed</strong> and <strong>Google Business Profile</strong>. All contact details (+91 98200 12345), operating hours, and active 15% discount have been cross-checked with your approved Source Facts.
                  </p>
                </div>

                {/* Audit Checklist Badges */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 pt-2 border-t border-white/[0.08] text-xs text-stone-300">
                  <div className="flex items-center gap-1.5 text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Brand Colors (AAA)</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Real Phone Verified</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Zero Invented Claims</span>
                  </div>
                </div>

                {/* 1-Tap Approval Row */}
                <div className="pt-3 flex items-center gap-3 flex-wrap">
                  {isApproved ? (
                    <div className="px-5 py-2.5 rounded-xl bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-sm font-semibold flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Approved! Scheduled for Friday, Oct 28 at 6:00 PM IST</span>
                    </div>
                  ) : (
                    <>
                      <Button
                        variant="primary"
                        size="lg"
                        onClick={handleQuickApprove}
                        className="shadow-xl shadow-amber-500/20 font-semibold"
                      >
                        ✓ Approve & Schedule (1-Tap)
                      </Button>

                      <Link href="/review">
                        <Button variant="secondary" size="lg">
                          Review Channel Details
                          <ArrowRight className="w-4 h-4 ml-1.5" />
                        </Button>
                      </Link>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Section 2: Publishing Next (7-Day Visual Flow) */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold tracking-wider uppercase text-stone-400 font-mono">
              Publishing Next (7-Day Content Flow)
            </h2>
            <Link href="/calendar" className="text-xs text-amber-500 hover:text-amber-400 transition-colors">
              Open Interactive Calendar →
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              {
                day: "Mon, Oct 24",
                time: "10:00 AM",
                channel: "GMB Update",
                title: "Weekly Review Highlight",
                status: "Published",
                statusClass: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
              },
              {
                day: "Wed, Oct 26",
                time: "6:30 PM",
                channel: "Instagram Reel",
                title: "Artisanal Roasting Process",
                status: "Scheduled",
                statusClass: "text-amber-400 bg-amber-500/10 border-amber-500/20",
              },
              {
                day: "Fri, Oct 28",
                time: "6:00 PM",
                channel: "IG + GMB Hero",
                title: "Diwali Festive Gift Box",
                status: isApproved ? "Scheduled" : "Awaiting Approval",
                statusClass: isApproved
                  ? "text-amber-400 bg-amber-500/10 border-amber-500/20"
                  : "text-rose-400 bg-rose-500/10 border-rose-500/20",
              },
              {
                day: "Sun, Oct 30",
                time: "9:30 AM",
                channel: "Instagram Story",
                title: "Weekend Tasting Flight",
                status: "Draft Concept",
                statusClass: "text-stone-400 bg-stone-800 border-stone-700",
              },
            ].map((slot, i) => (
              <div
                key={i}
                className="rounded-2xl bg-[#1A1816] border border-white/[0.08] p-4 flex flex-col justify-between hover:border-white/20 transition-all gap-3"
              >
                <div>
                  <div className="flex items-center justify-between text-xs text-stone-400 mb-1">
                    <span>{slot.day}</span>
                    <span className="font-mono text-[11px]">{slot.time}</span>
                  </div>
                  <h3 className="font-medium text-stone-100 text-sm">{slot.title}</h3>
                  <p className="text-xs text-amber-500 font-mono mt-0.5">{slot.channel}</p>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-white/[0.06]">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${slot.statusClass}`}>
                    ● {slot.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Section 3: Split Basement (Live Studio Floor + Performance Intelligence) */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Active Studio Floor (Left 60%) */}
          <div className="lg:col-span-7 rounded-3xl bg-[#1A1816] border border-white/[0.08] p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold tracking-wider uppercase text-stone-400 font-mono">
                The Studio Floor Right Now
              </h2>
              <Link href="/studio" className="text-xs text-amber-500 hover:text-amber-400">
                Open Studio Floor →
              </Link>
            </div>

            <div className="space-y-3">
              {[
                {
                  icon: "🔍",
                  name: "Research Agent",
                  role: "Audience Intelligence",
                  status: "Idle",
                  statusClass: "bg-stone-800 text-stone-400",
                  task: "Indexed 14 Pune festive gifting hooks from Google Trends",
                },
                {
                  icon: "🎨",
                  name: "Poster Designer",
                  role: "Visual Director",
                  status: "Active",
                  statusClass: "bg-amber-500/20 text-amber-300 animate-pulse",
                  task: "Rendering dual Pillow PNG and vector SVG for Weekend Tasting",
                },
                {
                  icon: "✍️",
                  name: "Copywriter Agent",
                  role: "Editorial Tone",
                  status: "Ready",
                  statusClass: "bg-emerald-500/15 text-emerald-300",
                  task: "Finished 3 caption variants for Instagram and Google Maps",
                },
              ].map((agent, i) => (
                <div key={i} className="flex items-center justify-between p-3.5 rounded-xl bg-stone-900/50 border border-white/[0.05]">
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{agent.icon}</span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-stone-100">{agent.name}</span>
                        <span className="text-[11px] text-stone-500">· {agent.role}</span>
                      </div>
                      <p className="text-xs text-stone-400 line-clamp-1">{agent.task}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border border-white/5 ${agent.statusClass}`}>
                    {agent.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Performance Intelligence (Right 40%) */}
          <div className="lg:col-span-5 rounded-3xl bg-[#1A1816] border border-white/[0.08] p-6 space-y-4 flex flex-col justify-between">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-amber-500 font-mono">
                Weekly Analyst Insight
              </span>
              <h2 className="font-display text-lg text-stone-100 mt-2 leading-snug">
                "Reels drove 2.4x more directions on Google Maps than static photos this week."
              </h2>
              <p className="text-xs text-stone-400 mt-2 leading-relaxed">
                Customers interacted most with video posts highlighting real behind-the-scenes bean roasting. Total Reach: <strong>48.2K (+28%)</strong>.
              </p>
            </div>

            <div className="pt-4 border-t border-white/[0.06] flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs text-emerald-400">
                <TrendingUp className="w-4 h-4" />
                <span>Direction requests up +36%</span>
              </div>
              <Link href="/studio">
                <Button variant="secondary" size="sm">
                  Create Video Brief ⚡
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
