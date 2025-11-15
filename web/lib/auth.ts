/**
 * Load authentication state from localStorage
 * This is a simple implementation - in production, use Clerk's hooks
 */
export function loadAuth(): { user: any | null; apiKey: string | null } {
  if (typeof window === "undefined") {
    return { user: null, apiKey: null };
  }

  const apiKey = localStorage.getItem("api_key");
  const userStr = localStorage.getItem("user");

  let user = null;
  if (userStr) {
    try {
      user = JSON.parse(userStr);
    } catch (e) {
      // Invalid JSON, ignore
    }
  }

  return { user, apiKey };
}

/**
 * Save API key to localStorage
 */
export function saveApiKey(apiKey: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("api_key", apiKey);
  }
}

/**
 * Clear authentication data
 */
export function clearAuth(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("api_key");
    localStorage.removeItem("user");
  }
}

