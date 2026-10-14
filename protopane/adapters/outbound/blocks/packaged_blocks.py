"""The packaged block vocabulary: shadcn-styled markup in token-backed utilities.

Every block's html uses the same Tailwind utility classes as the frontend's
src/components/ui, so canvas markup ports back into real shadcn React
components at handoff. `preview` (defaulting to the html) renders a themed
thumbnail in the palette. Markup here is the vocabulary every door shares:
the SPA palette, the REST API, and MCP agents all read this one list.
"""

from __future__ import annotations

from protopane.domain.model.block import Block

_DASHED = '<div class="min-h-12 rounded-md border border-dashed border-border bg-muted/40"></div>'

# The bottom bar's destinations, shared by its markup and its palette preview: the
# markup pins the bar to the bottom edge below 640px only, which a thumbnail cannot show.
_BOTTOM_BAR_ITEMS = (
    '<a aria-current="page" class="flex min-h-14 flex-1 flex-col items-center justify-center'
    ' gap-1 px-1 text-center text-xs font-medium leading-tight text-primary"><svg'
    ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-5 w-5"'
    ' aria-hidden="true"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path'
    ' d="M9 22V12h6v10"/></svg>Home</a><a class="flex min-h-14 flex-1 flex-col items-center'
    " justify-center gap-1 px-1 text-center text-xs font-medium leading-tight"
    ' text-muted-foreground hover:text-foreground"><svg viewBox="0 0 24 24" fill="none"'
    ' stroke="currentColor" stroke-width="2" class="h-5 w-5" aria-hidden="true"><circle'
    ' cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>Search</a><a class="flex'
    " min-h-14 flex-1 flex-col items-center justify-center gap-1 px-1 text-center text-xs"
    ' font-medium leading-tight text-muted-foreground hover:text-foreground"><svg'
    ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-5 w-5"'
    ' aria-hidden="true"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>'
    'Orders</a><a class="flex min-h-14 flex-1 flex-col items-center justify-center gap-1 px-1'
    " text-center text-xs font-medium leading-tight text-muted-foreground"
    ' hover:text-foreground"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"'
    ' stroke-width="2" class="h-5 w-5" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path'
    ' d="M4 21a8 8 0 0 1 16 0"/></svg>Account</a>'
)

PACKAGED_BLOCKS: list[Block] = [
    # Inputs
    Block(
        slug="sh-button",
        label="Button",
        category="Inputs",
        html='<button class="inline-flex items-center justify-center gap-2 rounded-md bg-primary'
        ' px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">'
        "Button</button>",
    ),
    Block(
        slug="sh-button-outline",
        label="Button (outline)",
        category="Inputs",
        html='<button class="inline-flex items-center justify-center gap-2 rounded-md border'
        ' border-input bg-background px-4 py-2 text-sm font-medium hover:bg-accent">'
        "Button</button>",
    ),
    Block(
        slug="sh-button-secondary",
        label="Button (secondary)",
        category="Inputs",
        html='<button class="inline-flex items-center justify-center gap-2 rounded-md bg-secondary'
        ' px-4 py-2 text-sm font-medium text-secondary-foreground hover:bg-accent">'
        "Button</button>",
    ),
    Block(
        slug="sh-button-ghost",
        label="Button (ghost)",
        category="Inputs",
        html='<button class="inline-flex items-center justify-center gap-2 rounded-md px-4 py-2'
        ' text-sm font-medium hover:bg-accent hover:text-accent-foreground">Button</button>',
    ),
    Block(
        slug="sh-button-destructive",
        label="Button (destructive)",
        category="Inputs",
        html='<button class="inline-flex items-center justify-center gap-2 rounded-md'
        ' bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground'
        ' hover:bg-destructive/90">Delete</button>',
    ),
    Block(
        slug="sh-input",
        label="Input",
        category="Inputs",
        html='<input placeholder="Type here..." class="flex h-9 w-full rounded-md border'
        ' border-input bg-transparent px-3 py-1 text-base shadow-sm'
        ' placeholder:text-muted-foreground sm:text-sm" />',
    ),
    Block(
        slug="sh-textarea",
        label="Textarea",
        category="Inputs",
        html='<textarea placeholder="Type your message..." class="flex min-h-20 w-full rounded-md'
        ' border border-input bg-transparent px-3 py-2 text-base shadow-sm'
        ' placeholder:text-muted-foreground sm:text-sm"></textarea>',
    ),
    Block(
        slug="sh-select",
        label="Select",
        category="Inputs",
        html='<select class="flex h-9 w-full rounded-md border border-input bg-transparent px-3'
        ' py-1 text-base shadow-sm sm:text-sm"><option>Select an option</option><option>Option A'
        "</option><option>Option B</option></select>",
    ),
    Block(
        slug="sh-field",
        label="Label + input",
        category="Inputs",
        html='<div class="grid w-full max-w-sm items-center gap-1.5"><label class="text-sm'
        ' font-medium leading-none text-foreground">Email</label><input'
        ' placeholder="you@example.com" class="flex h-9 w-full rounded-md border border-input'
        ' bg-transparent px-3 py-1 text-base shadow-sm placeholder:text-muted-foreground'
        ' sm:text-sm" /></div>',
    ),
    Block(
        slug="sh-checkbox",
        label="Checkbox",
        category="Inputs",
        html='<label class="flex items-center gap-2 text-sm text-foreground"><span class="flex'
        ' h-4 w-4 items-center justify-center rounded border border-primary bg-primary'
        ' text-primary-foreground"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"'
        ' stroke-width="3" class="h-3 w-3"><path d="M5 12l5 5L20 7"/></svg></span>'
        "Accept terms and conditions</label>",
    ),
    Block(
        slug="sh-switch",
        label="Switch",
        category="Inputs",
        html='<label class="flex items-center gap-2 text-sm text-foreground"><span'
        ' class="inline-flex h-5 w-9 items-center rounded-full bg-primary px-0.5"><span'
        ' class="ml-auto h-4 w-4 rounded-full bg-background"></span></span>'
        "Enable notifications</label>",
    ),
    Block(
        slug="sh-radio",
        label="Radio group",
        category="Inputs",
        html='<div class="flex flex-col gap-2 text-sm text-foreground"><label class="flex'
        ' items-center gap-2"><span class="flex h-4 w-4 items-center justify-center rounded-full'
        ' border border-primary"><span class="h-2 w-2 rounded-full bg-primary"></span></span>'
        'Option one</label><label class="flex items-center gap-2"><span class="h-4 w-4'
        ' rounded-full border border-input"></span>Option two</label></div>',
    ),
    # Forms
    Block(
        slug="sh-form",
        label="One-column form",
        category="Forms",
        html='<form class="flex w-full max-w-md flex-col gap-4"><label class="flex flex-col'
        ' gap-1.5"><span class="text-sm font-medium leading-none text-foreground">Full name'
        '</span><input type="text" autocomplete="name" spellcheck="false" enterkeyhint="next"'
        ' class="flex h-11 w-full rounded-md border border-input bg-transparent px-3 text-base'
        ' shadow-sm sm:h-9 sm:text-sm" /></label><label class="flex flex-col gap-1.5"><span'
        ' class="text-sm font-medium leading-none text-foreground">Email</span><input'
        ' type="email" autocomplete="email" spellcheck="false" enterkeyhint="next"'
        ' placeholder="you@example.com" class="flex h-11 w-full rounded-md border border-input'
        " bg-transparent px-3 text-base shadow-sm placeholder:text-muted-foreground sm:h-9"
        ' sm:text-sm" /></label><label class="flex flex-col gap-1.5"><span class="text-sm'
        ' font-medium leading-none text-foreground">Phone</span><input type="tel"'
        ' autocomplete="tel" enterkeyhint="next" class="flex h-11 w-full rounded-md border'
        ' border-input bg-transparent px-3 text-base shadow-sm sm:h-9 sm:text-sm" /></label>'
        '<label class="flex flex-col gap-1.5"><span class="text-sm font-medium leading-none'
        ' text-foreground">Order number</span><input type="text" inputmode="numeric"'
        ' spellcheck="false" enterkeyhint="send" class="flex h-11 w-full rounded-md border'
        ' border-input bg-transparent px-3 text-base shadow-sm sm:h-9 sm:text-sm" /></label>'
        '<button type="submit" class="inline-flex h-11 w-full items-center justify-center'
        " rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground"
        ' hover:bg-primary/90 sm:h-9 sm:w-auto sm:self-start">Send</button></form>',
    ),
    Block(
        slug="sh-action-bar",
        label="Pinned action bar",
        category="Forms",
        html='<div class="pb-[max(5rem,12svh)] [html:has(&)]:scroll-pb-[max(5rem,12svh)]">'
        '<form id="sh-action-form" class="mx-auto flex w-full max-w-md flex-col gap-4 p-4"><h2'
        ' class="text-lg font-semibold tracking-tight text-foreground">Delivery address</h2>'
        '<label class="flex flex-col gap-1.5"><span class="text-sm font-medium leading-none'
        ' text-foreground">Full name</span><input type="text" autocomplete="name"'
        ' spellcheck="false" enterkeyhint="next" class="flex h-11 w-full rounded-md border'
        ' border-input bg-transparent px-3 text-base shadow-sm sm:h-9 sm:text-sm" /></label>'
        '<label class="flex flex-col gap-1.5"><span class="text-sm font-medium leading-none'
        ' text-foreground">Street address</span><input type="text" autocomplete="address-line1"'
        ' enterkeyhint="next" class="flex h-11 w-full rounded-md border border-input'
        ' bg-transparent px-3 text-base shadow-sm sm:h-9 sm:text-sm" /></label><label'
        ' class="flex flex-col gap-1.5"><span class="text-sm font-medium leading-none'
        ' text-foreground">Postcode</span><input type="text" autocomplete="postal-code"'
        ' spellcheck="false" enterkeyhint="next" class="flex h-11 w-full rounded-md border'
        ' border-input bg-transparent px-3 text-base shadow-sm sm:h-9 sm:text-sm" /></label>'
        '<label class="flex flex-col gap-1.5"><span class="text-sm font-medium leading-none'
        ' text-foreground">City</span><input type="text" autocomplete="address-level2"'
        ' enterkeyhint="next" class="flex h-11 w-full rounded-md border border-input'
        ' bg-transparent px-3 text-base shadow-sm sm:h-9 sm:text-sm" /></label><label'
        ' class="flex flex-col gap-1.5"><span class="text-sm font-medium leading-none'
        ' text-foreground">Phone</span><input type="tel" autocomplete="tel" enterkeyhint="done"'
        ' class="flex h-11 w-full rounded-md border border-input bg-transparent px-3 text-base'
        ' shadow-sm sm:h-9 sm:text-sm" /></label></form><div class="fixed inset-x-0 bottom-0'
        " z-40 flex h-[max(5rem,12svh)] items-start gap-3 border-t bg-background px-4 pt-3"
        ' pb-[max(0.75rem,env(safe-area-inset-bottom))]"><p role="status" aria-live="polite"'
        ' class="flex min-h-11 flex-1 items-center text-sm text-destructive"></p><button'
        ' type="submit" form="sh-action-form" class="inline-flex h-11 items-center'
        " justify-center rounded-md bg-primary px-5 text-sm font-medium text-primary-foreground"
        ' hover:bg-primary/90">Continue</button></div></div>',
        preview='<div class="flex flex-col gap-3"><label class="flex flex-col gap-1.5"><span'
        ' class="text-sm font-medium leading-none text-foreground">Phone</span><input'
        ' type="tel" class="flex h-9 w-full rounded-md border border-input bg-transparent px-3'
        ' text-base shadow-sm sm:text-sm" /></label><div class="flex items-center gap-3'
        ' border-t pt-3"><p class="flex-1 text-sm text-muted-foreground"></p><button'
        ' class="inline-flex h-9 items-center justify-center rounded-md bg-primary px-5 text-sm'
        ' font-medium text-primary-foreground">Continue</button></div></div>',
    ),
    # Display
    Block(
        slug="sh-badge",
        label="Badge",
        category="Display",
        html='<span class="inline-flex items-center rounded-full border border-transparent'
        ' bg-primary px-2.5 py-0.5 text-xs font-semibold text-primary-foreground">Badge</span>',
    ),
    Block(
        slug="sh-badge-secondary",
        label="Badge (secondary)",
        category="Display",
        html='<span class="inline-flex items-center rounded-full border border-transparent'
        ' bg-secondary px-2.5 py-0.5 text-xs font-semibold text-secondary-foreground">'
        "Secondary</span>",
    ),
    Block(
        slug="sh-heading",
        label="Heading",
        category="Display",
        html='<h2 class="text-2xl font-semibold tracking-tight text-foreground">Heading</h2>',
    ),
    Block(
        slug="sh-text",
        label="Text",
        category="Display",
        html='<p class="text-sm text-muted-foreground">A line of body copy.</p>',
    ),
    Block(
        slug="sh-avatar",
        label="Avatar",
        category="Display",
        html='<span class="inline-flex h-10 w-10 items-center justify-center rounded-full'
        ' bg-muted text-sm font-medium text-muted-foreground">JD</span>',
    ),
    Block(
        slug="sh-separator",
        label="Separator",
        category="Display",
        html='<div class="h-px w-full bg-border"></div>',
        preview='<div class="flex h-8 items-center"><div class="h-px w-full bg-border"></div>'
        "</div>",
    ),
    Block(
        slug="sh-progress",
        label="Progress",
        category="Display",
        html='<div class="h-2 w-full overflow-hidden rounded-full bg-secondary"><div'
        ' class="h-full w-2/3 rounded-full bg-primary"></div></div>',
    ),
    Block(
        slug="sh-alert",
        label="Alert",
        category="Display",
        html='<div class="flex gap-3 rounded-lg border border-border bg-card p-4'
        ' text-card-foreground"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"'
        ' stroke-width="2" class="h-4 w-4 shrink-0 text-muted-foreground"><circle cx="12"'
        ' cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg><div><div class="text-sm'
        ' font-medium">Heads up</div><div class="text-sm text-muted-foreground">You can add'
        " components to your app using the canvas.</div></div></div>",
    ),
    Block(
        slug="sh-alert-destructive",
        label="Alert (destructive)",
        category="Display",
        html='<div class="flex gap-3 rounded-lg border border-destructive p-4 text-destructive">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4'
        ' w-4 shrink-0"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>'
        '<div><div class="text-sm font-medium">Something went wrong</div><div class="text-sm">'
        "Your session has expired. Please log in again.</div></div></div>",
    ),
    Block(
        slug="sh-card",
        label="Card",
        category="Display",
        html='<div class="max-w-sm rounded-lg border bg-card text-card-foreground shadow-sm">'
        '<div class="flex flex-col gap-1.5 p-4"><div class="font-semibold leading-none'
        ' tracking-tight">Card title</div><div class="text-sm text-muted-foreground">Card'
        ' description</div></div><div class="p-4 pt-0 text-sm">Card content goes here.</div>'
        "</div>",
    ),
    Block(
        slug="sh-card-footer",
        label="Card (with footer)",
        category="Display",
        html='<div class="max-w-sm rounded-lg border bg-card text-card-foreground shadow-sm">'
        '<div class="flex flex-col gap-1.5 p-4"><div class="font-semibold leading-none'
        ' tracking-tight">Create project</div><div class="text-sm text-muted-foreground">Deploy'
        ' your new project in one click.</div></div><div class="p-4 pt-0 text-sm'
        ' text-muted-foreground">Name your project and pick a framework.</div><div class="flex'
        ' items-center justify-between gap-2 p-4 pt-0"><button class="inline-flex items-center'
        ' rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium'
        ' hover:bg-accent">Cancel</button><button class="inline-flex items-center rounded-md'
        ' bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground'
        ' hover:bg-primary/90">Deploy</button></div></div>',
    ),
    Block(
        slug="sh-stat",
        label="Stat card",
        category="Display",
        html='<div class="rounded-lg border bg-card p-4 text-card-foreground shadow-sm"><div'
        ' class="text-sm font-medium text-muted-foreground">Total revenue</div><div class="mt-1'
        ' text-2xl font-bold">$45,231.89</div><div class="mt-1 text-xs text-muted-foreground">'
        "+20.1% from last month</div></div>",
    ),
    Block(
        slug="sh-table",
        label="Table",
        category="Display",
        html='<div role="region" aria-labelledby="sh-table-caption" tabindex="0" class="w-full'
        ' overflow-x-auto rounded-lg border bg-card text-card-foreground"><table class="w-full'
        ' whitespace-nowrap text-sm"><caption id="sh-table-caption" class="px-3 py-2'
        ' text-left font-medium">Invoices</caption><thead><tr class="border-b bg-muted'
        ' text-left text-muted-foreground"><th class="sticky left-0 bg-muted px-3 py-2'
        ' font-medium">Name</th><th class="px-3 py-2 font-medium">Status</th><th class="px-3'
        ' py-2 font-medium">Amount</th></tr></thead><tbody><tr class="border-b"><td'
        ' class="sticky left-0 bg-card px-3 py-2">Alice</td><td class="px-3 py-2">Paid</td><td'
        ' class="px-3 py-2">$250.00</td></tr><tr><td class="sticky left-0 bg-card px-3 py-2">'
        'Bob</td><td class="px-3 py-2">Pending</td><td class="px-3 py-2">$150.00</td></tr>'
        "</tbody></table></div>",
    ),
    Block(
        slug="sh-stacked-rows",
        label="Stacked rows",
        category="Display",
        html='<ul aria-label="Invoices" class="flex flex-col gap-3"><li class="rounded-lg border'
        ' bg-card p-4 text-card-foreground shadow-sm"><dl class="flex flex-col gap-2 text-sm">'
        '<div class="flex justify-between gap-4"><dt class="text-muted-foreground">Name</dt>'
        '<dd class="font-medium">Alice</dd></div><div class="flex justify-between gap-4"><dt'
        ' class="text-muted-foreground">Status</dt><dd>Paid</dd></div><div class="flex'
        ' justify-between gap-4"><dt class="text-muted-foreground">Amount</dt><dd>$250.00</dd>'
        '</div></dl><a class="mt-2 inline-flex min-h-11 items-center text-sm font-medium'
        ' text-primary hover:underline">View invoice</a></li><li class="rounded-lg border'
        ' bg-card p-4 text-card-foreground shadow-sm"><dl class="flex flex-col gap-2 text-sm">'
        '<div class="flex justify-between gap-4"><dt class="text-muted-foreground">Name</dt>'
        '<dd class="font-medium">Bob</dd></div><div class="flex justify-between gap-4"><dt'
        ' class="text-muted-foreground">Status</dt><dd>Pending</dd></div><div class="flex'
        ' justify-between gap-4"><dt class="text-muted-foreground">Amount</dt><dd>$150.00</dd>'
        '</div></dl><a class="mt-2 inline-flex min-h-11 items-center text-sm font-medium'
        ' text-primary hover:underline">View invoice</a></li></ul>',
    ),
    Block(
        slug="sh-list",
        label="List",
        category="Display",
        html='<div class="divide-y rounded-lg border bg-card text-card-foreground"><div'
        ' class="flex items-center justify-between p-3 text-sm"><span>List item one</span>'
        '<span class="text-muted-foreground">Detail</span></div><div class="flex items-center'
        ' justify-between p-3 text-sm"><span>List item two</span><span'
        ' class="text-muted-foreground">Detail</span></div><div class="flex items-center'
        ' justify-between p-3 text-sm"><span>List item three</span><span'
        ' class="text-muted-foreground">Detail</span></div></div>',
    ),
    Block(
        slug="sh-image",
        label="Image placeholder",
        category="Display",
        html='<div class="flex aspect-video w-full items-center justify-center rounded-lg'
        ' border border-dashed border-border bg-muted text-muted-foreground"><svg'
        ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"'
        ' class="h-10 w-10"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9"'
        ' cy="9" r="2"/><path d="m21 15-3.5-3.5L9 20"/></svg></div>',
    ),
    # Navigation
    Block(
        slug="sh-tabs",
        label="Tabs",
        category="Navigation",
        html='<div class="inline-flex items-center gap-1 rounded-lg bg-muted p-1'
        ' text-muted-foreground"><button class="rounded-md bg-background px-3 py-1.5 text-sm'
        ' font-medium text-foreground shadow-sm">Account</button><button class="rounded-md px-3'
        ' py-1.5 text-sm font-medium">Password</button><button class="rounded-md px-3 py-1.5'
        ' text-sm font-medium">Settings</button></div>',
    ),
    Block(
        slug="sh-breadcrumb",
        label="Breadcrumb",
        category="Navigation",
        html='<nav class="flex items-center gap-1.5 text-sm text-muted-foreground"><a'
        ' class="hover:text-foreground">Home</a><span>/</span><a class="hover:text-foreground">'
        'Projects</a><span>/</span><span class="text-foreground">Acme</span></nav>',
    ),
    Block(
        slug="sh-navbar",
        label="Navbar",
        category="Navigation",
        html='<header class="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-lg border'
        ' bg-card px-4 py-3 text-card-foreground"><span class="font-semibold tracking-tight">'
        'Acme</span><nav class="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm'
        ' text-muted-foreground"><a class="hover:text-foreground">Dashboard</a><a'
        ' class="hover:text-foreground">Projects</a><a class="hover:text-foreground">Team</a>'
        '</nav><button class="ml-auto inline-flex items-center rounded-md bg-primary px-3'
        ' py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90">Sign in'
        "</button></header>",
    ),
    Block(
        slug="sh-sheet-menu",
        label="Sheet menu",
        category="Navigation",
        html='<header class="relative flex flex-wrap items-center gap-x-4 gap-y-2 rounded-lg'
        ' border bg-card px-4 py-3 text-card-foreground"><span class="font-semibold'
        ' tracking-tight">Acme</span><nav aria-label="Main" class="hidden flex-wrap'
        ' items-center gap-x-4 gap-y-1 text-sm text-muted-foreground sm:flex"><a'
        ' class="hover:text-foreground">Home</a><a class="hover:text-foreground">Projects</a><a'
        ' class="hover:text-foreground">Team</a><a class="hover:text-foreground">Reports</a><a'
        ' class="hover:text-foreground">Billing</a><a class="hover:text-foreground">'
        'Integrations</a><a class="hover:text-foreground">Settings</a></nav><div class="flex'
        ' flex-wrap items-center gap-3 text-sm text-muted-foreground sm:hidden"><a'
        ' class="inline-flex min-h-11 items-center hover:text-foreground">Home</a><a'
        ' class="inline-flex min-h-11 items-center hover:text-foreground">Projects</a><details>'
        '<summary class="inline-flex min-h-11 cursor-pointer list-none items-center gap-1.5'
        " rounded-md border border-input bg-background px-3 font-medium text-foreground"
        ' hover:bg-accent [&::-webkit-details-marker]:hidden"><svg viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4"'
        ' aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg>Menu</summary><nav'
        ' aria-label="Main" class="absolute inset-x-0 top-full z-40 mt-2 flex flex-col'
        ' rounded-lg border bg-card p-2 text-card-foreground shadow-md"><a class="flex min-h-11'
        ' items-center rounded-md px-3 hover:bg-accent">Home</a><a class="flex min-h-11'
        ' items-center rounded-md px-3 hover:bg-accent">Projects</a><a class="flex min-h-11'
        ' items-center rounded-md px-3 hover:bg-accent">Team</a><a class="flex min-h-11'
        ' items-center rounded-md px-3 hover:bg-accent">Reports</a><a class="flex min-h-11'
        ' items-center rounded-md px-3 hover:bg-accent">Billing</a><a class="flex min-h-11'
        ' items-center rounded-md px-3 hover:bg-accent">Integrations</a><a class="flex'
        ' min-h-11 items-center rounded-md px-3 hover:bg-accent">Settings</a></nav></details>'
        '</div><button class="ml-auto inline-flex items-center rounded-md bg-primary px-3'
        ' py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90">Sign in'
        "</button></header>",
    ),
    Block(
        slug="sh-bottom-bar",
        label="Bottom bar",
        category="Navigation",
        html='<nav aria-label="Main" class="fixed inset-x-0 bottom-0 z-40 flex'
        " h-[calc(4rem+env(safe-area-inset-bottom))] border-t bg-card"
        " pb-[max(0.25rem,env(safe-area-inset-bottom))] text-card-foreground sm:hidden"
        ' max-sm:[html:has(&)]:scroll-pb-[calc(4rem+env(safe-area-inset-bottom))]">'
        + _BOTTOM_BAR_ITEMS
        + "</nav>",
        preview='<nav class="flex rounded-lg border bg-card text-card-foreground">'
        + _BOTTOM_BAR_ITEMS
        + "</nav>",
    ),
    # Marketing
    Block(
        slug="sh-hero",
        label="Hero",
        category="Marketing",
        html='<section class="flex flex-col items-center gap-4 px-8 py-16 text-center"><span'
        ' class="inline-flex items-center rounded-full border border-border bg-secondary px-3'
        ' py-1 text-xs font-medium text-secondary-foreground">New: just launched</span><h1'
        ' class="max-w-2xl text-4xl font-bold tracking-tight text-foreground">A headline that'
        ' sells the outcome</h1><p class="max-w-xl text-muted-foreground">One supporting'
        " sentence that explains what the product does and why it matters to the reader.</p>"
        '<div class="flex gap-3"><button class="inline-flex items-center rounded-md bg-primary'
        ' px-5 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90">Get'
        ' started</button><button class="inline-flex items-center rounded-md border'
        " border-input bg-background px-5 py-2.5 text-sm font-medium hover:bg-accent"
        '">Learn more</button></div></section>',
    ),
    Block(
        slug="sh-cta",
        label="CTA banner",
        category="Marketing",
        html='<section class="flex flex-col items-center gap-3 rounded-xl bg-primary px-8 py-10'
        ' text-center text-primary-foreground"><h2 class="text-2xl font-semibold'
        ' tracking-tight">Ready to see it with your brand?</h2><p class="max-w-lg text-sm'
        ' opacity-90">A closing push that turns interest into the next step.</p><button'
        ' class="inline-flex items-center rounded-md bg-background px-5 py-2.5 text-sm'
        ' font-medium text-foreground hover:bg-accent">Book a session</button></section>',
    ),
    Block(
        slug="sh-testimonial",
        label="Testimonial",
        category="Marketing",
        html='<figure class="max-w-md rounded-lg border bg-card p-6 text-card-foreground'
        ' shadow-sm"><blockquote class="text-sm leading-relaxed">&ldquo;This cut our design'
        " cycle from weeks to a single working session. The team saw their brand live before"
        ' any code existed.&rdquo;</blockquote><figcaption class="mt-4 flex items-center'
        ' gap-3"><span class="inline-flex h-10 w-10 items-center justify-center rounded-full'
        ' bg-muted text-sm font-medium text-muted-foreground">MK</span><div><div class="text-sm'
        ' font-medium">Mara Kim</div><div class="text-xs text-muted-foreground">Head of'
        " Product, Acme</div></div></figcaption></figure>",
    ),
    Block(
        slug="sh-pricing",
        label="Pricing card",
        category="Marketing",
        html='<div class="max-w-xs rounded-lg border bg-card p-6 text-card-foreground'
        ' shadow-sm"><div class="text-sm font-medium text-muted-foreground">Pro</div><div'
        ' class="mt-2 flex items-baseline gap-1"><span class="text-3xl font-bold">$29</span>'
        '<span class="text-sm text-muted-foreground">/month</span></div><ul class="mt-4 flex'
        ' flex-col gap-2 text-sm"><li class="flex items-center gap-2"><svg viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="3" class="h-3.5 w-3.5 text-primary">'
        '<path d="M5 12l5 5L20 7"/></svg>Unlimited projects</li><li class="flex items-center'
        ' gap-2"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"'
        ' class="h-3.5 w-3.5 text-primary"><path d="M5 12l5 5L20 7"/></svg>Custom themes</li>'
        '<li class="flex items-center gap-2"><svg viewBox="0 0 24 24" fill="none"'
        ' stroke="currentColor" stroke-width="3" class="h-3.5 w-3.5 text-primary"><path'
        ' d="M5 12l5 5L20 7"/></svg>Priority support</li></ul><button class="mt-6 inline-flex'
        " w-full items-center justify-center rounded-md bg-primary px-4 py-2 text-sm"
        ' font-medium text-primary-foreground hover:bg-primary/90">Choose Pro</button></div>',
    ),
    Block(
        slug="sh-faq",
        label="FAQ item",
        category="Marketing",
        html='<div class="max-w-xl border-b border-border pb-4"><div class="flex items-center'
        ' justify-between text-sm font-medium text-foreground"><span>How does the handoff'
        ' work?</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"'
        ' stroke-width="2" class="h-4 w-4 text-muted-foreground"><path d="m6 9 6 6 6-6"/>'
        '</svg></div><p class="mt-2 text-sm text-muted-foreground">The theme exports as design'
        " tokens and every screen as component-ready markup, so the build team starts from"
        " exactly what you approved.</p></div>",
    ),
    Block(
        slug="sh-logo-row",
        label="Logo row",
        category="Marketing",
        html='<section class="flex flex-col items-center gap-4 px-8 py-6"><div class="text-xs'
        ' font-medium uppercase tracking-widest text-muted-foreground">Trusted by teams at'
        '</div><div class="flex flex-wrap items-center justify-center gap-8 text-lg'
        ' font-semibold tracking-tight text-muted-foreground/70"><span>Acme</span><span>Globex'
        "</span><span>Umbra</span><span>Initech</span><span>Hooli</span></div></section>",
    ),
    Block(
        slug="sh-footer",
        label="Footer",
        category="Marketing",
        html='<footer class="border-t border-border px-8 py-10"><div class="grid grid-cols-1'
        ' sm:grid-cols-3 gap-8"><div><div class="font-semibold tracking-tight'
        ' text-foreground">Acme</div><p'
        ' class="mt-2 text-sm text-muted-foreground">Short line about the company.</p></div>'
        '<div><div class="text-sm font-medium text-foreground">Product</div><nav class="mt-2'
        ' flex flex-col gap-1.5 text-sm text-muted-foreground"><a class="hover:text-foreground'
        '">Features</a><a class="hover:text-foreground">Pricing</a><a'
        ' class="hover:text-foreground">Docs</a></nav></div><div><div class="text-sm'
        ' font-medium text-foreground">Company</div><nav class="mt-2 flex flex-col gap-1.5'
        ' text-sm text-muted-foreground"><a class="hover:text-foreground">About</a><a'
        ' class="hover:text-foreground">Contact</a></nav></div></div><div class="mt-8 border-t'
        ' border-border pt-4 text-xs text-muted-foreground">&copy; 2026 Acme, Inc.</div>'
        "</footer>",
    ),
    # Layout
    Block(
        slug="sh-section",
        label="Section",
        category="Layout",
        html='<section class="p-8"></section>',
        preview=_DASHED,
    ),
    Block(
        slug="sh-container",
        label="Container",
        category="Layout",
        html='<div class="mx-auto max-w-3xl px-4"></div>',
        preview='<div class="mx-auto min-h-12 max-w-[75%] rounded-md border border-dashed'
        ' border-border bg-muted/40"></div>',
    ),
    Block(
        slug="sh-2col",
        label="2 columns",
        category="Layout",
        html='<div class="grid grid-cols-1 sm:grid-cols-2 gap-4"><div class="min-h-16'
        ' rounded-md border border-dashed border-border p-4"></div><div class="min-h-16'
        ' rounded-md border border-dashed border-border p-4"></div></div>',
    ),
    Block(
        slug="sh-3col",
        label="3 columns",
        category="Layout",
        html='<div class="grid grid-cols-1 sm:grid-cols-3 gap-4"><div class="min-h-16'
        ' rounded-md border border-dashed border-border p-4"></div><div class="min-h-16'
        ' rounded-md border border-dashed border-border p-4"></div><div class="min-h-16'
        ' rounded-md border border-dashed border-border p-4"></div></div>',
    ),
]
