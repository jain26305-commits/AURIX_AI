import type { Metadata, Viewport } from 'next';
import { Inter, IBM_Plex_Mono, Chakra_Petch } from 'next/font/google';
import '@/styles/globals.css';
import { QueryProvider } from '@/providers/QueryProvider';
import { TenantProvider } from '@/context/TenantContext';
import { SidebarProvider } from '@/context/SidebarContext';
import { WorkspaceHeaderProvider } from '@/context/WorkspaceHeaderContext';
import { AppShell } from '@/components/layout/AppShell';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
});

const plexMono = IBM_Plex_Mono({
  weight: ['400', '500', '600'],
  subsets: ['latin'],
  variable: '--font-mono',
});

const chakraPetch = Chakra_Petch({
  weight: ['500', '600', '700'],
  subsets: ['latin'],
  variable: '--font-display',
});

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#030303',
};

export const metadata: Metadata = {
  title: {
    template: '%s | AURIX AI Enterprise Platform',
    default: 'AURIX AI | Enterprise Business Operating Intelligence',
  },
  description:
    'Deterministic supply chain intelligence, multi-echelon optimization, and autonomous operational execution platform.',
  keywords: [
    'Supply Chain',
    'ERP',
    'Inventory Optimization',
    'Demand Forecasting',
    'MRP',
    'AURIX AI',
    'Agent Studio',
  ],
  authors: [{ name: 'AURIX Systems' }],
  robots: 'noindex, nofollow',
  icons: {
    icon: [
      { url: '/favicon.svg', type: 'image/svg+xml' },
      { url: '/icon.svg', type: 'image/svg+xml' },
    ],
    apple: [{ url: '/icon.svg', type: 'image/svg+xml' }],
  },
  openGraph: {
    title: 'AURIX AI | Enterprise Business Operating Intelligence',
    description:
      'Autonomous multi-echelon inventory, financial, manufacturing, and operational execution intelligence.',
    siteName: 'AURIX AI',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${plexMono.variable} ${chakraPetch.variable} scroll-smooth`}
      suppressHydrationWarning
    >
      <head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/icon.svg" type="image/svg+xml" />
      </head>
      <body className="bg-[#030303] text-[#F9FAFB] min-h-screen overflow-x-hidden selection:bg-[#D4AF37]/30 selection:text-white">
        <QueryProvider>
          <TenantProvider>
            <SidebarProvider>
              <WorkspaceHeaderProvider>
                <AppShell>{children}</AppShell>
              </WorkspaceHeaderProvider>
            </SidebarProvider>
          </TenantProvider>
        </QueryProvider>
      </body>
    </html>
  );
}