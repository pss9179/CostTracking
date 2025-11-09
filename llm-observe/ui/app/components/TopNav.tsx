"use client";

import { useTheme } from "./ThemeProvider";

export function TopNav() {
  const { theme, toggleTheme } = useTheme();

  return (
    <nav className="fixed top-0 left-0 right-0 h-16 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 z-40 flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">LLM Observe</h1>
        <span className="text-xs text-gray-500 dark:text-gray-400">AI Agent Observability</span>
      </div>
      <button
        onClick={toggleTheme}
        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
        aria-label="Toggle theme"
      >
        {theme === "light" ? "🌙" : "☀️"}
      </button>
    </nav>
  );
}

