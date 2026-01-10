export default function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // This layout bypasses the main app layout with sidebar
  // The docs page has its own header/footer
  return <>{children}</>;
}
