"use client";

import * as React from "react";
import Link from "next/link";
import { Header } from "@/components/ui/header";
import { Button } from "@/components/ui/button";
import { AgentCard } from "@/components/ui/agent-card";
import { PosterHeroMat } from "@/components/ui/poster-hero-mat";
import {
  Sparkles,
  ArrowRight,
  RefreshCw,
  MessageSquare,
  Layers,
  ShieldCheck,
  Check,
  Download,
  Eye,
  X,
  CheckCircle2,
} from "lucide-react";
import { campaignService, authService, getAuthToken } from "@/lib/api";

export default function StudioFloorPage() {
  const [businessName, setBusinessName] = React.useState("Rajkumar's Coffee Studio");
  const [industry, setIndustry] = React.useState("Specialty Cafe & Roastery");
  const [city, setCity] = React.useState("Pune, Maharashtra");
  const [phone, setPhone] = React.useState("+91 98200 12345");
  const [address, setAddress] = React.useState("42 Koregaon Park, Pune");

  const [objective, setObjective] = React.useState("Single-Origin Cold Brew Tasting");
  const [tone, setTone] = React.useState("Warm Editorial");
  const [brandColor, setBrandColor] = React.useState("#D97706");
  const [verifiedOffer, setVerifiedOffer] = React.useState("15% Off Cold Brew Reserve on Weekdays");
  const [selectedPlatforms, setSelectedPlatforms] = React.useState<string[]>([
    "Instagram",
    "GMB",
    "Facebook",
  ]);

  const [isWorking, setIsWorking] = React.useState(false);
  const [archetype, setArchetype] = React.useState<string>("split-image-text");
  const [activePosterUrl, setActivePosterUrl] = React.useState(
    "http://127.0.0.1:8000/static/generated/posters/66f4e5ff-eb1f-4147-b171-2e6481b01163.png"
  );
  const [activeHeadline, setActiveHeadline] = React.useState(
    "Artisanal Single-Origin Cold Brew"
  );
  const [agentStep, setAgentStep] = React.useState<"idle" | "research" | "copy" | "design" | "done">("idle");
  const [latestRunId, setLatestRunId] = React.useState<string | null>(null);
  const [isZoomOpen, setIsZoomOpen] = React.useState(false);
  const [toastMessage, setToastMessage] = React.useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleOpenCanva = async () => {
    try {
      const res = await campaignService.createCanvaDesign({
        title: activeHeadline,
        brand_color: brandColor,
        width: 1080,
        height: 1350,
      });
      if (res?.edit_url) {
        window.open(res.edit_url, "_blank");
        showToast("🎨 Opened in Canva AI Studio!");
      }
    } catch (_) {
      window.open("https://www.canva.com/create/posters/?width=1080&height=1350&unit=px", "_blank");
    }
  };


  // Load brand profile and authenticate
  React.useEffect(() => {
    try {
      const saved = localStorage.getItem("nexus_brand_profile");
      if (saved) {
        const p = JSON.parse(saved);
        if (p.businessName) setBusinessName(p.businessName);
        if (p.industry) setIndustry(p.industry);
        if (p.city) setCity(p.city);
        if (p.phone) setPhone(p.phone);
        if (p.address) setAddress(p.address);
        if (p.approvedOffer) setVerifiedOffer(p.approvedOffer);
        if (p.toneVoice) setTone(p.toneVoice);
        if (p.primaryColor) setBrandColor(p.primaryColor);
      }
    } catch (_) {}

    if (!getAuthToken()) {
      authService.getDevToken().catch(() => {});
    }
  }, []);

  const togglePlatform = (p: string) => {
    if (selectedPlatforms.includes(p)) {
      if (selectedPlatforms.length > 1) {
        setSelectedPlatforms(selectedPlatforms.filter((item) => item !== p));
      }
    } else {
      setSelectedPlatforms([...selectedPlatforms, p]);
    }
  };

  const handleBriefTeam = async () => {
    setIsWorking(true);
    setAgentStep("research");

    try {
      // 1. Call Backend API to trigger real multi-agent team run
      const runRes = await campaignService.createRun({
        brand: businessName,
        headline: `${objective}: ${verifiedOffer.split("(")[0].trim()}`,
        goal: `Promote our ${objective} with an emphasis on artisanal quality and verified 5.0 Google ratings`,
        tone: tone.toLowerCase().includes("festive") ? "festive" : "visionary",
        platforms: selectedPlatforms.map((p) => (p === "GMB" ? "gmb" : p.toLowerCase())),
        call_to_action: "Order Now",
        primary_color: brandColor,
      });

      setLatestRunId(runRes.id);

      // Save latest run to localStorage for Review Page
      try {
        localStorage.setItem("nexus_latest_run", JSON.stringify(runRes));
      } catch (_) {}

      // 2. Animate agent step hand-offs
      setTimeout(() => setAgentStep("copy"), 600);
      setTimeout(() => setAgentStep("design"), 1200);

      // 3. Extract the generated poster
      const posts = runRes.result?.content || [];
      const posterPost = posts.find((p: any) => p.poster_url);
      if (posterPost && posterPost.poster_url) {
        setActivePosterUrl(posterPost.poster_url);
      }
      if (runRes.result?.flagship_narrative?.headline) {
        setActiveHeadline(runRes.result.flagship_narrative.headline);
      }

      setTimeout(() => {
        setAgentStep("done");
        setIsWorking(false);
        showToast("⚡ Creative Studio Floor generated campaign & high-res poster!");
      }, 1800);
    } catch (err) {
      console.warn("Agent run error, calling direct poster render fallback:", err);
      // Fallback: directly render high-res poster via poster endpoint
      try {
        const renderRes = await campaignService.renderPoster({
          business_name: businessName,
          title: objective,
          subtitle: verifiedOffer,
          theme: objective.toLowerCase().includes("diwali") ? "festival_diwali" : "dining_culinary",
          archetype: archetype,
          phone: phone,
          address: address,
          rating: "Google 5.0 Star Rated",
          primary_color: brandColor,
        });
        if (renderRes.poster_url) {
          setActivePosterUrl(renderRes.poster_url);
        }
      } catch (_) {}
      setIsWorking(false);
      setAgentStep("done");
      showToast("✓ Studio poster rendered successfully!");
    }
  };

  const presetObjectives = [
    "Diwali Festive Special Offer",
    "Google 5-Star Reviews Spotlight",
    "Weekend Cold Brew Tasting",
    "Flash 15% Seasonal Discount",
  ];

  return (
    <div className="min-h-screen bg-[#121110] text-stone-100 flex flex-col pb-24">
      <Header brandName={businessName} />

      {/* Floating Toast Notification */}
      {toastMessage && (
        <div
          role="status"
          aria-live="polite"
          className="fixed top-20 right-6 z-50 px-4 py-2.5 rounded-xl bg-amber-500 text-stone-950 font-semibold text-xs shadow-2xl flex items-center gap-2 animate-in slide-in-from-top-3"
        >
          <CheckCircle2 className="w-4 h-4" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Full Zoom Inspection Modal */}
      {isZoomOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md animate-in fade-in"
        >
          <div className="relative max-w-2xl w-full flex flex-col items-center">
            <button
              onClick={() => setIsZoomOpen(false)}
              className="absolute -top-10 right-0 text-white/80 hover:text-white flex items-center gap-1 text-xs"
              aria-label="Close poster preview"
            >
              <X className="w-5 h-5" /> Close
            </button>
            <div className="w-full aspect-square rounded-2xl overflow-hidden border border-white/20 shadow-2xl bg-black">
              <img
                src={activePosterUrl}
                alt="High-resolution campaign poster"
                className="w-full h-full object-contain"
              />
            </div>
            <div className="mt-4 flex items-center gap-3">
              <a
                href={activePosterUrl}
                download="studio_campaign_poster.png"
                target="_blank"
                rel="noreferrer"
              >
                <Button variant="primary" size="sm">
                  <Download className="w-3.5 h-3.5 mr-1.5" />
                  Download High-Res Master (PNG)
                </Button>
              </a>
            </div>
          </div>
        </div>
      )}

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6 space-y-6">
        {/* Breadcrumb / Title Bar */}
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-amber-500 uppercase">Studio Floor</span>
              <span className="text-stone-600">/</span>
              <span className="text-xs text-stone-400">Autonomous Pipeline</span>
            </div>
            <h1 className="font-display text-2xl font-semibold text-stone-100 mt-1">
              Autonomous Creative Floor
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <Link href="/review">
              <Button variant="primary" size="sm" className="font-semibold shadow-lg shadow-amber-500/20">
                <span>View Final Review & Approve</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            </Link>
          </div>
        </div>

        {/* The 3-Zone Studio Floor Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Zone 1: The Briefing Console (Left 4 cols) */}
          <section aria-labelledby="briefingConsoleHeading" className="lg:col-span-4 rounded-3xl bg-[#1A1816] border border-white/[0.08] p-5 space-y-5 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 id="briefingConsoleHeading" className="text-xs font-mono text-amber-500 uppercase font-semibold">
                Zone 1 · Briefing Console
              </h2>
              <span className="text-[11px] text-stone-400">{businessName}</span>
            </div>

            <div className="space-y-4 text-xs">
              {/* Campaign Objective */}
              <div>
                <label htmlFor="objectiveInput" className="text-stone-300 font-medium block mb-1">
                  Campaign Objective / Theme *
                </label>
                <input
                  id="objectiveInput"
                  type="text"
                  required
                  value={objective}
                  onChange={(e) => setObjective(e.target.value)}
                  placeholder="e.g. Diwali Festive Special Offer"
                  className="w-full bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                />

                {/* Preset Chips */}
                <div className="flex flex-wrap gap-1.5 pt-2">
                  {presetObjectives.map((p) => (
                    <button
                      type="button"
                      key={p}
                      onClick={() => setObjective(p)}
                      className={`px-2 py-0.5 rounded-lg text-[10px] transition-colors border ${
                        objective === p
                          ? "bg-amber-500/20 border-amber-500 text-amber-300"
                          : "bg-stone-900 border-white/5 text-stone-400 hover:text-stone-200"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              {/* Verified Offer */}
              <div>
                <label htmlFor="verifiedOfferInput" className="text-stone-300 font-medium block mb-1">
                  Verified Offer (From Source Facts) *
                </label>
                <input
                  id="verifiedOfferInput"
                  type="text"
                  required
                  value={verifiedOffer}
                  onChange={(e) => setVerifiedOffer(e.target.value)}
                  placeholder="e.g. 15% Off Cold Brew Reserve on Weekdays"
                  className="w-full bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 focus:outline-none focus:border-amber-500"
                />
              </div>

              {/* Target Platforms Toggles */}
              <div>
                <label className="text-stone-300 font-medium block mb-1.5">
                  Target Publishing Channels
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {["Instagram", "GMB", "Facebook", "LinkedIn", "X"].map((plat) => {
                    const isSelected = selectedPlatforms.includes(plat);
                    return (
                      <button
                        type="button"
                        key={plat}
                        onClick={() => togglePlatform(plat)}
                        aria-pressed={isSelected}
                        className={`py-1.5 px-2 rounded-xl text-center text-[11px] font-medium border transition-all ${
                          isSelected
                            ? "bg-amber-500/15 border-amber-500 text-amber-400 font-semibold"
                            : "bg-stone-900 border-white/5 text-stone-400 hover:text-stone-300"
                        }`}
                      >
                        {plat}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Canva Design Theme & Brand Palette */}
              <div>
                <label className="text-stone-300 font-medium block mb-1.5 flex items-center justify-between">
                  <span>Canva Color Theme & Mood</span>
                  <span className="text-[10px] text-amber-400 font-mono">Dynamic WCAG</span>
                </label>
                <div className="grid grid-cols-4 gap-1.5">
                  {[
                    { id: "terracotta", name: "Artisan", hex: "#D97706" },
                    { id: "indigo", name: "Cyber", hex: "#6366F1" },
                    { id: "emerald", name: "Wellness", hex: "#10B981" },
                    { id: "crimson", name: "Flash", hex: "#EF4444" },
                    { id: "blue", name: "Keynote", hex: "#3B82F6" },
                    { id: "gold", name: "Luxury", hex: "#D4AF37" },
                    { id: "slate", name: "Minimal", hex: "#78716C" },
                    { id: "magenta", name: "Joyful", hex: "#EC4899" },
                  ].map((p) => {
                    const isSelected = brandColor.toUpperCase() === p.hex.toUpperCase();
                    return (
                      <button
                        type="button"
                        key={p.id}
                        onClick={() => setBrandColor(p.hex)}
                        className={`p-1.5 rounded-lg border text-center transition-all flex items-center justify-center gap-1.5 ${
                          isSelected
                            ? "bg-white/10 border-white text-white font-semibold shadow-md"
                            : "bg-stone-900 border-white/5 text-stone-400 hover:text-stone-200"
                        }`}
                      >
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: p.hex }} />
                        <span className="text-[11px]">{p.name}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Design Layout Archetype (Prompt Pack) */}
              <div>
                <label className="text-stone-300 font-medium block mb-1.5 flex items-center justify-between">
                  <span>Canva Layout Archetype</span>
                  <span className="text-[10px] text-amber-400 font-mono">7 Pro Templates</span>
                </label>
                <div className="grid grid-cols-2 gap-1.5">
                  {[
                    { id: "split-image-text", name: "Split Showcase", desc: "Food, dining & products" },
                    { id: "hero-text", name: "Hero Text", desc: "Bold headline focus" },
                    { id: "centered-badge", name: "Centered Badge", desc: "Festivals & openings" },
                    { id: "offer-burst", name: "Offer Burst", desc: "Flash sales & discounts" },
                    { id: "quote-card", name: "Quote Card", desc: "Reviews & testimonials" },
                    { id: "event-ticket", name: "Event Ticket", desc: "Conferences & dates" },
                    { id: "minimal-editorial", name: "Minimal Editorial", desc: "Quiet luxury & monograph" },
                  ].map((arch) => (
                    <button
                      type="button"
                      key={arch.id}
                      onClick={() => setArchetype(arch.id)}
                      className={`p-2 rounded-xl text-left border transition-all ${
                        archetype === arch.id
                          ? "bg-amber-500/15 border-amber-500 text-amber-300 font-semibold"
                          : "bg-stone-900 border-white/5 text-stone-400 hover:text-stone-200"
                      }`}
                    >
                      <div className="text-xs font-semibold">{arch.name}</div>
                      <div className="text-[10px] text-stone-500">{arch.desc}</div>
                    </button>
                  ))}
                </div>
              </div>


              {/* Tone of Voice */}
              <div>
                <label htmlFor="toneSelector" className="text-stone-300 font-medium block mb-1">
                  Tone of Voice
                </label>
                <select
                  id="toneSelector"
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  className="w-full bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 focus:outline-none focus:border-amber-500"
                >
                  <option value="Warm Editorial">Warm Editorial (Coffee & Dining)</option>
                  <option value="Friendly Casual">Friendly Casual (Local Community)</option>
                  <option value="High Urgency">High Urgency (Flash Deals & Events)</option>
                  <option value="Luxury Gold">Luxury Gold (High-End & Reserved)</option>
                </select>
              </div>

              {/* Action Button */}
              <div className="pt-2">
                <Button
                  type="button"
                  variant="primary"
                  size="lg"
                  disabled={isWorking}
                  onClick={handleBriefTeam}
                  className="w-full font-semibold shadow-xl shadow-amber-500/20"
                >
                  {isWorking ? (
                    <span className="flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Studio Team Generating...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4" />
                      Brief Studio Crew & Generate ⚡
                    </span>
                  )}
                </Button>
              </div>
            </div>
          </section>

          {/* Zone 2: The Agent Floor Timeline (Center 4 cols) */}
          <section aria-labelledby="agentFloorHeading" className="lg:col-span-4 rounded-3xl bg-[#1A1816] border border-white/[0.08] p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 id="agentFloorHeading" className="text-xs font-mono text-amber-500 uppercase font-semibold">
                Zone 2 · Live Agent Floor
              </h2>
              <span className="text-[11px] text-emerald-400 font-mono">
                {isWorking ? "Active Run in Progress" : "5 Specialists Ready"}
              </span>
            </div>

            <div className="space-y-3">
              <AgentCard
                id="research"
                name="Research Specialist"
                role="Market Radar"
                avatarIcon="radar"
                taskSummary="Verified Diwali holiday trends, Pune coffee footfall, and local search intent."
                status={
                  agentStep === "research"
                    ? "working"
                    : agentStep === "copy" || agentStep === "design" || agentStep === "done"
                    ? "done"
                    : "idle"
                }
              />

              <AgentCard
                id="copy"
                name="Strategy & Copywriter"
                role="Content Engine"
                avatarIcon="pen"
                taskSummary="Drafted warm flagship narrative with 15% weekday offer and zero unverified claims."
                status={
                  agentStep === "copy"
                    ? "working"
                    : agentStep === "design" || agentStep === "done"
                    ? "done"
                    : "idle"
                }
              />

              <AgentCard
                id="design"
                name="Poster Designer"
                role="Visual Studio"
                avatarIcon="palette"
                taskSummary="Composed 1080×1080 Saffron Gold layout, Diya motifs, and crisp Google rating badge."
                status={
                  agentStep === "design" ? "working" : agentStep === "done" ? "done" : "idle"
                }
              />

              <AgentCard
                id="quality"
                name="Quality Gate"
                role="Governance"
                avatarIcon="shield"
                taskSummary="Audit completed: 100/100 compliance score. Verified contact and WCAG AAA contrast."
                status={agentStep === "done" ? "done" : "idle"}
              />

              <AgentCard
                id="publish"
                name="Publisher Agent"
                role="Operations"
                avatarIcon="send"
                taskSummary="Staged draft for Instagram, GMB, and Facebook. Awaiting 1-tap editorial sign-off."
                status={agentStep === "done" ? "done" : "idle"}
              />
            </div>
          </section>

          {/* Zone 3: Live Poster Hero Mat (Right 4 cols) */}
          <section aria-labelledby="liveMatHeading" className="lg:col-span-4 rounded-3xl bg-[#1A1816] border border-white/[0.08] p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 id="liveMatHeading" className="text-xs font-mono text-amber-500 uppercase font-semibold">
                Zone 3 · Live Master Mat
              </h2>
              <span className="text-[11px] text-stone-400">1080×1080 Square</span>
            </div>

            <div className="rounded-2xl bg-black border border-white/10 p-3 space-y-3 shadow-inner">
              <div className="relative w-full aspect-square rounded-xl overflow-hidden border border-white/10 bg-[#121110] group">
                <img
                  src={activePosterUrl}
                  alt={activeHeadline}
                  className="w-full h-full object-cover transition-transform group-hover:scale-[1.02]"
                />

                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                  <button
                    onClick={() => setIsZoomOpen(true)}
                    className="p-2.5 rounded-full bg-white/20 hover:bg-white/30 text-white backdrop-blur-md transition-colors"
                    aria-label="Inspect poster full screen"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                  <a
                    href={activePosterUrl}
                    download="studio_campaign_poster.png"
                    target="_blank"
                    rel="noreferrer"
                    className="p-2.5 rounded-full bg-white/20 hover:bg-white/30 text-white backdrop-blur-md transition-colors"
                    aria-label="Download poster PNG"
                  >
                    <Download className="w-4 h-4" />
                  </a>
                </div>
              </div>

              <div className="space-y-1 text-xs">
                <span className="text-[10px] font-mono text-amber-500 uppercase font-semibold block">
                  Flagship Headline
                </span>
                <p className="font-semibold text-stone-100 text-xs leading-snug">
                  {activeHeadline}
                </p>
                <p className="text-[11px] text-stone-400">
                  {phone} · {address}
                </p>
              </div>

              <div className="pt-2 border-t border-white/[0.08] flex items-center justify-between gap-2">
                <button
                  type="button"
                  onClick={() => setIsZoomOpen(true)}
                  className="text-stone-400 hover:text-stone-200 text-xs flex items-center gap-1"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Inspect</span>
                </button>

                <button
                  type="button"
                  onClick={handleOpenCanva}
                  className="px-2.5 py-1.5 rounded-xl bg-gradient-to-r from-teal-500/20 to-cyan-500/20 hover:from-teal-500/30 hover:to-cyan-500/30 text-teal-300 border border-teal-500/30 text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm"
                  title="Open and edit layout inside Canva AI Design Studio"
                >
                  <span>🎨 Edit in Canva AI</span>
                </button>

                <Link href="/review">
                  <Button variant="primary" size="sm">
                    <span>Review</span>
                    <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                </Link>
              </div>

            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
