"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

export function TopBar() {
  const pathname = usePathname();

  useEffect(() => {
    console.log('TopBar useEffect running - hiding Skyline links');
    
    const hideSkylineElements = () => {
      // Find the div that's a sibling to main
      const mainElement = document.querySelector('main');
      if (!mainElement) return;
      
      const mainParent = mainElement.parentElement;
      if (!mainParent) return;
      
      // Find all siblings of main
      const siblings = Array.from(mainParent.children);
      siblings.forEach(sibling => {
        if (sibling.tagName === 'MAIN') return;
        
        // Check if this sibling contains a Skyline link
        const skylineLink = sibling.querySelector('a[href="/overview"]');
        if (skylineLink && skylineLink.textContent?.trim() === 'Skyline') {
          console.log('Found Skyline link, hiding parent div');
          (sibling as HTMLElement).style.display = 'none';
        }
        
        // Also check for Skyline spans
        const skylineSpan = sibling.querySelector('span.text-xl.font-bold.text-gray-900');
        if (skylineSpan && skylineSpan.textContent?.trim() === 'Skyline') {
          console.log('Found Skyline span, hiding parent div');
          (sibling as HTMLElement).style.display = 'none';
        }
      });
    };

    hideSkylineElements();
    setTimeout(hideSkylineElements, 100);
    setTimeout(hideSkylineElements, 500);
    setTimeout(hideSkylineElements, 1000);
    
    const observer = new MutationObserver(() => {
      hideSkylineElements();
    });
    observer.observe(document.body, { childList: true, subtree: true });
    
    return () => observer.disconnect();
  }, [pathname]);

  // Don't show top bar on auth pages or landing page
  if (pathname?.startsWith('/sign-') || pathname === '/') {
    return null;
  }

  return (
    <>
      <style dangerouslySetInnerHTML={{__html: `
        /* Hide any Skyline links with href="/overview" that are siblings to main */
        .flex.flex-col.min-w-0 > div:not(:first-child):not(main) a[href="/overview"],
        .flex.flex-col.min-w-0 > div:not(:first-child):not(main) a[href*="/overview"],
        main ~ div a[href="/overview"],
        main ~ div a[href*="/overview"] {
          display: none !important;
        }
        main ~ div:has(a[href="/overview"]) {
          display: none !important;
        }
      `}} />
      <div className="flex items-center justify-between h-16 px-8 border-b bg-background">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-semibold">
            {pathname === "/overview" && "Overview"}
            {pathname === "/dashboard" && "Dashboard"}
            {pathname === "/runs" && "Runs"}
            {pathname === "/agents" && "Agents"}
            {pathname === "/llms" && "LLMs"}
            {pathname === "/infrastructure" && "Infrastructure"}
            {pathname === "/costs" && "Costs"}
            {pathname === "/settings" && "Settings"}
            {pathname?.startsWith("/runs/") && "Run Details"}
          </h1>
        </div>
      </div>
    </>
  );
}

