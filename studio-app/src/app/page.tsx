"use client";

import * as React from "react";
import Link from "next/link";
import { Header } from "@/components/ui/header";
import { Button } from "@/components/ui/button";
import { 
  Sparkles, Calendar, ArrowRight, CheckCircle2, TrendingUp, 
  Users, MapPin, Eye, PlusCircle, ShieldAlert, ArrowUpRight, 
  Share2, Layers, Clock
} from "lucide-react";
import { campaignService, authService } from "@/lib/api";

export default function MissionControlPage() {
  const [user, setUser] = React.useState<any>(null);
  const [businessProfile, setBusinessProfile] = React.useState<any>(null);
  const [runs, setRuns] = React.useState<any[]>([]);
  const [connections, setConnections] = React.useState<any[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    let isMounted = true;
    async function loadWorkspaceData() {
      try {
        const profile = await authService.getProfile();
        if (isMounted) {
          setUser(profile);
          if (profile?.business_name) {
            setBusinessProfile({
              name: profile.business_name,
              category: profile.category || "General",
            });
          }
        }

        // Fetch real runs
        try {
          const runRes = await campaignService.getRuns();
          if (isMounted && runRes?.runs) {
            setRuns(runRes.runs);
          }
        } catch (_) {}

        // Fetch real connections
        try {
          const connRes = await fetch("/api/connections", { credentials: "include" });
          if (connRes.ok) {
            const data = await connRes.json();
            if (isMounted) {
              setConnections(data.connections || []);
            }
          }
        } catch (_) {}
      } catch (_) {
        if (isMounted) {
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadWorkspaceData();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#121110] text-stone-100 flex flex-col font-sans">
      <Header brandName={businessProfile?.name || ""} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8 space-y-8">
        {/* Loading State */}
        {isLoading ? (
          <div className="py-24 flex flex-col items-center justify-center space-y-4">
            <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-xs text-stone-400 font-mono">Loading workspace intelligence...</p>
          </div>
        ) : !user ? (
          /* Unauthenticated State */
          <div className="rounded-3xl bg-gradient-to-b from-[#1C1A17] to-[#141312] border border-white/[0.08] p-8 lg:p-12 shadow-2xl relative overflow-hidden">
            <div className="max-w-2xl space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-semibold tracking-wide">
                <Sparkles className="w-3.5 h-3.5" />
                Production AI-Native Marketing System
              </div>
              <h1 className="text-3xl lg:text-4xl font-bold tracking-tight text-white leading-tight">
                Enterprise Multi-Agent Social Media Team
              </h1>
              <p className="text-stone-300 text-sm leading-relaxed">
                Connect your real business profile and social channels. Our LangGraph agent team researches, designs, writes copy, and schedules high-converting visual posters tailored strictly to your industry.
              </p>
              <div className="pt-2 flex items-center gap-4">
                <Link href="/login">
                  <Button variant="primary" size="lg" className="font-semibold shadow-lg shadow-amber-500/20">
                    Sign in with Google
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        ) : !businessProfile?.name ? (
          /* Onboarding Incomplete State */
          <div className="rounded-3xl bg-[#1A1816] border border-amber-500/30 p-8 lg:p-10 shadow-2xl relative overflow-hidden">
            <div className="max-w-2xl space-y-5">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-400 text-xs font-semibold">
                <ShieldAlert className="w-3.5 h-3.5" />
                Action Required: Business Registration
              </div>
              <h2 className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
                Register Your Business Profile
              </h2>
              <p className="text-stone-300 text-sm leading-relaxed">
                Your account is authenticated via Google. Before the AI design team can compose posters and campaigns, enter your business details, industry vertical, and brand kit.
              </p>
              <div className="pt-2">
                <Link href="/onboarding">
                  <Button variant="primary" size="lg" className="font-semibold shadow-md shadow-amber-500/20">
                    Start Business Registration
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        ) : (
          /* Active Real Workspace State */
          <>
            {/* Header / Workspace Banner */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/[0.08]">
              <div>
                <div className="flex items-center gap-2 text-xs font-mono text-stone-400 mb-1">
                  <span>WORKSPACE:</span>
                  <span className="text-amber-400 font-semibold">{businessProfile.name}</span>
                </div>
                <h1 className="text-2xl font-bold text-white tracking-tight">
                  Mission Control Floor
                </h1>
              </div>
              <div className="flex items-center gap-3">
                <Link href="/studio">
                  <Button variant="primary" size="md" className="font-semibold shadow-sm">
                    <PlusCircle className="w-4 h-4 mr-2" />
                    New Campaign Brief
                  </Button>
                </Link>
                <Link href="/connect">
                  <Button variant="secondary" size="md">
                    <Share2 className="w-4 h-4 mr-2" />
                    {connections.length} Channels
                  </Button>
                </Link>
              </div>
            </div>

            {/* Campaign Summary & Honest Empty State */}
            {runs.length === 0 ? (
              <div className="rounded-3xl bg-[#1A1816] border border-white/[0.08] p-12 text-center space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center mx-auto">
                  <Layers className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-semibold text-white">No campaigns generated yet</h3>
                <p className="text-sm text-stone-400 max-w-md mx-auto">
                  Create your first campaign brief in Studio Floor. Your business understanding agent will compose designs using your real brand assets.
                </p>
                <div className="pt-2">
                  <Link href="/studio">
                    <Button variant="primary" size="md" className="font-semibold">
                      Launch First Campaign
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </Link>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <h2 className="text-sm font-semibold tracking-wider uppercase text-stone-400 font-mono">
                  Active Campaigns ({runs.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {runs.map((run) => (
                    <div
                      key={run.id}
                      className="rounded-2xl bg-[#1A1816] border border-white/[0.08] p-5 space-y-3 hover:border-white/20 transition-all"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-mono text-stone-400">{run.created_at?.slice(0, 10)}</span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          {run.status}
                        </span>
                      </div>
                      <h3 className="font-semibold text-white text-base truncate">
                        {run.request?.brand || businessProfile.name}
                      </h3>
                      <p className="text-xs text-stone-400 line-clamp-2">
                        {run.request?.goal || "Brand awareness and visual poster distribution."}
                      </p>
                      <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between">
                        <span className="text-xs text-stone-500 font-mono">Run ID #{run.id?.slice(0, 8)}</span>
                        <Link href={`/review?run_id=${run.id}`} className="text-xs text-amber-400 hover:text-amber-300 font-medium flex items-center gap-1">
                          View Details <ArrowUpRight className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
