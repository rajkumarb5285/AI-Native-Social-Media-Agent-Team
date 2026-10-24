import { Client, Account, OAuthProvider } from "appwrite";

let rawEndpoint = process.env.NEXT_PUBLIC_APPWRITE_ENDPOINT || "https://fra.cloud.appwrite.io/v1";
if (rawEndpoint.includes("cloud.appwrite.io") && !rawEndpoint.includes("fra.cloud.appwrite.io")) {
  rawEndpoint = "https://fra.cloud.appwrite.io/v1";
}
const APPWRITE_ENDPOINT = rawEndpoint;
const APPWRITE_PROJECT_ID = process.env.NEXT_PUBLIC_APPWRITE_PROJECT_ID || process.env.NEXT_PUBLIC_APPWRITE_PROJECT || "6adb9d5e003b622dd710";
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// Initialize Appwrite Client for real Google OAuth 2.0
let appwriteClient: Client | null = null;
let appwriteAccount: Account | null = null;

if (typeof window !== "undefined") {
  try {
    appwriteClient = new Client().setEndpoint(APPWRITE_ENDPOINT).setProject(APPWRITE_PROJECT_ID);
    appwriteAccount = new Account(appwriteClient);
  } catch (err) {
    console.warn("Appwrite init error:", err);
  }
}

export function getAuthToken(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("agent_team_token") || "";
}

export function setAuthToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("agent_team_token", token);
  }
}

export function removeAuthToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("agent_team_token");
    localStorage.removeItem("agent_team_user");
  }
}

export async function fetchApi<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errorJson = await res.json();
      errorDetail = errorJson.detail || errorJson.message || errorDetail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return res.json();
}

// ---------------------------------------------------------------------------
// Authentication & MFA Service
// ---------------------------------------------------------------------------
export const authService = {
  async getDevToken() {
    const data = await fetchApi("/api/auth/token");
    setAuthToken(data.token);
    return data;
  },

  async login(email: string, password: string) {
    return fetchApi("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  async register(data: {
    email: string;
    password: string;
    business_name: string;
    full_name?: string;
    enable_mfa?: boolean;
  }) {
    return fetchApi("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async verifyMfa(challenge_token: string, otp_code: string) {
    return fetchApi("/api/auth/mfa/verify", {
      method: "POST",
      body: JSON.stringify({ challenge_token, otp_code }),
    });
  },

  async sendOtp(challenge_token: string) {
    return fetchApi("/api/auth/otp/send", {
      method: "POST",
      body: JSON.stringify({ challenge_token }),
    });
  },

  async getProfile() {
    return fetchApi("/api/auth/me");
  },

  async getMfaSetup() {
    return fetchApi("/api/auth/mfa/setup", { method: "POST" });
  },

  async activateMfa(secret: string, code: string) {
    return fetchApi("/api/auth/mfa/activate", {
      method: "POST",
      body: JSON.stringify({ secret, code }),
    });
  },

  async verifyGoogleCredential(credential: string) {
    const res = await fetchApi("/api/auth/google", {
      method: "POST",
      body: JSON.stringify({ credential }),
    });
    if (res.access_token) {
      setAuthToken(res.access_token);
      if (res.user) {
        localStorage.setItem("agent_team_user", JSON.stringify(res.user));
      }
    }
    return res;
  },

  async handleAppwriteCallback() {
    if (!appwriteAccount) return null;
    try {
      const apwUser = await appwriteAccount.get();
      const res = await fetchApi("/api/auth/appwrite", {
        method: "POST",
        body: JSON.stringify({
          appwrite_user_id: apwUser.$id,
          email: apwUser.email,
          name: apwUser.name,
          email_verified: apwUser.emailVerification,
        }),
      });
      if (res.access_token) {
        setAuthToken(res.access_token);
        if (res.user) {
          localStorage.setItem("agent_team_user", JSON.stringify(res.user));
        }
        return res.user;
      }
    } catch (err) {
      console.warn("Appwrite Google exchange error:", err);
    }
    return null;
  },

  async verifyGoogleAccessToken(accessToken: string) {
    return fetchApi("/api/auth/google", {
      method: "POST",
      body: JSON.stringify({ access_token: accessToken }),
    });
  },

  async quickAccess() {
    const res = await fetchApi("/api/auth/quick-access", { method: "POST" });
    if (res.access_token) {
      setAuthToken(res.access_token);
      if (res.user) {
        localStorage.setItem("agent_team_user", JSON.stringify(res.user));
      }
    }
    return res;
  },

  initiateGoogleLogin() {
    if (typeof window === "undefined") return;
    const origin = encodeURIComponent(window.location.origin);
    window.location.href = `${API_BASE}/auth/google/login?redirect_origin=${origin}`;
  },
};


// ---------------------------------------------------------------------------
// Agent Studio & Campaign Service
// ---------------------------------------------------------------------------
export const campaignService = {
  async getRuns() {
    return fetchApi("/api/runs");
  },

  async getRun(id: string) {
    return fetchApi(`/api/runs/${id}`);
  },

  async createRun(data: {
    brand: string;
    headline?: string;
    goal: string;
    tone?: string;
    platforms?: string[];
    call_to_action?: string;
    style?: string;
    auto_publish?: boolean;
    primary_color?: string;
  }) {
    return fetchApi("/api/runs", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async approveRun(id: string) {
    return fetchApi(`/api/runs/${id}/approve`, { method: "POST" });
  },

  async publishRun(id: string) {
    return fetchApi(`/api/runs/${id}/publish`, { method: "POST" });
  },

  async renderPoster(data: {
    business_name: string;
    title: string;
    subtitle?: string;
    theme?: string;
    archetype?: string;
    cta?: string;
    phone?: string;
    address?: string;
    website?: string;
    rating?: string;
    primary_color?: string;
  }) {
    return fetchApi("/api/poster/render", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getPosterArchetypes() {
    return fetchApi("/api/poster/archetypes");
  },

  async lintPosterSpec(spec: any) {
    return fetchApi("/api/poster/spec/lint", {
      method: "POST",
      body: JSON.stringify(spec),
    });
  },

  async renderPosterSpec(spec: any) {
    return fetchApi("/api/poster/spec/render", {
      method: "POST",
      body: JSON.stringify(spec),
    });
  },

  async getConnections() {
    return fetchApi("/api/connections");
  },

  async connectPlatform(platform: string, account_name: string) {
    return fetchApi("/api/connections/connect", {
      method: "POST",
      body: JSON.stringify({ platform, account_name }),
    });
  },

  async disconnectPlatform(platform: string) {
    return fetchApi(`/api/connections/${platform}`, { method: "DELETE" });
  },

  async createCanvaDesign(data: { title: string; brand_color?: string; width?: number; height?: number }) {
    return fetchApi("/api/canva/create-design", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getCanvaStatus() {
    return fetchApi("/api/canva/status");
  },
};

