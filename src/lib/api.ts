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

// Cross-tab authentication synchronization
export const authChannel = typeof window !== "undefined" && "BroadcastChannel" in window 
  ? new BroadcastChannel("auth") 
  : null;

if (authChannel) {
  authChannel.onmessage = (event) => {
    if (event.data === "logout") {
      if (typeof window !== "undefined" && window.location.pathname !== "/login") {
        window.location.href = `/login?return_to=${encodeURIComponent(window.location.pathname)}`;
      }
    } else if (event.data === "login") {
      if (typeof window !== "undefined" && window.location.pathname === "/login") {
        window.location.href = "/studio";
      }
    }
  };
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

  // Rewrite /api and /auth through local origin when possible or use API_BASE
  const url = endpoint.startsWith("http") 
    ? endpoint 
    : endpoint.startsWith("/") 
      ? endpoint 
      : `/${endpoint}`;

  const res = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // Ensure session cookies are sent with every request
  });

  if (res.status === 401) {
    // If unauthorized, notify other tabs and redirect to login
    if (typeof window !== "undefined" && window.location.pathname !== "/login") {
      removeAuthToken();
      if (authChannel) {
        authChannel.postMessage("logout");
      }
      const safeReturnTo = window.location.pathname.startsWith("/") ? window.location.pathname : "/studio";
      window.location.href = `/login?return_to=${encodeURIComponent(safeReturnTo)}`;
    }
    throw new Error("Authentication required. Please sign in.");
  }

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
// Authentication & Session Service
// ---------------------------------------------------------------------------
export const authService = {
  async getProfile() {
    return fetchApi("/auth/me");
  },

  async logout() {
    try {
      await fetchApi("/auth/logout", { method: "POST" });
    } catch (_) {}
    removeAuthToken();
    if (authChannel) {
      authChannel.postMessage("logout");
    }
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  },

  async logoutAll() {
    try {
      await fetchApi("/auth/logout-all", { method: "POST" });
    } catch (_) {}
    removeAuthToken();
    if (authChannel) {
      authChannel.postMessage("logout");
    }
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  },

  initiateGoogleLogin(returnTo: string = "/studio") {
    if (typeof window === "undefined") return;
    const safeReturnTo = returnTo.startsWith("/") && !returnTo.startsWith("//") ? returnTo : "/studio";
    window.location.href = `/auth/google/login?return_to=${encodeURIComponent(safeReturnTo)}`;
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

  async getPosterTemplates() {
    return fetchApi("/api/poster/templates");
  },

  async getTemplateCandidates(params: {
    vertical?: string;
    industry_category?: string;
    goal?: string;
    has_client_photos?: boolean;
    recent_archetypes?: string[];
  }) {
    return fetchApi("/api/poster/candidates", {
      method: "POST",
      body: JSON.stringify(params),
    });
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

