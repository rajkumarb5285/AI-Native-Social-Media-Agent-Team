"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Search, Sparkles, ChevronDown, CheckCircle2, ShieldCheck, LogIn, LogOut, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { AuthModal } from "@/components/auth/auth-modal";
import { getAuthToken, removeAuthToken, authService } from "@/lib/api";

interface HeaderProps {
  onOpenCommand?: () => void;
  brandName?: string;
}

export function Header({
  onOpenCommand,
  brandName = "Rajkumar's Coffee Studio",
}: HeaderProps) {
  const pathname = usePathname();
  const [brand, setBrand] = React.useState(brandName);
  const [isAuthModalOpen, setIsAuthModalOpen] = React.useState(false);
  const [currentUser, setCurrentUser] = React.useState<any>(null);

  React.useEffect(() => {
    const readBrand = () => {
      try {
        const saved = localStorage.getItem("nexus_brand_profile");
        if (saved) {
          const p = JSON.parse(saved);
          if (p.businessName) setBrand(p.businessName);
        }
      } catch (_) {}
    };
    readBrand();
    window.addEventListener("storage", readBrand);
    return () => window.removeEventListener("storage", readBrand);
  }, [brandName]);

  React.useEffect(() => {
    const token = getAuthToken();
    if (token) {
      authService.getProfile().then((res) => {
        if (res.user) setCurrentUser(res.user);
      }).catch(() => {
        // Fallback demo user
        setCurrentUser({ email: "rajkumar@studio.local", role: "admin" });
      });
    }
  }, []);

  const handleSignOut = () => {
    removeAuthToken();
    setCurrentUser(null);
  };

  const navLinks = [
    { href: "/", label: "Mission Control" },
    { href: "/studio", label: "Studio Floor" },
    { href: "/review", label: "Review & Approve" },
    { href: "/connect", label: "Channels" },
    { href: "/onboarding", label: "Brand Kit Setup" },
  ];

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-white/[0.08] bg-[#121110]/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
          {/* Brand Switcher */}
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-500 font-bold text-sm group-hover:border-amber-500 transition-colors">
                ❖
              </div>
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-stone-100 tracking-tight text-sm">
                  {currentUser?.business_name || brand}
                </span>
                <ChevronDown className="w-3.5 h-3.5 text-stone-500 group-hover:text-stone-300 transition-colors" />
              </div>
            </Link>

            {/* Desktop Nav Links */}
            <nav className="hidden md:flex items-center gap-1">
              {navLinks.map((link) => {
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
                      isActive
                        ? "bg-white/[0.08] text-amber-400 font-semibold"
                        : "text-stone-400 hover:text-stone-200 hover:bg-white/[0.04]"
                    )}
                  >
                    {link.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Global Omnibar & Health Beacon */}
          <div className="flex items-center gap-3">
            <button
              onClick={onOpenCommand}
              className="hidden sm:flex items-center gap-3 px-3 py-1.5 rounded-lg bg-stone-900/60 border border-white/10 text-stone-400 hover:text-stone-200 hover:border-white/20 text-xs transition-colors"
            >
              <Search className="w-3.5 h-3.5" />
              <span>Search or command...</span>
              <kbd className="px-1.5 py-0.5 rounded bg-stone-800 text-[10px] font-mono text-stone-400 border border-white/10">
                ⌘K
              </kbd>
            </button>

            {/* Channel Health Beacon */}
            <Link
              href="/connect"
              className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium hover:border-emerald-500/40 transition-colors"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>3 Live</span>
            </Link>

            {/* User Profile or Sign In Button */}
            {currentUser ? (
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-stone-800 border border-white/15 flex items-center justify-center text-xs font-semibold text-stone-200 select-none">
                  {currentUser.email ? currentUser.email.slice(0, 2).toUpperCase() : "RP"}
                </div>
                <button
                  onClick={handleSignOut}
                  title="Sign Out"
                  className="p-1.5 text-stone-400 hover:text-rose-400 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setIsAuthModalOpen(true)}
                className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-amber-500 text-stone-950 font-semibold text-xs hover:bg-amber-400 transition-colors shadow-sm"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In / Google</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Auth Modal with Google OAuth & MFA */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onSuccess={(user) => {
          setCurrentUser(user);
        }}
      />
    </>
  );
}
