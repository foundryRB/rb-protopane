// The one mark: the speechmark, the same file the browser tab shows. Headers carry the full
// lockup (components/Lockup); this is the mark on its own, for an empty state.
export function Logo({ className }: { className?: string }) {
    return <img src="/favicon.svg" alt="Vodafone" className={className} />;
}
