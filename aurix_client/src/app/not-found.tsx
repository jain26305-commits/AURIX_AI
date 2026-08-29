import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#030303] text-white flex flex-col items-center justify-center p-6 text-center font-mono select-none">
      <div className="w-16 h-16 rounded-2xl bg-gold/10 border border-gold/30 flex items-center justify-center mb-6 shadow-[0_0_24px_rgba(212,175,55,0.15)]">
        <span className="text-gold text-2xl font-bold font-display">404</span>
      </div>
      <h1 className="text-xl font-bold tracking-widest uppercase mb-2">PAGE / NODE NOT FOUND</h1>
      <p className="text-xs text-slate-400 max-w-md mb-8">
        The requested operational surface or entity endpoint does not exist or has been relocated within the AURIX topology.
      </p>
      <Link
        href="/control-tower"
        className="px-4 py-2 rounded-lg bg-gold/15 hover:bg-gold/25 border border-gold/40 text-gold text-xs font-bold transition-all shadow-[0_0_16px_rgba(212,175,55,0.12)] cursor-pointer"
      >
        RETURN TO CONTROL TOWER →
      </Link>
    </div>
  );
}