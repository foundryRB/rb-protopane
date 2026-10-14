import { useState } from 'react';

import { Button } from '@/components/ui/button';

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
}

interface ChatPanelProps {
    slug: string;
    /** Persist the current canvas before the agent runs (the save-first conflict rule). */
    onBeforeSend: () => Promise<void>;
    /** Signal the editor that the agent is (or is no longer) editing, so it live-reloads. */
    onAgentActive: (active: boolean) => void;
}

interface StreamEvent {
    kind: string;
    text: string;
}

export function ChatPanel({ slug, onBeforeSend, onAgentActive }: ChatPanelProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [busy, setBusy] = useState(false);
    const [activity, setActivity] = useState('');

    function appendToLastAssistant(text: string): void {
        setMessages((current) => {
            const next = [...current];
            const last = next[next.length - 1];
            if (last) next[next.length - 1] = { role: 'assistant', content: last.content + text };
            return next;
        });
    }

    async function send(): Promise<void> {
        const text = input.trim();
        if (!text || busy) return;
        const history = messages;
        setInput('');
        setMessages((current) => [
            ...current,
            { role: 'user', content: text },
            { role: 'assistant', content: '' },
        ]);
        setBusy(true);
        setActivity('');
        onAgentActive(true);
        try {
            await onBeforeSend();
            const res = await fetch(`/api/projects/${slug}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, history }),
            });
            if (!res.ok || !res.body) throw new Error(`Chat failed (${res.status})`);
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            for (;;) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const chunks = buffer.split('\n\n');
                buffer = chunks.pop() ?? '';
                for (const chunk of chunks) {
                    const line = chunk.split('\n').find((l) => l.startsWith('data: '));
                    const data = line?.slice(6);
                    if (!data || data === '{}') continue;
                    let event: StreamEvent;
                    try {
                        event = JSON.parse(data) as StreamEvent;
                    } catch {
                        continue;
                    }
                    if (event.kind === 'text') appendToLastAssistant(event.text);
                    else if (event.kind === 'tool') setActivity(`Running ${event.text}...`);
                    else if (event.kind === 'error') appendToLastAssistant(`\n[error: ${event.text}]`);
                }
            }
        } catch (e) {
            appendToLastAssistant(`\n[${e instanceof Error ? e.message : 'chat failed'}]`);
        } finally {
            setBusy(false);
            setActivity('');
            onAgentActive(false);
        }
    }

    return (
        <div className="flex h-full flex-col">
            <div className="border-b px-4 py-3">
                <div className="font-semibold text-foreground">Design chat</div>
                <div className="text-xs text-muted-foreground">Edits this screen live.</div>
            </div>
            <div className="flex-1 space-y-3 overflow-y-auto p-4 text-sm">
                {messages.length === 0 && (
                    <p className="text-muted-foreground">
                        Ask me to build or restyle this screen, or to apply a brand.
                    </p>
                )}
                {messages.map((message, index) => (
                    <div
                        key={index}
                        className={message.role === 'user' ? 'text-foreground' : 'text-muted-foreground'}
                    >
                        <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                            {message.role}
                        </div>
                        <div className="whitespace-pre-wrap">
                            {message.content || (busy && index === messages.length - 1 ? '...' : '')}
                        </div>
                    </div>
                ))}
                {activity && <div className="text-xs italic text-muted-foreground">{activity}</div>}
            </div>
            <div className="border-t p-3">
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            void send();
                        }
                    }}
                    placeholder="Describe a change..."
                    rows={2}
                    disabled={busy}
                    className="w-full resize-none rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                />
                <Button
                    type="button"
                    onClick={() => void send()}
                    disabled={busy}
                    className="mt-2 w-full"
                >
                    {busy ? 'Working...' : 'Send'}
                </Button>
            </div>
        </div>
    );
}
