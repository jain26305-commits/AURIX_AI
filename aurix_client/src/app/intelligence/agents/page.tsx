import { redirect } from 'next/navigation';

// Consolidated per ADR-001: this route duplicated content that now lives
// under the canonical 15-domain IA. Kept as a redirect so existing
// bookmarks/links keep working.
export default function IntelAgentsRedirectPage() {
  redirect('/agents');
}
