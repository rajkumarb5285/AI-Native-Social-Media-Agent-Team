"use client";

import * as React from "react";
import { X, ShieldCheck, Mail, Lock, ArrowRight, RefreshCw, KeyRound, QrCode } from "lucide-react";
import { Button } from "@/components/ui/button";
import { authService, setAuthToken } from "@/lib/api";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: any) => void;
}

export function AuthModal({ isOpen, onClose, onSuccess }: AuthModalProps) {
  const [mode, setMode] = React.useState<"login" | "register" | "mfa_challenge" | "mfa_setup">("login");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [businessName, setBusinessName] = React.useState("");
  const [enableMfa, setEnableMfa] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  // MFA Challenge State
  const [challengeToken, setChallengeToken] = React.useState("");
  const [otpCode, setOtpCode] = React.useState(["", "", "", "", "", ""]);
  const [countdown, setCountdown] = React.useState(300);

  // MFA Setup State
  const [mfaSecret, setMfaSecret] = React.useState("");
  const [mfaQrCode, setMfaQrCode] = React.useState("");
  const [setupCode, setSetupCode] = React.useState("");

  React.useEffect(() => {
    let timer: any;
    if (mode === "mfa_challenge" && countdown > 0) {
      timer = setInterval(() => setCountdown((c) => c - 1), 1000);
    }
    return () => clearInterval(timer);
  }, [mode, countdown]);

  React.useEffect(() => {
    if (!isOpen || typeof window === "undefined") return;

    const clientId =
      process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ||
      "461486698811-7gmaavot3f8u6tdpdr9lhqe0veiccuiv.apps.googleusercontent.com";

    const setupGsi = () => {
      const google = (window as any).google;
      if (!google?.accounts?.id) return;

      try {
        google.accounts.id.initialize({
          client_id: clientId,
          callback: async (response: any) => {
            if (!response?.credential) return;
            setIsLoading(true);
            setErrorMessage(null);
            try {
              const res = await authService.verifyGoogleCredential(response.credential);
              if (res.mfa_required) {
                setChallengeToken(res.challenge_token);
                setMode("mfa_challenge");
                setCountdown(300);
              } else {
                setAuthToken(res.access_token);
                onSuccess(res.user);
                onClose();
              }
            } catch (err: any) {
              setErrorMessage(err.message || "Google authentication failed");
            } finally {
              setIsLoading(false);
            }
          },
        });

        const container = document.getElementById("googleSignInContainer");
        if (container) {
          container.innerHTML = "";
          google.accounts.id.renderButton(container, {
            theme: "filled_blue",
            size: "large",
            width: 340,
            text: "continue_with",
            shape: "rectangular",
          });
        }
      } catch (e) {
        console.warn("GSI error:", e);
      }
    };

    if (!(window as any).google?.accounts?.id) {
      if (!document.getElementById("google-gsi-client")) {
        const script = document.createElement("script");
        script.id = "google-gsi-client";
        script.src = "https://accounts.google.com/gsi/client";
        script.async = true;
        script.defer = true;
        script.onload = setupGsi;
        document.body.appendChild(script);
      }
    } else {
      setTimeout(setupGsi, 50);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleGoogleLogin = () => {
    setIsLoading(true);
    setErrorMessage(null);

    const google = typeof window !== "undefined" ? (window as any).google : null;
    const clientId =
      process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ||
      "461486698811-7gmaavot3f8u6tdpdr9lhqe0veiccuiv.apps.googleusercontent.com";

    // 1. Preferred Modern Flow: Google Identity Services Token Client Popup
    if (google?.accounts?.oauth2?.initTokenClient) {
      try {
        const client = google.accounts.oauth2.initTokenClient({
          client_id: clientId,
          scope: "openid email profile",
          callback: async (tokenResponse: any) => {
            if (tokenResponse?.error) {
              setIsLoading(false);
              if (tokenResponse.error !== "popup_closed_by_user") {
                setErrorMessage(`Google sign-in error: ${tokenResponse.error_description || tokenResponse.error}`);
              }
              return;
            }
            if (tokenResponse?.access_token) {
              try {
                const res = await authService.verifyGoogleAccessToken(tokenResponse.access_token);
                if (res.mfa_required) {
                  setChallengeToken(res.challenge_token);
                  setMode("mfa_challenge");
                  setCountdown(300);
                } else {
                  setAuthToken(res.access_token);
                  onSuccess(res.user);
                  onClose();
                }
              } catch (err: any) {
                setErrorMessage(err.message || "Google authentication failed");
              } finally {
                setIsLoading(false);
              }
            }
          },
        });
        client.requestAccessToken({ prompt: "select_account" });
        return;
      } catch (err) {
        console.warn("TokenClient popup error, falling back:", err);
      }
    }

    // 2. Direct server redirect fallback
    authService.initiateGoogleLogin();
  };

  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsLoading(true);

    try {
      if (mode === "login") {
        const res = await authService.login(email, password);
        if (res.mfa_required) {
          setChallengeToken(res.challenge_token);
          setMode("mfa_challenge");
          setCountdown(300);
        } else {
          setAuthToken(res.access_token);
          onSuccess(res.user);
          onClose();
        }
      } else {
        const res = await authService.register({
          email,
          password,
          business_name: businessName || "My Business",
          enable_mfa: enableMfa,
        });
        setAuthToken(res.access_token);
        if (res.mfa_setup) {
          setMfaSecret(res.mfa_setup.secret);
          setMfaQrCode(res.mfa_setup.qr_code_base64);
          setMode("mfa_setup");
        } else {
          onSuccess(res.user);
          onClose();
        }
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Authentication failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOtpChange = (index: number, val: string) => {
    if (val.length > 1) val = val[val.length - 1];
    const newOtp = [...otpCode];
    newOtp[index] = val;
    setOtpCode(newOtp);

    // Auto-focus next box
    if (val && index < 5) {
      const nextInput = document.getElementById(`otp_input_${index + 1}`);
      nextInput?.focus();
    }
  };

  const handleVerifyMfa = async (e: React.FormEvent) => {
    e.preventDefault();
    const fullCode = otpCode.join("");
    if (fullCode.length < 6) {
      setErrorMessage("Please enter the full 6-digit code");
      return;
    }
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await authService.verifyMfa(challengeToken, fullCode);
      setAuthToken(res.access_token);
      onSuccess(res.user);
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || "Invalid verification code");
    } finally {
      setIsLoading(false);
    }
  };

  const handleActivateMfaSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (setupCode.length < 6) {
      setErrorMessage("Enter the 6-digit code from Google Authenticator");
      return;
    }
    setIsLoading(true);
    setErrorMessage(null);
    try {
      await authService.activateMfa(mfaSecret, setupCode);
      onSuccess({ email, business_name: businessName });
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to activate Two-Factor Authentication");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in">
      <div className="relative w-full max-w-md rounded-3xl bg-[#1A1816] border border-white/15 p-6 sm:p-8 shadow-2xl space-y-6">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-stone-400 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="text-center space-y-1.5">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-500 flex items-center justify-center mx-auto text-lg font-bold">
            ❖
          </div>
          <h2 className="font-display text-2xl font-semibold text-stone-100">
            {mode === "login"
              ? "Sign in to Nexus Studio"
              : mode === "register"
              ? "Create Business Account"
              : mode === "mfa_challenge"
              ? "Two-Factor Verification"
              : "Set Up Google Authenticator"}
          </h2>
          <p className="text-xs text-stone-400">
            {mode === "mfa_challenge"
              ? "Enter the 6-digit code from Google Authenticator or your email"
              : mode === "mfa_setup"
              ? "Scan the QR code with Google Authenticator to enable 2FA"
              : "Autonomous social media creative team for modern business"}
          </p>
        </div>

        {errorMessage && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
            {errorMessage}
          </div>
        )}

        {/* 1. Normal Login & Register Views */}
        {(mode === "login" || mode === "register") && (
          <div className="space-y-4">
            {/* Native Google One-Tap & Sign-In Button Container */}
            <div id="googleSignInContainer" className="w-full flex justify-center empty:hidden min-h-[44px]"></div>

            {/* Google OAuth Button */}
            <button
              type="button"
              onClick={handleGoogleLogin}
              className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl bg-white text-stone-900 font-semibold text-sm hover:bg-stone-100 transition-all shadow-md active:scale-[0.98]"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
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
              <span>Continue with Google</span>
            </button>

            <div className="relative flex items-center justify-center my-3">
              <div className="w-full border-t border-white/10" />
              <span className="absolute px-3 bg-[#1A1816] text-[11px] text-stone-500 uppercase tracking-wider">
                Or with email
              </span>
            </div>

            {/* Email & Password Form */}
            <form onSubmit={handleEmailAuth} className="space-y-3 text-xs">
              {mode === "register" && (
                <div>
                  <label className="text-stone-300 font-medium">Business / Brand Name</label>
                  <input
                    type="text"
                    required
                    value={businessName}
                    onChange={(e) => setBusinessName(e.target.value)}
                    placeholder="Rajkumar's Coffee Studio"
                    className="w-full mt-1 bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 placeholder:text-stone-500 focus:outline-none focus:border-amber-500 text-xs"
                  />
                </div>
              )}

              <div>
                <label className="text-stone-300 font-medium">Email Address</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@workspace.local"
                  className="w-full mt-1 bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 placeholder:text-stone-500 focus:outline-none focus:border-amber-500 text-xs"
                />
              </div>

              <div>
                <label className="text-stone-300 font-medium">Password</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full mt-1 bg-stone-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-stone-100 placeholder:text-stone-500 focus:outline-none focus:border-amber-500 text-xs"
                />
              </div>

              {mode === "register" && (
                <label className="flex items-center gap-2 pt-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={enableMfa}
                    onChange={(e) => setEnableMfa(e.target.checked)}
                    className="rounded border-white/20 text-amber-500 focus:ring-0"
                  />
                  <span className="text-[11px] text-stone-300">
                    Enable Two-Factor Authentication (Recommended)
                  </span>
                </label>
              )}

              <Button
                type="submit"
                variant="primary"
                size="lg"
                isLoading={isLoading}
                className="w-full mt-2 font-semibold shadow-lg shadow-amber-500/20"
              >
                {mode === "login" ? "Sign In to Workspace" : "Register Business Account"}
              </Button>
            </form>

            {/* Mode Switcher */}
            <div className="text-center pt-2">
              <button
                onClick={() => setMode(mode === "login" ? "register" : "login")}
                className="text-xs text-amber-400 hover:text-amber-300 transition-colors"
              >
                {mode === "login"
                  ? "Don't have an account? Sign up"
                  : "Already registered? Sign in"}
              </button>
            </div>
          </div>
        )}

        {/* 2. MFA Challenge (6-Digit OTP Box View) */}
        {mode === "mfa_challenge" && (
          <form onSubmit={handleVerifyMfa} className="space-y-5 text-center">
            <div className="flex items-center justify-center gap-2.5">
              {otpCode.map((digit, idx) => (
                <input
                  key={idx}
                  id={`otp_input_${idx}`}
                  type="text"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleOtpChange(idx, e.target.value)}
                  className="w-11 h-12 rounded-xl bg-stone-900 border border-white/15 text-center text-lg font-mono text-amber-400 focus:outline-none focus:border-amber-500"
                />
              ))}
            </div>

            <div className="text-xs text-stone-400">
              <span>Code valid for </span>
              <span className="font-mono text-amber-400">
                {Math.floor(countdown / 60)}:{(countdown % 60).toString().padStart(2, "0")}
              </span>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isLoading}
              className="w-full font-semibold shadow-lg shadow-amber-500/20"
            >
              Verify & Unlock Studio Floor
            </Button>

            <button
              type="button"
              onClick={() => authService.sendOtp(challengeToken)}
              className="text-xs text-stone-400 hover:text-stone-200 transition-colors"
            >
              Resend 6-Digit Email OTP
            </button>
          </form>
        )}

        {/* 3. MFA Setup (QR Code View) */}
        {mode === "mfa_setup" && (
          <form onSubmit={handleActivateMfaSetup} className="space-y-4 text-center text-xs">
            {mfaQrCode ? (
              <div className="w-48 h-48 mx-auto rounded-2xl overflow-hidden p-2 bg-white flex items-center justify-center">
                <img src={mfaQrCode} alt="TOTP QR Code" className="w-full h-full" />
              </div>
            ) : (
              <div className="p-3 bg-stone-900 rounded-xl font-mono text-[11px] text-amber-400 break-all">
                Secret: {mfaSecret}
              </div>
            )}

            <div>
              <label className="text-stone-300 font-medium">
                Enter 6-digit code shown in Google Authenticator
              </label>
              <input
                type="text"
                maxLength={6}
                value={setupCode}
                onChange={(e) => setSetupCode(e.target.value)}
                placeholder="123456"
                className="w-full mt-1 bg-stone-900 border border-white/15 rounded-xl px-4 py-2.5 text-center font-mono text-lg tracking-widest text-amber-400 focus:outline-none focus:border-amber-500"
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isLoading}
              className="w-full font-semibold shadow-lg shadow-amber-500/20"
            >
              Verify & Complete Setup
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}
