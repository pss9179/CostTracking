"use client";

import { useState, useEffect } from "react";
import { Copy, Check } from "lucide-react";
import { cn } from "@/lib/utils";

// Table of contents item
export interface TocItem {
  id: string;
  title: string;
  level?: number;
}

interface DocPageProps {
  title: string;
  description?: string;
  category?: string;
  toc?: TocItem[];
  children: React.ReactNode;
}

export function DocPage({ title, description, category, toc = [], children }: DocPageProps) {
  const [activeSection, setActiveSection] = useState<string>("");

  // Track scroll position to highlight active TOC item
  useEffect(() => {
    if (toc.length === 0) return;
    
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { rootMargin: "-100px 0px -80% 0px" }
    );

    toc.forEach((item) => {
      const element = document.getElementById(item.id);
      if (element) observer.observe(element);
    });

    return () => observer.disconnect();
  }, [toc]);

  return (
    <div className="flex">
      {/* Content */}
      <div className="flex-1 min-w-0 px-8 py-8 lg:px-12 lg:py-10 max-w-4xl">
        {/* Breadcrumb / Category */}
        {category && (
          <p className="text-sm text-slate-500 mb-2">{category}</p>
        )}
        
        {/* Title */}
        <h1 className="text-4xl font-bold text-slate-900 mb-4">{title}</h1>
        
        {/* Description */}
        {description && (
          <p className="text-lg text-slate-600 mb-8 leading-relaxed">{description}</p>
        )}

        {/* Content */}
        <div className="prose prose-slate max-w-none 
          prose-headings:scroll-mt-20 
          prose-h2:text-2xl prose-h2:font-semibold prose-h2:mt-10 prose-h2:mb-4
          prose-h3:text-xl prose-h3:font-medium prose-h3:mt-8 prose-h3:mb-3
          prose-p:text-slate-600 prose-p:leading-7
          prose-a:text-emerald-600 prose-a:no-underline hover:prose-a:underline
          prose-strong:text-slate-900
          prose-code:text-sm prose-code:bg-slate-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:before:content-none prose-code:after:content-none
          prose-ul:my-4 prose-li:text-slate-600
          prose-hr:my-8
        ">
          {children}
        </div>
      </div>

      {/* On This Page - Table of Contents */}
      {toc.length > 0 && (
        <aside className="w-56 flex-shrink-0 hidden xl:block">
          <div className="sticky top-20 py-10 pr-6">
            <h4 className="text-sm font-semibold text-slate-900 mb-4">On this page</h4>
            <nav className="space-y-1">
              {toc.map((item) => (
                <a
                  key={item.id}
                  href={`#${item.id}`}
                  className={cn(
                    "block text-sm py-1 transition-colors",
                    item.level === 2 ? "pl-0" : "pl-3",
                    activeSection === item.id
                      ? "text-emerald-600 font-medium"
                      : "text-slate-500 hover:text-slate-900"
                  )}
                >
                  {item.title}
                </a>
              ))}
            </nav>
          </div>
        </aside>
      )}
    </div>
  );
}

// Code block component with copy button
interface CodeBlockProps {
  code: string;
  language?: string;
  filename?: string;
  showLineNumbers?: boolean;
}

export function CodeBlock({ code, language = "python", filename, showLineNumbers = false }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group rounded-lg overflow-hidden bg-slate-900 my-4">
      {/* Header */}
      {(filename || language) && (
        <div className="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
          <span className="text-xs text-slate-400 font-mono">
            {filename || language}
          </span>
          <button
            onClick={copyToClipboard}
            className="text-slate-400 hover:text-white transition-colors p-1"
          >
            {copied ? (
              <Check className="w-4 h-4 text-emerald-400" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        </div>
      )}
      
      {/* Code */}
      <div className="relative">
        {!filename && !language && (
          <button
            onClick={copyToClipboard}
            className="absolute top-2 right-2 text-slate-400 hover:text-white transition-colors p-1.5 opacity-0 group-hover:opacity-100"
          >
            {copied ? (
              <Check className="w-4 h-4 text-emerald-400" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        )}
        <pre className={cn(
          "text-sm font-mono text-slate-100 overflow-x-auto p-4",
          showLineNumbers && "pl-12"
        )}>
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
}

// Callout / Info box
interface CalloutProps {
  type?: "info" | "warning" | "tip" | "note";
  title?: string;
  children: React.ReactNode;
}

export function Callout({ type = "info", title, children }: CalloutProps) {
  const styles = {
    info: "bg-blue-50 border-blue-200 text-blue-900",
    warning: "bg-amber-50 border-amber-200 text-amber-900",
    tip: "bg-emerald-50 border-emerald-200 text-emerald-900",
    note: "bg-slate-50 border-slate-200 text-slate-900",
  };

  const icons = {
    info: "💡",
    warning: "⚠️",
    tip: "✨",
    note: "📝",
  };

  return (
    <div className={cn("rounded-lg border p-4 my-4", styles[type])}>
      <div className="flex items-start gap-3">
        <span className="text-lg">{icons[type]}</span>
        <div>
          {title && <p className="font-semibold mb-1">{title}</p>}
          <div className="text-sm leading-relaxed">{children}</div>
        </div>
      </div>
    </div>
  );
}

// Parameter table
interface Parameter {
  name: string;
  type: string;
  required?: boolean;
  description: string;
  default?: string;
}

export function ParameterTable({ parameters }: { parameters: Parameter[] }) {
  return (
    <div className="overflow-x-auto my-6">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200">
            <th className="text-left py-2 pr-4 font-semibold text-slate-900">Parameter</th>
            <th className="text-left py-2 pr-4 font-semibold text-slate-900">Type</th>
            <th className="text-left py-2 font-semibold text-slate-900">Description</th>
          </tr>
        </thead>
        <tbody>
          {parameters.map((param) => (
            <tr key={param.name} className="border-b border-slate-100">
              <td className="py-3 pr-4">
                <code className="text-sm bg-slate-100 px-1.5 py-0.5 rounded text-slate-900 font-medium">
                  {param.name}
                </code>
                {param.required && (
                  <span className="ml-2 text-xs text-rose-600 font-medium">required</span>
                )}
              </td>
              <td className="py-3 pr-4 text-slate-600 font-mono text-xs">
                {param.type}
              </td>
              <td className="py-3 text-slate-600">
                {param.description}
                {param.default && (
                  <span className="text-slate-400 ml-1">
                    Default: <code className="text-xs">{param.default}</code>
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Step list for tutorials
interface Step {
  title: string;
  description?: string;
  children?: React.ReactNode;
}

export function Steps({ steps }: { steps: Step[] }) {
  return (
    <div className="space-y-6 my-6">
      {steps.map((step, index) => (
        <div key={index} className="flex gap-4">
          <div className="flex-shrink-0 w-8 h-8 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center font-semibold text-sm">
            {index + 1}
          </div>
          <div className="flex-1 pt-0.5">
            <h4 className="font-semibold text-slate-900 mb-1">{step.title}</h4>
            {step.description && (
              <p className="text-slate-600 text-sm mb-3">{step.description}</p>
            )}
            {step.children}
          </div>
        </div>
      ))}
    </div>
  );
}

