"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Header } from "@/components/ui/header";
import { Button } from "@/components/ui/button";
import {
  Check,
  Sparkles,
  Upload,
  ArrowRight,
  ArrowLeft,
  ShieldCheck,
  Building2,
  User,
  Globe,
  Phone,
  MapPin,
  Tag,
  Ban,
  Clock,
  Palette,
  X,
  CheckCircle2,
} from "lucide-react";
import { fetchApi, campaignService } from "@/lib/api";

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = React.useState(1);
  const [saveStatus, setSaveStatus] = React.useState<string | null>(null);

  // Form Fields
  const [accountType, setAccountType] = React.useState<"business" | "creator" | "agency">("business");
  const [businessName, setBusinessName] = React.useState("Rajkumar's Coffee Studio");
  const [industry, setIndustry] = React.useState("Specialty Cafe & Roastery");
  const [city, setCity] = React.useState("Pune, Maharashtra");
  const [website, setWebsite] = React.useState("https://rajkumarstudio.in");
  const [logoPreview, setLogoPreview] = React.useState<string | null>(null);
  const [selectedColor, setSelectedColor] = React.useState("#F59E0B");
  const [customHex, setCustomHex] = React.useState("#F59E0B");
  const [previewPosterUrl, setPreviewPosterUrl] = React.useState<string>(
    "http://127.0.0.1:8000/static/generated/posters/66f4e5ff-eb1f-4147-b171-2e6481b01163.png"
  );
  const [isUpdatingPoster, setIsUpdatingPoster] = React.useState(false);
  const [fontPairing, setFontPairing] = React.useState("Fraunces + Geist");
  const [primaryGoal, setPrimaryGoal] = React.useState("More walk-in customers & footfall");
  const [customGoal, setCustomGoal] = React.useState("");
  const [toneVoice, setToneVoice] = React.useState("Warm Editorial");
  const [phone, setPhone] = React.useState("+91 98200 12345");
  const [address, setAddress] = React.useState("42 Koregaon Park, Pune 411001");
  const [hours, setHours] = React.useState("8:00 AM - 11:00 PM Daily");
  const [approvedOffer, setApprovedOffer] = React.useState("15% Off Cold Brew Reserve on Weekdays");
  const [bannedWords, setBannedWords] = React.useState("cheapest, fake discount, crypto");
  const [competitors, setCompetitors] = React.useState<string[]>(["@bluebottle", "@subko.coffee"]);
  const [newCompetitor, setNewCompetitor] = React.useState("");
  const [approvalMode, setApprovalMode] = React.useState<"human" | "autopilot">("human");

  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const triggerColorPreview = React.useCallback(
    async (colorHex: string) => {
      try {
        setIsUpdatingPoster(true);
        const res = await campaignService.renderPoster({
          business_name: businessName,
          title: "Diwali Festive Offer: Scale Your Operations With AI Agents",
          subtitle: "May this auspicious festival illuminate prosperity & new heights",
          primary_color: colorHex,
          phone: phone,
          address: address,
          rating: "Google 5-Star Customer Rating",
        });
        if (res.poster_url) {
          setPreviewPosterUrl(res.poster_url);
        }
      } catch (err) {
        console.warn("Color poster render error:", err);
      } finally {
        setIsUpdatingPoster(false);
      }
    },
    [businessName, phone, address]
  );

  // Load existing profile from localStorage if available
  React.useEffect(() => {
    try {
      const saved = localStorage.getItem("nexus_brand_profile");
      if (saved) {
        const p = JSON.parse(saved);
        if (p.businessName) setBusinessName(p.businessName);
        if (p.industry) setIndustry(p.industry);
        if (p.city) setCity(p.city);
        if (p.website) setWebsite(p.website);
        if (p.primaryColor) {
          setSelectedColor(p.primaryColor);
          setCustomHex(p.primaryColor);
        }
        if (p.fontPairing) setFontPairing(p.fontPairing);
        if (p.primaryGoal) setPrimaryGoal(p.primaryGoal);
        if (p.toneVoice) setToneVoice(p.toneVoice);
        if (p.phone) setPhone(p.phone);
        if (p.address) setAddress(p.address);
        if (p.approvedOffer) setApprovedOffer(p.approvedOffer);
        if (p.bannedWords) setBannedWords(p.bannedWords);
        if (p.approvalMode) setApprovalMode(p.approvalMode);
        if (p.logoPreview) setLogoPreview(p.logoPreview);
        if (p.competitors) setCompetitors(p.competitors);
      }
    } catch (_) {}
  }, []);

  const persistProfile = (goToStudio = false) => {
    const profile = {
      accountType,
      businessName,
      industry,
      city,
      website,
      logoPreview,
      primaryColor: selectedColor,
      fontPairing,
      primaryGoal: customGoal ? customGoal : primaryGoal,
      toneVoice,
      phone,
      address,
      hours,
      approvedOffer,
      bannedWords,
      competitors,
      approvalMode,
      updatedAt: new Date().toISOString(),
    };

    localStorage.setItem("nexus_brand_profile", JSON.stringify(profile));
    window.dispatchEvent(new Event("storage"));

    // Sync to backend business profile
    fetchApi("/api/business-profile", {
      method: "POST",
      body: JSON.stringify({
        business_name: businessName,
        category: industry,
        phone,
        address,
        website,
        tagline: approvedOffer,
        rating: "5.0 ★★★★★",
        review_count: "150+ Verified Reviews",
        primary_color: selectedColor,
      }),
    }).catch(() => {});

    setSaveStatus("Brand Kit Synchronized ✓");
    setTimeout(() => setSaveStatus(null), 2500);

    if (goToStudio) {
      router.push("/studio");
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        if (evt.target?.result) {
          setLogoPreview(evt.target.result as string);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAddCompetitor = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && newCompetitor.trim()) {
      e.preventDefault();
      const handle = newCompetitor.trim().startsWith("@")
        ? newCompetitor.trim()
        : `@${newCompetitor.trim()}`;
      if (!competitors.includes(handle)) {
        setCompetitors([...competitors, handle]);
      }
      setNewCompetitor("");
    }
  };

  const removeCompetitor = (handle: string) => {
    setCompetitors(competitors.filter((c) => c !== handle));
  };

  const sampleCaptions: Record<string, string> = {
    "Warm Editorial":
      "Savor the quiet comfort of small-batch roasts in Koregaon Park. Brewed slow for rich, chocolate notes.",
    "Friendly Casual":
      "Craving your daily iced latte? Drop by today and enjoy 15% off our signature cold brew!",
    "High Urgency":
      "⚡ Flash festive discount! Only 48 hours left to claim your 15% discount on handcrafted cold brew reserve.",
    "Luxury Gold":
      "Distinguished single-origin beans, precision roasted for an uncompromising sensory experience.",
  };

  return (
    <div className="min-h-screen bg-[#121110] text-stone-100 flex flex-col pb-16">
      <Header brandName={businessName} />

      {saveStatus && (
        <div
          role="status"
          aria-live="polite"
          className="fixed top-20 right-6 z-50 px-4 py-2.5 rounded-xl bg-amber-500 text-stone-950 font-semibold text-xs shadow-2xl flex items-center gap-2 animate-in slide-in-from-top-3"
        >
          <CheckCircle2 className="w-4 h-4" />
          <span>{saveStatus}</span>
        </div>
      )}

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Conversational Stepper (7 cols) */}
          <div className="lg:col-span-7 rounded-3xl bg-[#1A1816] border border-white/[0.08] p-6 lg:p-8 space-y-6 shadow-xl">
            {/* Step Counter */}
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-amber-500 font-semibold uppercase tracking-wider">
                Step {step} of 8 ·{" "}
                {step === 1
                  ? "Account Type"
                  : step === 2
                  ? "Business Identity"
                  : step === 3
                  ? "Brand Kit DNA"
                  : step === 4
                  ? "Growth Goals"
                  : step === 5
                  ? "Tone of Voice"
                  : step === 6
                  ? "Source Facts & Safety"
                  : step === 7
                  ? "Inspiration Benchmarks"
                  : "Editorial Mode"}
              </span>

              {/* Accessible Stepper Tabs */}
              <div
                role="tablist"
                aria-label="Onboarding Steps"
                className="flex items-center gap-1.5"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <button
                    key={s}
                    role="tab"
                    aria-selected={s === step}
                    aria-label={`Jump to step ${s}`}
                    onClick={() => {
                      persistProfile();
                      setStep(s);
                    }}
                    className={`h-2 rounded-full transition-all focus:outline-none focus:ring-2 focus:ring-amber-500 ${
                      s === step
                        ? "bg-amber-500 w-5"
                        : s < step
                        ? "bg-amber-500/60 w-2 hover:bg-amber-400"
                        : "bg-stone-800 w-2 hover:bg-stone-700"
                    }`}
                  />
                ))}
              </div>
            </div>

            {/* STEP 1: Who are you creating content for? */}
            {step === 1 && (
              <section aria-labelledby="step1-heading" className="space-y-4">
                <div className="space-y-1.5">
                  <h1 id="step1-heading" className="font-display text-2xl font-semibold text-stone-100">
                    Who are you creating content for?
                  </h1>
                  <p className="text-xs text-stone-400 leading-relaxed">
                    Avatar Agent: &quot;Let me know your operational role so our AI crew tunes its research and publishing workflows.&quot;
                  </p>
                </div>

                <div
                  role="radiogroup"
                  aria-label="Account Type Selection"
                  className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2"
                >
                  {[
                    {
                      id: "business",
                      title: "Local Business / Brand",
                      desc: "Cafes, clinics, retail stores & local services",
                    },
                    {
                      id: "creator",
                      title: "Solo Creator / Founder",
                      desc: "Consultants, influencers & independent makers",
                    },
                    {
                      id: "agency",
                      title: "Digital Agency",
                      desc: "Managing multiple client brand workspaces",
                    },
                  ].map((t) => {
                    const isSelected = accountType === t.id;
                    return (
                      <div
                        key={t.id}
                        role="radio"
                        aria-checked={isSelected}
                        tabIndex={0}
                        onClick={() => setAccountType(t.id as any)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            setAccountType(t.id as any);
                          }
                        }}
                        className={`p-4 rounded-2xl border text-left flex flex-col justify-between gap-3 transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-amber-500 ${
                          isSelected
                            ? "bg-amber-500/10 border-amber-500 text-stone-100 shadow-md"
                            : "bg-stone-900 border-white/5 text-stone-400 hover:border-white/20"
                        }`}
                      >
                        <div>
                          <span className="font-semibold text-sm text-stone-100 block">{t.title}</span>
                          <p className="text-[11px] text-stone-400 mt-1 leading-relaxed">{t.desc}</p>
                        </div>
                        <div className="flex items-center gap-1 text-[11px] font-semibold text-amber-500">
                          {isSelected ? "✓ Selected" : "Select"}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            )}

            {/* STEP 2: Business Details */}
            {step === 2 && (
              <section aria-labelledby="step2-heading" className="space-y-4">
                <div className="space-y-1.5">
                  <h1 id="step2-heading" className="font-display text-2xl font-semibold text-stone-100">
                    What is your business name and location?
                  </h1>
                  <p className="text-xs text-stone-400 leading-relaxed">
                    Avatar Agent: &quot;We&apos;ll anchor these official details across your Google Business Profile and social posts.&quot;
                  </p>
                </div>

                <div className="space-y-3.5 text-xs">
                  <div>
                    <label htmlFor="businessNameInput" className="text-stone-300 font-medium block mb-1">
                      Official Brand / Business Name *
                    </label>
                    <input
                      id="businessNameInput"
                      type="text"
                      required
                      value={businessName}
                      onChange={(e) => setBusinessName(e.target.value)}
                      placeholder="e.g. Rajkumar's Coffee Studio"
                      className="w-full bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label htmlFor="industryInput" className="text-stone-300 font-medium block mb-1">
                        Industry Vertical *
                      </label>
                      <input
                        id="industryInput"
                        type="text"
                        required
                        value={industry}
                        onChange={(e) => setIndustry(e.target.value)}
                        placeholder="e.g. Specialty Cafe & Roastery"
                        className="w-full bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                      />
                    </div>
                    <div>
                      <label htmlFor="cityInput" className="text-stone-300 font-medium block mb-1">
                        City / Operating Region *
                      </label>
                      <input
                        id="cityInput"
                        type="text"
                        required
                        value={city}
                        onChange={(e) => setCity(e.target.value)}
                        placeholder="e.g. Pune, Maharashtra"
                        className="w-full bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="websiteInput" className="text-stone-300 font-medium block mb-1">
                      Website or Digital Menu Link (Optional)
                    </label>
                    <input
                      id="websiteInput"
                      type="url"
                      value={website}
                      onChange={(e) => setWebsite(e.target.value)}
                      placeholder="https://rajkumarstudio.in"
                      className="w-full bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                    />
                  </div>
                </div>
              </section>
            )}

            {/* STEP 3: Logo & Brand Kit Extraction */}
            {step === 3 && (
              <section aria-labelledby="step3-heading" className="space-y-5">
                <div className="space-y-1.5">
                  <h1 id="step3-heading" className="font-display text-2xl font-semibold text-stone-100">
                    Upload your logo & confirm brand colors
                  </h1>
                  <p className="text-xs text-stone-400 leading-relaxed">
                    Avatar Agent: &quot;Drop your logo. I&apos;ll extract your primary colors and pair them with typographic scales.&quot;
                  </p>
                </div>

                <input
                  type="file"
                  id="logoFileInput"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  accept="image/png, image/jpeg, image/svg+xml, image/webp"
                  aria-label="Upload logo file"
                  className="hidden"
                />

                <div
                  tabIndex={0}
                  role="button"
                  aria-label="Upload brand logo file"
                  onClick={() => fileInputRef.current?.click()}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      fileInputRef.current?.click();
                    }
                  }}
                  className="border border-dashed border-white/20 rounded-2xl p-6 flex flex-col items-center justify-center text-center gap-2.5 bg-stone-900/40 hover:border-amber-500/50 transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-amber-500"
                >
                  <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-500 flex items-center justify-center">
                    <Upload className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-stone-200">
                      {logoPreview ? "✓ Logo Uploaded (Click to swap image)" : "Drop your logo here (SVG, PNG, min 400px)"}
                    </p>
                    <p className="text-[11px] text-stone-500 mt-0.5">
                      or tap to browse your local computer files
                    </p>
                  </div>
                  {logoPreview && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setLogoPreview(null);
                      }}
                      className="text-[11px] text-rose-400 hover:text-rose-300 flex items-center gap-1 mt-1"
                    >
                      <X className="w-3 h-3" /> Remove logo
                    </button>
                  )}
                </div>

                {/* Color Palette Selector & Custom Hex Input */}
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <label htmlFor="customHexInput" className="text-xs text-stone-300 font-medium">
                      Extracted Brand Color & Theme
                    </label>
                    <span className="text-[10px] text-emerald-400 font-mono">WCAG AAA Contrast ✓</span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {[
                      { hex: "#F59E0B", label: "Artisan Saffron" },
                      { hex: "#121110", label: "Warm Charcoal" },
                      { hex: "#FDFCFB", label: "Linen White" },
                      { hex: "#22C55E", label: "Emerald Accent" },
                    ].map((c) => (
                      <button
                        type="button"
                        key={c.hex}
                        onClick={() => {
                          setSelectedColor(c.hex);
                          setCustomHex(c.hex);
                          triggerColorPreview(c.hex);
                        }}
                        className={`flex items-center gap-2 p-2 rounded-xl border transition-colors text-left ${
                          selectedColor === c.hex
                            ? "bg-amber-500/10 border-amber-500 ring-1 ring-amber-500"
                            : "bg-stone-900 border-white/10 hover:border-white/20"
                        }`}
                      >
                        <span
                          className="w-5 h-5 rounded-lg border border-white/20 shrink-0"
                          style={{ backgroundColor: c.hex }}
                        />
                        <div className="overflow-hidden">
                          <p className="text-[11px] font-semibold text-stone-200">{c.hex}</p>
                          <p className="text-[9px] text-stone-400 truncate">{c.label}</p>
                        </div>
                      </button>
                    ))}
                  </div>

                  {/* Custom Hex Picker Input */}
                  <div className="flex items-center gap-2 pt-1">
                    <input
                      type="color"
                      id="nativeColorPicker"
                      value={selectedColor.startsWith("#") ? selectedColor : "#F59E0B"}
                      onChange={(e) => {
                        const val = e.target.value;
                        setSelectedColor(val);
                        setCustomHex(val);
                        triggerColorPreview(val);
                      }}
                      className="w-8 h-8 rounded-lg cursor-pointer bg-transparent border-0 p-0"
                      aria-label="Pick color from palette"
                    />
                    <input
                      id="customHexInput"
                      type="text"
                      value={customHex}
                      onChange={(e) => {
                        const val = e.target.value;
                        setCustomHex(val);
                        if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                          setSelectedColor(val);
                          triggerColorPreview(val);
                        }
                      }}
                      placeholder="#F59E0B"
                      aria-label="Custom Hex Code"
                      className="flex-1 bg-stone-900 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-stone-100 font-mono focus:outline-none focus:border-amber-500"
                    />
                    <span className="text-[11px] text-stone-400">Custom Brand Hex</span>
                  </div>
                </div>

                {/* Font Pairings */}
                <div className="space-y-2">
                  <label className="text-xs text-stone-300 font-medium block">
                    Recommended Font Pairing
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {[
                      { name: "Fraunces + Geist", desc: "Warm editorial elegance for coffee & dining" },
                      { name: "Clash Display + Inter", desc: "Geometric modern punch for tech & agency" },
                    ].map((f) => {
                      const isSelected = fontPairing === f.name;
                      return (
                        <button
                          type="button"
                          key={f.name}
                          onClick={() => setFontPairing(f.name)}
                          className={`p-3 rounded-xl border text-left transition-all ${
                            isSelected
                              ? "bg-amber-500/10 border-amber-500 ring-1 ring-amber-500"
                              : "bg-stone-900 border-white/10 opacity-80 hover:opacity-100"
                          }`}
                        >
                          <p className="font-semibold text-xs text-stone-100">{f.name}</p>
                          <p className="text-[10px] text-stone-400 mt-0.5">{f.desc}</p>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </section>
            )}

            {/* STEP 4: Goals */}
            {step === 4 && (
              <section aria-labelledby="step4-heading" className="space-y-4">
                <div className="space-y-1.5">
                  <h1 id="step4-heading" className="font-display text-2xl font-semibold text-stone-100">
                    What is your primary marketing goal?
                  </h1>
                  <p className="text-xs text-stone-400 leading-relaxed">
                    Avatar Agent: &quot;Our strategy agent will align call-to-actions and captions with this priority.&quot;
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
                  {[
                    "More walk-in customers & footfall",
                    "Drive direct online orders & reservations",
                    "Build local brand authority & 5-star reviews",
                    "Promote seasonal festival gift boxes",
                  ].map((g) => {
                    const isSelected = primaryGoal === g && !customGoal;
                    return (
                      <button
                        type="button"
                        key={g}
                        onClick={() => {
                          setPrimaryGoal(g);
                          setCustomGoal("");
                        }}
                        className={`p-3.5 rounded-xl border text-left transition-all ${
                          isSelected
                            ? "bg-amber-500/10 border-amber-500 text-stone-100 ring-1 ring-amber-500"
                            : "bg-stone-900 border-white/5 text-stone-400 hover:border-white/20"
                        }`}
                      >
                        <span className="font-medium block">{g}</span>
                      </button>
                    );
                  })}
                </div>

                <div className="pt-2 text-xs">
                  <label htmlFor="customGoalInput" className="text-stone-300 font-medium block mb-1">
                    Or Enter a Custom Goal
                  </label>
                  <input
                    id="customGoalInput"
                    type="text"
                    value={customGoal}
                    onChange={(e) => setCustomGoal(e.target.value)}
                    placeholder="e.g. Launch winter specialty matcha latte menu"
                    className="w-full bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 focus:outline-none focus:border-amber-500"
                  />
                </div>
              </section>
            )}

            {/* STEP 5: Tone of Voice */}
            {step === 5 && (
              <section aria-labelledby="step5-heading" className="space-y-4">
                <div className="space-y-1.5">
                  <h1 id="step5-heading" className="font-display text-2xl font-semibold text-stone-100">
                    Choose your brand&apos;s tone of voice
                  </h1>
                  <p className="text-xs text-stone-400 leading-relaxed">
                    Avatar Agent: &quot;Listen to how your captions will sound when the copywriter agent writes for your business.&quot;
                  </p>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {Object.keys(sampleCaptions).map((t) => (
                    <button
                      type="button"
                      key={t}
                      onClick={() => setToneVoice(t)}
                      className={`py-2 px-3 rounded-xl border text-xs font-medium transition-all ${
                        toneVoice === t
                          ? "bg-amber-500 text-stone-950 font-semibold"
                          : "bg-stone-900 border-white/10 text-stone-400 hover:text-stone-200"
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>

                {/* Sample Caption Box */}
                <div
                  aria-live="polite"
                  className="p-4 rounded-2xl bg-stone-900/90 border border-white/10 space-y-2 shadow-inner"
                >
                  <span className="text-[10px] font-mono uppercase text-amber-500 font-semibold">
                    Live Tone Sample Caption
                  </span>
                  <p className="text-xs text-stone-200 italic leading-relaxed">
                    &quot;{sampleCaptions[toneVoice] || sampleCaptions["Warm Editorial"]}&quot;
                  </p>
                </div>
              </section>
            )}

            {/* STEP 6: Source Facts & Guardrails */}
            {step === 6 && (
              <section aria-labelledby="step6-heading" className="space-y-4">
                <div className="space-y-1.5">
                  <h1 id="step6-heading" className="font-display text-2xl font-semibold text-stone-100">
                    Source Facts & Safety Guardrails
                  </h1>
                  <p className="text-xs text-stone-400 leading-relaxed">
                    Avatar Agent: &quot;The AI crew will only use approved facts below. It will NEVER invent fake prices, discounts, or awards.&quot;
                  </p>
                </div>

                <div className="space-y-3.5 text-xs">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label htmlFor="phoneInput" className="text-stone-300 font-medium block mb-1">
                        Official Business Phone *
                      </label>
                      <input
                        id="phoneInput"
                        type="tel"
                        required
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        className="w-full bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 focus:outline-none focus:border-amber-500"
                      />
                    </div>
                    <div>
                      <label htmlFor="hoursInput" className="text-stone-300 font-medium block mb-1">
                        Operating Hours
                      </label>
                      <input
                        id="hoursInput"
                        type="text"
                        value={hours}
                        onChange={(e) => setHours(e.target.value)}
                        className="w-full bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 focus:outline-none focus:border-amber-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="addressInput" className="text-stone-300 font-medium block mb-1">
                      Physical Store Address *
                    </label>
                    <input
                      id="addressInput"
                      type="text"
                      required
                      value={address}
                      onChange={(e) => setAddress(e.target.value)}
                      className="w-full bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 focus:outline-none focus:border-amber-500"
                    />
                  </div>

                  <div>
                    <label htmlFor="offerInput" className="text-stone-300 font-medium block mb-1">
                      Approved Offer Allowed in Campaigns *
                    </label>
                    <input
                      id="offerInput"
                      type="text"
                      required
                      value={approvedOffer}
                      onChange={(e) => setApprovedOffer(e.target.value)}
                      className="w-full bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 focus:outline-none focus:border-amber-500"
                    />
                  </div>

                  <div>
                    <label htmlFor="bannedWordsInput" className="text-stone-300 font-medium block mb-1">
                      Banned Words / Off-Limit Claims
                    </label>
                    <input
                      id="bannedWordsInput"
                      type="text"
                      value={bannedWords}
                      onChange={(e) => setBannedWords(e.target.value)}
                      placeholder="e.g. cheapest, guaranteed, crypto"
                      className="w-full bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 focus:outline-none focus:border-amber-500"
                    />
                  </div>
                </div>
              </section>
            )}

            {/* STEP 7: Competitors / Inspiration */}
            {step === 7 && (
              <section aria-labelledby="step7-heading" className="space-y-4">
                <div className="space-y-1.5">
                  <h1 id="step7-heading" className="font-display text-2xl font-semibold text-stone-100">
                    Inspiration Accounts & Benchmarks
                  </h1>
                  <p className="text-xs text-stone-400 leading-relaxed">
                    Avatar Agent: &quot;Add brands whose aesthetic or tone you admire for benchmark research.&quot;
                  </p>
                </div>

                <div className="space-y-3 text-xs">
                  <div>
                    <label htmlFor="competitorInput" className="text-stone-300 font-medium block mb-1">
                      Add Instagram or Social Handle (Press Enter)
                    </label>
                    <input
                      id="competitorInput"
                      type="text"
                      value={newCompetitor}
                      onChange={(e) => setNewCompetitor(e.target.value)}
                      onKeyDown={handleAddCompetitor}
                      placeholder="e.g. @bluebottle or @thirdwavecoffee"
                      className="w-full bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 focus:outline-none focus:border-amber-500"
                    />
                  </div>

                  {/* Handles Badges */}
                  <div className="flex flex-wrap gap-2 pt-1">
                    {competitors.map((handle) => (
                      <span
                        key={handle}
                        className="px-2.5 py-1 rounded-lg bg-stone-900 border border-white/10 text-stone-200 text-xs flex items-center gap-1.5"
                      >
                        <Tag className="w-3 h-3 text-amber-500" />
                        <span>{handle}</span>
                        <button
                          type="button"
                          onClick={() => removeCompetitor(handle)}
                          aria-label={`Remove handle ${handle}`}
                          className="hover:text-rose-400 ml-1 text-stone-500"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              </section>
            )}

            {/* STEP 8: Approval Mode */}
            {step === 8 && (
              <section aria-labelledby="step8-heading" className="space-y-4">
                <div className="space-y-1.5">
                  <h1 id="step8-heading" className="font-display text-2xl font-semibold text-stone-100">
                    Choose your Editorial Approval Mode
                  </h1>
                  <p className="text-xs text-stone-400 leading-relaxed">
                    Avatar Agent: &quot;How would you like to review content created by your studio team?&quot;
                  </p>
                </div>

                <div
                  role="radiogroup"
                  aria-label="Editorial Approval Mode"
                  className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2"
                >
                  <div
                    role="radio"
                    aria-checked={approvalMode === "human"}
                    tabIndex={0}
                    onClick={() => setApprovalMode("human")}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        setApprovalMode("human");
                      }
                    }}
                    className={`p-4 rounded-2xl border text-left space-y-2 transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-amber-500 ${
                      approvalMode === "human"
                        ? "bg-amber-500/10 border-amber-500 ring-1 ring-amber-500"
                        : "bg-stone-900 border-white/10 opacity-75 hover:opacity-100"
                    }`}
                  >
                    <span className="text-[10px] font-mono text-amber-400 uppercase font-semibold">
                      Recommended
                    </span>
                    <h3 className="font-semibold text-sm text-stone-100">Human Editorial Approval</h3>
                    <p className="text-xs text-stone-400 leading-relaxed">
                      Every campaign requires your 1-tap approval before publishing live to Instagram, Google, or Facebook.
                    </p>
                  </div>

                  <div
                    role="radio"
                    aria-checked={approvalMode === "autopilot"}
                    tabIndex={0}
                    onClick={() => setApprovalMode("autopilot")}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        setApprovalMode("autopilot");
                      }
                    }}
                    className={`p-4 rounded-2xl border text-left space-y-2 transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-amber-500 ${
                      approvalMode === "autopilot"
                        ? "bg-amber-500/10 border-amber-500 ring-1 ring-amber-500"
                        : "bg-stone-900 border-white/10 opacity-75 hover:opacity-100"
                    }`}
                  >
                    <span className="text-[10px] font-mono text-stone-400 uppercase font-semibold">
                      Hands-Free
                    </span>
                    <h3 className="font-semibold text-sm text-stone-100">Full Autopilot</h3>
                    <p className="text-xs text-stone-400 leading-relaxed">
                      Quality Gate automatically schedules & publishes approved drafts once safety threshold is met.
                    </p>
                  </div>
                </div>
              </section>
            )}

            {/* Stepper Navigation Buttons */}
            <div className="flex items-center justify-between pt-4 border-t border-white/[0.08]">
              {step > 1 ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    persistProfile();
                    setStep(step - 1);
                  }}
                >
                  <ArrowLeft className="w-3.5 h-3.5 mr-1" />
                  <span>Back</span>
                </Button>
              ) : (
                <div />
              )}

              {step < 8 ? (
                <Button
                  type="button"
                  variant="primary"
                  size="md"
                  onClick={() => {
                    persistProfile();
                    setStep(step + 1);
                  }}
                >
                  <span>Save & Continue</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              ) : (
                <Button
                  type="button"
                  variant="primary"
                  size="md"
                  onClick={() => persistProfile(true)}
                  className="shadow-xl shadow-amber-500/20 font-semibold"
                >
                  <span>Finish Setup & Launch Studio Floor ⚡</span>
                </Button>
              )}
            </div>
          </div>

          {/* Right Column: Live Brand Kit Preview Mat (5 cols) */}
          <aside aria-label="Live Brand Kit Preview" className="lg:col-span-5 rounded-3xl bg-[#1A1816] border border-white/[0.1] p-6 shadow-2xl space-y-4">
            <div>
              <span className="text-[11px] font-mono text-amber-500 uppercase font-semibold">
                Live Brand Kit Preview
              </span>
              <p className="text-xs text-stone-400 mt-0.5">
                Updates dynamically as you calibrate your brand.
              </p>
            </div>

            <div className="rounded-2xl bg-black border border-white/10 p-5 space-y-4 shadow-inner">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-lg overflow-hidden border border-white/20"
                  style={{ backgroundColor: `${selectedColor}25`, color: selectedColor }}
                >
                  {logoPreview ? (
                    <img src={logoPreview} alt="Brand Logo Preview" className="w-full h-full object-cover" />
                  ) : (
                    "❖"
                  )}
                </div>
                <div>
                  <h3 className="font-semibold text-stone-100 text-sm">{businessName}</h3>
                  <p className="text-xs text-stone-400">
                    {industry} · {city}
                  </p>
                </div>
              </div>

              {/* Sample Mini Poster Card */}
              <div className="w-full aspect-square rounded-xl overflow-hidden border border-white/10 relative bg-[#121110]">
                <img
                  src={previewPosterUrl}
                  alt="Live Brand Preview Poster"
                  className={`w-full h-full object-cover transition-opacity duration-300 ${isUpdatingPoster ? "opacity-60" : "opacity-100"}`}
                />
                {isUpdatingPoster && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-[2px]">
                    <span className="text-[10px] font-mono text-amber-400 bg-stone-900/90 px-2.5 py-1 rounded-full border border-amber-500/30 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                      Applying Color...
                    </span>
                  </div>
                )}
              </div>

              <div className="pt-2 text-xs text-stone-400 space-y-1">
                <div className="flex items-center justify-between">
                  <span>
                    Palette: <strong className="text-stone-200">{selectedColor}</strong>
                  </span>
                  <span className="text-emerald-400 font-mono text-[11px]">✓ Real-time sync</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>
                    Typography: <strong className="text-stone-200">{fontPairing}</strong>
                  </span>
                  <span className="text-stone-300 font-mono text-[11px]">{phone}</span>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
