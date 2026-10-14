// The one mark: the RB tile, the same file the browser tab shows. Headers carry the full
// lockup (components/Lockup); this is the mark on its own, for an empty state.
export function Logo({ className }: { className?: string }) {
    return <img src="/favicon.svg" alt="RB" className={className} />;
}
