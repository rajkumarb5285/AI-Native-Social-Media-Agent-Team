"use client";

import * as React from "react";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ShieldCheck, ArrowRight, AlertCircle, Sparkles } from "lucide-react";

function LoginContent() {
  const searchParams = useSearchParams();
  const returnTo = searchParams.get("return_to") || "/studio";
  const authError = searchParams.get("auth_error");

  const [isLoading, setIsLoading] = React.useState(false);

  const handleGoogleSignIn = () => {
    setIsLoading(true);
    // Sanitize return_to
    const safeReturnTo = returnTo.startsWith("/") && !returnTo.startsWith("//") ? returnTo : "/studio";
    // Full-page redirect to Google OAuth login endpoint
    window.location.href = `/auth/google/login?return_to=${encodeURIComponent(safeReturnTo)}`;
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-center items-center px-4 py-12 relative overflow-hidden">
      {/* Background ambient glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[540px] h-[540px] bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[380px] h-[380px] bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-950/80 border border-indigo-700/40 text-indigo-300 text-xs font-medium tracking-wide mb-4 shadow-inner">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            AI-Native Social Media Team SaaS
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">
            Sign in to your Workspace
          </h1>
          <p className="text-sm text-slate-400 max-w-sm mx-auto">
            Autonomous AI research, visual design, and multi-channel publishing tailored strictly to your business.
          </p>
        </div>

        {/* Auth Error Banner if redirected back with error */}
        {authError && (
          <div className="mb-6 p-4 rounded-xl bg-red-950/50 border border-red-800/60 text-red-200 text-sm flex items-start gap-3 backdrop-blur-sm">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-300">Sign-in Error</p>
              <p className="text-xs text-red-200/90 mt-0.5">{authError}</p>
            </div>
          </div>
        )}

        {/* Card */}
        <div className="p-8 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-2xl backdrop-blur-xl">
          <div className="space-y-6">
            <div className="text-xs text-slate-400 text-center font-medium">
              Enterprise Google Identity Verification
            </div>

            {/* Google OAuth Button */}
            <button
              onClick={handleGoogleSignIn}
              disabled={isLoading}
              className="w-full py-3.5 px-5 rounded-xl bg-white hover:bg-slate-100 text-slate-900 font-semibold text-sm flex items-center justify-center gap-3 transition-all duration-200 shadow-md hover:shadow-lg hover:scale-[1.01] active:scale-[0.99] disabled:opacity-75 disabled:pointer-events-none"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-slate-800 border-t-transparent rounded-full animate-spin" />
              ) : (
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                  />
                </svg>
              )}
              <span>{isLoading ? "Redirecting to Google..." : "Continue with Google"}</span>
              {!isLoading && <ArrowRight className="w-4 h-4 ml-auto text-slate-400" />}
            </button>

            <div className="pt-4 border-t border-slate-800/80 space-y-3">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Zero demo data. Real workspace generated per client.</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Strict OpenID Connect PKCE verification with Google JWKS.</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <p className="mt-8 text-center text-xs text-slate-500">
          By signing in, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-950 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
