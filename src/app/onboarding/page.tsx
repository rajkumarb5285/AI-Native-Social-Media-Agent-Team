"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/ui/header";
import { Button } from "@/components/ui/button";
import {
  Check,
  Sparkles,
  Upload,
  ArrowRight,
  ArrowLeft,
  Building2,
  Globe,
  Phone,
  MapPin,
  Tag,
  ShieldAlert,
  Clock,
  Palette,
  Layers,
  Plus,
  Trash2,
  CheckCircle2,
  Sliders,
  DollarSign,
  AlertTriangle
} from "lucide-react";
import { fetchApi } from "@/lib/api";

const INDUSTRY_TAXONOMY = [
  { id: "sneakers_streetwear", name: "Sneakers & Streetwear", desc: "Bold, high-contrast, diagonal energy, product cutouts" },
  { id: "fashion_boutique", name: "Fashion Boutique", desc: "Editorial, generous whitespace, serif display, elegant" },
  { id: "salon_spa", name: "Salon, Spa & Beauty", desc: "Soft organic tones, line art, serene, portrait-focused" },
  { id: "restaurant_cafe", name: "Restaurant, Cafe & Bakery", desc: "Warm, appetizing, macro food, rich sensory tones" },
  { id: "gym_fitness", name: "Gym & Fitness", desc: "High contrast, dark mode, dynamic angles, metric stats" },
  { id: "real_estate", name: "Real Estate & Architecture", desc: "Clean, trustworthy, structured grids, architectural heroes" },
  { id: "clinic_healthcare", name: "Clinic & Healthcare (Regulated)", desc: "Calm blues/greens, strict factual copy, zero false medical claims" },
  { id: "jewelry_luxury", name: "Jewelry & Luxury Goods", desc: "Dark or ivory, serif typography, macro product focus, gold accents" },
  { id: "education_coaching", name: "Education & Coaching", desc: "Friendly, structured info blocks, inspirational, clear CTAs" },
  { id: "electronics_tech", name: "Electronics & Tech", desc: "Sleek dark UI, restrained gradients, specification highlights" },
  { id: "auto_bikes", name: "Automotive & Motorcycles", desc: "Dynamic, metallic, angled speed lines, vehicle focus" },
  { id: "travel_tourism", name: "Travel & Tourism", desc: "Vibrant full-bleed landscapes, postcard motifs, adventurous" },
  { id: "events_festivals", name: "Events & Festivals", desc: "Ornate, culturally verified motifs, celebratory date blocks" },
  { id: "local_services", name: "Local Services (Repair, Home)", desc: "Practical, trustworthy, direct contact blocks, service highlights" }
];

const BUSINESS_MODELS = [
  { id: "physical_products", name: "Physical Products & Retail", icon: "👟" },
  { id: "services", name: "Services & Appointments", icon: "💇" },
  { id: "food_beverage", name: "Food & Beverage", icon: "🍽️" },
  { id: "real_estate", name: "Property & Real Estate", icon: "🏢" },
  { id: "healthcare", name: "Healthcare & Wellness", icon: "🩺" },
  { id: "b2b_tech", name: "B2B & Technology", icon: "💻" },
  { id: "education", name: "Education & Courses", icon: "🎓" },
  { id: "creator", name: "Creator & Personal Brand", icon: "✨" }
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = React.useState(1);
  const [isSaving, setIsSaving] = React.useState(false);
  const [saveMessage, setSaveMessage] = React.useState<string | null>(null);

  // 1. Identity & Business Model
  const [businessName, setBusinessName] = React.useState("");
  const [legalName, setLegalName] = React.useState("");
  const [website, setWebsite] = React.useState("");
  const [businessModel, setBusinessModel] = React.useState("physical_products");
  const [region, setRegion] = React.useState("US");
  const [timezone, setTimezone] = React.useState("America/New_York");

  // 2. Industry & Offerings
  const [industryPrimary, setIndustryPrimary] = React.useState("");
  const [offeringsDescription, setOfferingsDescription] = React.useState("");
  const [offerings, setOfferings] = React.useState<Array<{ name: string; price: string; description: string; is_bestseller: boolean; image_url?: string }>>([]);
  const [newOffName, setNewOffName] = React.useState("");
  const [newOffPrice, setNewOffPrice] = React.useState("");
  const [newOffDesc, setNewOffDesc] = React.useState("");
  const [newOffBestseller, setNewOffBestseller] = React.useState(false);
  const [newOffImage, setNewOffImage] = React.useState("");

  // 3. Audience & Positioning
  const [positioning, setPositioning] = React.useState<"budget" | "mid" | "premium" | "luxury">("mid");
  const [audienceAge, setAudienceAge] = React.useState("20-45");
  const [audienceLocation, setAudienceLocation] = React.useState("");
  const [personalityTraits, setPersonalityTraits] = React.useState<string[]>(["Modern", "Confident"]);

  // 4. Brand Assets & Visual Identity
  const [logoUrl, setLogoUrl] = React.useState("");
  const [primaryColor, setPrimaryColor] = React.useState("#6366f1");
  const [secondaryColor, setSecondaryColor] = React.useState("#f59e0b");
  const [displayFont, setDisplayFont] = React.useState("Inter");
  const [bodyFont, setBodyFont] = React.useState("Inter");

  // 5. Source Facts & Guardrails
  const [phone, setPhone] = React.useState("");
  const [address, setAddress] = React.useState("");
  const [hours, setHours] = React.useState("");
  const [approvedOffer, setApprovedOffer] = React.useState("");
  const [bannedWords, setBannedWords] = React.useState("");
  const [complianceRules, setComplianceRules] = React.useState("");
  const [approvalMode, setApprovalMode] = React.useState<"human" | "autopilot">("human");

  // Load existing draft if any (starts 100% empty for new users)
  React.useEffect(() => {
    async function loadDraft() {
      try {
        const res = await fetchApi("/api/profile");
        if (res && res.exists) {
          if (res.business_name) setBusinessName(res.business_name);
          if (res.legal_name) setLegalName(res.legal_name);
          if (res.website) setWebsite(res.website);
          if (res.business_model) setBusinessModel(res.business_model);
          if (res.region) setRegion(res.region);
          if (res.timezone) setTimezone(res.timezone);
          if (res.industry_primary) setIndustryPrimary(res.industry_primary);
          if (res.offerings_description) setOfferingsDescription(res.offerings_description);
          if (res.positioning) setPositioning(res.positioning);
          if (res.logo_url) setLogoUrl(res.logo_url);
          if (res.primary_color) setPrimaryColor(res.primary_color);
          if (res.secondary_color) setSecondaryColor(res.secondary_color);
          if (res.display_font) setDisplayFont(res.display_font);
          if (res.body_font) setBodyFont(res.body_font);
          if (res.phone) setPhone(res.phone);
          if (res.address) setAddress(res.address);
          if (res.approval_mode) setApprovalMode(res.approval_mode);
        }

        const offRes = await fetchApi("/api/offerings");
        if (offRes && offRes.offerings) {
          setOfferings(offRes.offerings);
        }
      } catch (_) {}
    }
    loadDraft();
  }, []);

  const handleAddOffering = async () => {
    if (!newOffName.trim()) return;
    const item = {
      name: newOffName.trim(),
      price: newOffPrice.trim(),
      description: newOffDesc.trim(),
      is_bestseller: newOffBestseller,
      image_url: newOffImage.trim() || undefined
    };
    try {
      await fetchApi("/api/offerings", {
        method: "POST",
        body: JSON.stringify(item)
      });
      setOfferings((prev) => [...prev, item]);
      setNewOffName("");
      setNewOffPrice("");
      setNewOffDesc("");
      setNewOffBestseller(false);
      setNewOffImage("");
    } catch (err: any) {
      alert("Failed to save offering: " + err.message);
    }
  };

  const saveProfileData = async (status: "draft" | "complete" = "draft") => {
    setIsSaving(true);
    setSaveMessage(null);
    try {
      const payload = {
        business_name: businessName.trim() || "Untitled Business",
        legal_name: legalName.trim(),
        category: industryPrimary,
        industry_primary: industryPrimary,
        industry_sub: "",
        offerings_description: offeringsDescription.trim(),
        business_model: businessModel,
        phone: phone.trim(),
        address: address.trim(),
        website: website.trim(),
        tagline: approvedOffer.trim(),
        primary_color: primaryColor,
        secondary_color: secondaryColor,
        display_font: displayFont,
        body_font: bodyFont,
        positioning: positioning,
        personality_json: { traits: personalityTraits },
        audience_json: { age: audienceAge, location: audienceLocation },
        source_facts_json: { phone, address, hours, approved_offer: approvedOffer },
        guardrails_json: { banned_words: bannedWords, compliance_rules: complianceRules },
        region: region,
        timezone: timezone,
        onboarding_status: status,
        approval_mode: approvalMode
      };

      await fetchApi("/api/profile", {
        method: "POST",
        body: JSON.stringify(payload)
      });

      if (status === "complete") {
        router.push("/studio");
      } else {
        setSaveMessage("Draft auto-saved");
        setTimeout(() => setSaveMessage(null), 3000);
      }
    } catch (err: any) {
      setSaveMessage("Save error: " + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleNext = async () => {
    if (step === 1 && !businessName.trim()) {
      alert("Please enter your business name to continue.");
      return;
    }
    if (step === 2 && !industryPrimary) {
      alert("Please select your primary industry vertical.");
      return;
    }
    await saveProfileData("draft");
    setStep((s) => s + 1);
  };

  const handleFinish = async () => {
    if (!businessName.trim() || !industryPrimary) {
      alert("Please ensure business name and industry vertical are filled.");
      return;
    }
    await saveProfileData("complete");
  };

  return (
    <div className="min-h-screen bg-[#121110] text-stone-100 flex flex-col font-sans">
      <Header brandName={businessName || "Register Business"} />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-8 space-y-8">
        {/* Step Indicator Progress Bar */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-stone-400">
            <span>STEP {step} OF 5</span>
            <span className="text-amber-400 font-semibold">
              {step === 1 && "1. Identity & Business Model"}
              {step === 2 && "2. Vertical & Product Offerings"}
              {step === 3 && "3. Audience & Brand Positioning"}
              {step === 4 && "4. Brand Kit & Visual Assets"}
              {step === 5 && "5. Source Facts, Guardrails & Activation"}
            </span>
            {saveMessage && <span className="text-emerald-400 text-xs">{saveMessage}</span>}
          </div>
          <div className="w-full h-1.5 bg-stone-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-amber-500 to-indigo-500 transition-all duration-300"
              style={{ width: `${(step / 5) * 100}%` }}
            />
          </div>
        </div>

        {/* STEP 1: IDENTITY & MODEL */}
        {step === 1 && (
          <div className="rounded-3xl bg-[#1A1816] border border-white/[0.08] p-6 lg:p-8 space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">Business Identity</h2>
              <p className="text-stone-400 text-sm mt-1">
                Enter your real business details. Every field starts blank so your AI agent team builds designs specific to your brand.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-1.5">
                  Business Name *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Sole Vault Sneakers, Radiant Glow Spa, Prestige Realty"
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-stone-900 border border-white/10 text-white placeholder-stone-600 focus:outline-none focus:border-amber-500 text-sm"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-1.5">
                    Legal Name (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Sole Vault Retail LLC"
                    value={legalName}
                    onChange={(e) => setLegalName(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-stone-900 border border-white/10 text-white placeholder-stone-600 focus:outline-none focus:border-amber-500 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-1.5">
                    Website (Optional)
                  </label>
                  <input
                    type="url"
                    placeholder="https://yourstore.com"
                    value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-stone-900 border border-white/10 text-white placeholder-stone-600 focus:outline-none focus:border-amber-500 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-2">
                  Business Model *
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {BUSINESS_MODELS.map((m) => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => setBusinessModel(m.id)}
                      className={`p-3 rounded-xl border text-left flex flex-col justify-between transition-all ${
                        businessModel === m.id
                          ? "bg-amber-500/10 border-amber-500 text-amber-300"
                          : "bg-stone-900 border-white/10 text-stone-400 hover:border-white/20 hover:text-stone-200"
                      }`}
                    >
                      <span className="text-lg mb-1">{m.icon}</span>
                      <span className="text-xs font-medium leading-tight">{m.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-1.5">
                    Primary Region
                  </label>
                  <select
                    value={region}
                    onChange={(e) => setRegion(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-stone-900 border border-white/10 text-white focus:outline-none focus:border-amber-500 text-sm"
                  >
                    <option value="US">United States / Global</option>
                    <option value="IN">India</option>
                    <option value="UK">United Kingdom</option>
                    <option value="EU">European Union</option>
                    <option value="CA">Canada</option>
                    <option value="AU">Australia</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-1.5">
                    Timezone
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. America/New_York or Asia/Kolkata"
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-stone-900 border border-white/10 text-white focus:outline-none focus:border-amber-500 text-sm"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: INDUSTRY VERTICAL & OFFERINGS */}
        {step === 2 && (
          <div className="rounded-3xl bg-[#1A1816] border border-white/[0.08] p-6 lg:p-8 space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">Industry Vertical & Offerings</h2>
              <p className="text-stone-400 text-sm mt-1">
                The visual language, archetype selection, and copy tone of your posters are driven directly by your primary vertical.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-2">
                  Select Primary Industry Vertical *
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-72 overflow-y-auto pr-1">
                  {INDUSTRY_TAXONOMY.map((ind) => (
                    <button
                      key={ind.id}
                      type="button"
                      onClick={() => setIndustryPrimary(ind.id)}
                      className={`p-3.5 rounded-xl border text-left transition-all ${
                        industryPrimary === ind.id
                          ? "bg-amber-500/10 border-amber-500 text-amber-300 shadow-sm"
                          : "bg-stone-900 border-white/10 text-stone-300 hover:border-white/20"
                      }`}
                    >
                      <div className="font-semibold text-sm text-white mb-0.5">{ind.name}</div>
                      <div className="text-[11px] text-stone-400 line-clamp-1">{ind.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-1.5">
                  What do you sell or offer? (Free-text brief for AI understanding)
                </label>
                <textarea
                  rows={2}
                  placeholder="e.g. Exclusive limited-edition street sneakers, deadstock retro Jordans, and premium sneaker cleaning kits."
                  value={offeringsDescription}
                  onChange={(e) => setOfferingsDescription(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-stone-900 border border-white/10 text-white placeholder-stone-600 focus:outline-none focus:border-amber-500 text-sm"
                />
              </div>

              {/* Offerings list */}
              <div className="pt-2 border-t border-white/[0.08] space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono">
                    Product & Service Catalog ({offerings.length})
                  </h3>
                </div>

                {offerings.length > 0 && (
                  <div className="space-y-2">
                    {offerings.map((item, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-stone-900 border border-white/10 flex items-center justify-between text-xs"
                      >
                        <div className="space-y-0.5">
                          <span className="font-semibold text-white">{item.name}</span>
                          {item.price && <span className="text-amber-400 font-mono ml-2">{item.price}</span>}
                          {item.is_bestseller && (
                            <span className="ml-2 px-1.5 py-0.5 bg-amber-500/20 text-amber-300 rounded text-[10px]">
                              Bestseller
                            </span>
                          )}
                          {item.description && <p className="text-stone-400 text-[11px]">{item.description}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Add offering form */}
                <div className="p-4 rounded-xl bg-stone-900/60 border border-white/10 space-y-3">
                  <span className="text-xs font-medium text-stone-300">Add an offering or hero product:</span>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                    <input
                      type="text"
                      placeholder="Item name (e.g. Air Retro High '85)"
                      value={newOffName}
                      onChange={(e) => setNewOffName(e.target.value)}
                      className="px-3 py-2 rounded-lg bg-stone-900 border border-white/10 text-white text-xs focus:outline-none focus:border-amber-500"
                    />
                    <input
                      type="text"
                      placeholder="Price (e.g. $190 or Starting at $45)"
                      value={newOffPrice}
                      onChange={(e) => setNewOffPrice(e.target.value)}
                      className="px-3 py-2 rounded-lg bg-stone-900 border border-white/10 text-white text-xs focus:outline-none focus:border-amber-500"
                    />
                    <input
                      type="url"
                      placeholder="Product Cutout URL (optional)"
                      value={newOffImage}
                      onChange={(e) => setNewOffImage(e.target.value)}
                      className="px-3 py-2 rounded-lg bg-stone-900 border border-white/10 text-white text-xs focus:outline-none focus:border-amber-500"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <label className="flex items-center gap-2 text-xs text-stone-400 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={newOffBestseller}
                        onChange={(e) => setNewOffBestseller(e.target.checked)}
                        className="rounded bg-stone-800 border-white/20 text-amber-500 focus:ring-0"
                      />
                      <span>Mark as best-seller / hero item</span>
                    </label>
                    <button
                      type="button"
                      onClick={handleAddOffering}
                      className="px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      Add to Catalog
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* STEP 3: AUDIENCE & POSITIONING */}
        {step === 3 && (
          <div className="rounded-3xl bg-[#1A1816] border border-white/[0.08] p-6 lg:p-8 space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">Audience & Brand Positioning</h2>
              <p className="text-stone-400 text-sm mt-1">
                Configure your target demographic, market tier, and personality traits.
              </p>
            </div>

            <div className="space-y-5">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-2">
                  Market Positioning Tier *
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { id: "budget", name: "Budget / Value", desc: "Accessible, high utility, deal-oriented" },
                    { id: "mid", name: "Mid-Market", desc: "Reliable, modern, balanced quality" },
                    { id: "premium", name: "Premium", desc: "Elevated design, curated, high craft" },
                    { id: "luxury", name: "Luxury", desc: "Exclusive, understated, bespoke prestige" }
                  ].map((tier) => (
                    <button
                      key={tier.id}
                      type="button"
                      onClick={() => setPositioning(tier.id as any)}
                      className={`p-3.5 rounded-xl border text-left transition-all ${
                        positioning === tier.id
                          ? "bg-amber-500/10 border-amber-500 text-amber-300"
                          : "bg-stone-900 border-white/10 text-stone-400 hover:border-white/20"
                      }`}
                    >
                      <div className="font-semibold text-white text-sm mb-1">{tier.name}</div>
                      <div className="text-[11px] text-stone-400">{tier.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-1.5">
                    Target Age Demographic
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. 18-35 or Working Professionals 25-50"
                    value={audienceAge}
                    onChange={(e) => setAudienceAge(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-stone-900 border border-white/10 text-white placeholder-stone-600 focus:outline-none focus:border-amber-500 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-1.5">
                    Location / Service Area
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Greater Austin Area or Nationwide E-Commerce"
                    value={audienceLocation}
                    onChange={(e) => setAudienceLocation(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-stone-900 border border-white/10 text-white placeholder-stone-600 focus:outline-none focus:border-amber-500 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-2">
                  Brand Personality Traits
                </label>
                <div className="flex flex-wrap gap-2">
                  {["Bold & Confident", "Minimal & Editorial", "Playful & Vibrant", "Warm & Welcoming", "Technical & Precise", "Direct & Practical"].map((trait) => {
                    const isSelected = personalityTraits.includes(trait);
                    return (
                      <button
                        key={trait}
                        type="button"
                        onClick={() => {
                          if (isSelected) {
                            setPersonalityTraits((p) => p.filter((t) => t !== trait));
                          } else {
                            setPersonalityTraits((p) => [...p, trait]);
                          }
                        }}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                          isSelected
                            ? "bg-amber-500 text-stone-950 border-amber-500 font-semibold"
                            : "bg-stone-900 text-stone-400 border-white/10 hover:border-white/20"
                        }`}
                      >
                        {trait}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* STEP 4: BRAND ASSETS & VISUAL IDENTITY */}
        {step === 4 && (
          <div className="rounded-3xl bg-[#1A1816] border border-white/[0.08] p-6 lg:p-8 space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">Brand Kit & Visual Assets</h2>
              <p className="text-stone-400 text-sm mt-1">
                Customize brand colors and font selections. These tokens are injected into all generated posters and flyers.
              </p>
            </div>

            <div className="space-y-5">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-1.5">
                  Brand Logo URL
                </label>
                <input
                  type="url"
                  placeholder="https://yourstore.com/logo.png"
                  value={logoUrl}
                  onChange={(e) => setLogoUrl(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-stone-900 border border-white/10 text-white placeholder-stone-600 focus:outline-none focus:border-amber-500 text-sm"
                />
                <span className="text-[11px] text-stone-500 mt-1 block">
                  Leave empty if you don't have an image logo; the poster designer will render a styled typographic wordmark.
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-2">
                    Primary Brand Color
                  </label>
                  <div className="flex items-center gap-3">
                    <input
                      type="color"
                      value={primaryColor}
                      onChange={(e) => setPrimaryColor(e.target.value)}
                      className="w-10 h-10 rounded-lg cursor-pointer bg-transparent border-0"
                    />
                    <input
                      type="text"
                      value={primaryColor}
                      onChange={(e) => setPrimaryColor(e.target.value)}
                      className="px-3 py-2 rounded-lg bg-stone-900 border border-white/10 text-white font-mono text-xs focus:outline-none focus:border-amber-500 uppercase"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-2">
                    Secondary Accent Color
                  </label>
                  <div className="flex items-center gap-3">
                    <input
                      type="color"
                      value={secondaryColor}
                      onChange={(e) => setSecondaryColor(e.target.value)}
                      className="w-10 h-10 rounded-lg cursor-pointer bg-transparent border-0"
                    />
                    <input
                      type="text"
                      value={secondaryColor}
                      onChange={(e) => setSecondaryColor(e.target.value)}
                      className="px-3 py-2 rounded-lg bg-stone-900 border border-white/10 text-white font-mono text-xs focus:outline-none focus:border-amber-500 uppercase"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-1.5">
                    Display Headline Font
                  </label>
                  <select
                    value={displayFont}
                    onChange={(e) => setDisplayFont(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-stone-900 border border-white/10 text-white focus:outline-none focus:border-amber-500 text-sm"
                  >
                    <option value="Inter">Inter (Clean Modern Sans)</option>
                    <option value="Fraunces">Fraunces (Warm Editorial Serif)</option>
                    <option value="Outfit">Outfit (Bold Geometric)</option>
                    <option value="Cinzel">Cinzel (Luxury Classical Serif)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-1.5">
                    Body & Subline Font
                  </label>
                  <select
                    value={bodyFont}
                    onChange={(e) => setBodyFont(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-stone-900 border border-white/10 text-white focus:outline-none focus:border-amber-500 text-sm"
                  >
                    <option value="Inter">Inter (Optimized Legibility)</option>
                    <option value="Roboto">Roboto (Neutral Sans)</option>
                    <option value="Geist">Geist (High Precision)</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* STEP 5: SOURCE FACTS, GUARDRAILS & ACTIVATION */}
        {step === 5 && (
          <div className="rounded-3xl bg-[#1A1816] border border-white/[0.08] p-6 lg:p-8 space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">Source Facts & Guardrails</h2>
              <p className="text-stone-400 text-sm mt-1">
                Establish facts the AI is strictly permitted to state, and guardrails it must never violate.
              </p>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-1.5">
                    Contact Phone (For Poster Footer)
                  </label>
                  <input
                    type="tel"
                    placeholder="e.g. +1 (512) 555-0199"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-stone-900 border border-white/10 text-white placeholder-stone-600 focus:outline-none focus:border-amber-500 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-1.5">
                    Operating Hours
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Mon-Sat 10:00 AM - 8:00 PM"
                    value={hours}
                    onChange={(e) => setHours(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-stone-900 border border-white/10 text-white placeholder-stone-600 focus:outline-none focus:border-amber-500 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-1.5">
                  Physical Address / Location
                </label>
                <input
                  type="text"
                  placeholder="e.g. 104 E 5th St, Austin, TX 78701"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-stone-900 border border-white/10 text-white placeholder-stone-600 focus:outline-none focus:border-amber-500 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-1.5">
                  Approved Promotional Offer / Value Hook
                </label>
                <input
                  type="text"
                  placeholder="e.g. 20% off all retro drops with code RETRO20"
                  value={approvedOffer}
                  onChange={(e) => setApprovedOffer(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-stone-900 border border-white/10 text-white placeholder-stone-600 focus:outline-none focus:border-amber-500 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-rose-400 font-mono mb-1.5 flex items-center gap-1.5">
                  <ShieldAlert className="w-3.5 h-3.5" />
                  Prohibited Claims & Banned Words ("Never Say")
                </label>
                <textarea
                  rows={2}
                  placeholder="e.g. cheapest, guaranteed cure, miracle, fake scarcity, crypto, no-risk"
                  value={bannedWords}
                  onChange={(e) => setBannedWords(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-stone-900 border border-rose-900/30 text-white placeholder-stone-600 focus:outline-none focus:border-rose-500 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-300 font-mono mb-2">
                  Publishing Approval Mode
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setApprovalMode("human")}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      approvalMode === "human"
                        ? "bg-amber-500/10 border-amber-500 text-amber-300"
                        : "bg-stone-900 border-white/10 text-stone-400 hover:border-white/20"
                    }`}
                  >
                    <div className="font-semibold text-white text-sm mb-0.5">Human Approval (Recommended)</div>
                    <div className="text-[11px] text-stone-400">
                      Designs and copy are staged in Review for 1-tap approval before publishing.
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setApprovalMode("autopilot")}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      approvalMode === "autopilot"
                        ? "bg-amber-500/10 border-amber-500 text-amber-300"
                        : "bg-stone-900 border-white/10 text-stone-400 hover:border-white/20"
                    }`}
                  >
                    <div className="font-semibold text-white text-sm mb-0.5">Autonomous Autopilot</div>
                    <div className="text-[11px] text-stone-400">
                      High-confidence designs passing automated QA publish directly on schedule.
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between pt-4 border-t border-white/[0.08]">
          {step > 1 ? (
            <Button
              variant="secondary"
              size="md"
              onClick={() => setStep((s) => s - 1)}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Previous Step
            </Button>
          ) : (
            <div />
          )}

          {step < 5 ? (
            <Button
              variant="primary"
              size="md"
              onClick={handleNext}
              disabled={isSaving}
              className="flex items-center gap-2 font-semibold shadow-md shadow-amber-500/20"
            >
              {isSaving ? "Saving..." : "Save & Continue"}
              <ArrowRight className="w-4 h-4" />
            </Button>
          ) : (
            <Button
              variant="primary"
              size="lg"
              onClick={handleFinish}
              disabled={isSaving}
              className="flex items-center gap-2 font-bold shadow-xl shadow-amber-500/20 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500"
            >
              <Sparkles className="w-4 h-4" />
              {isSaving ? "Activating Team..." : "Complete Registration & Enter Studio"}
            </Button>
          )}
        </div>
      </main>
    </div>
  );
}
