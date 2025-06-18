import "./globals.css";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className="scrollbar-track-transparent scrollbar-thumb-foreground/10"
    >
      <body>{children}</body>
    </html>
  );
}
