# currency-switch

**What it is and when to use it.** A row of choices, one per currency, that
shows every price on the page in the currency a visitor picks. Use it on a
pricing page that shows its prices in two to six currencies. A page with one
currency has nothing to switch and reads better without it, and a page can
show several currencies with no switch at all: its prices then sit side by
side, which is the right choice for two currencies and a short page.

It is a pattern of its own, not an option on `pricing-tiers`, because prices
are not only in tier cards. A pricing page repeats them in its questions and
answers and its small print, and one switch has to move all of them.

**How it works.** The switch is a radio group, and the stylesheet alone does
the switching, so it works where scripts do not run. It reads the place of the
picked option and shows the price in the same place inside every wrapper:

```html
<span class="currency-switch-price"><span>first</span><span>second</span></span>
```

So the options and the prices inside every wrapper are written **in one
order**, and every wrapper carries every currency. A wrapper one currency
short shows nothing when that currency is picked. Nothing but the prices goes
inside a wrapper: the words around a price, "a week" or "every 3 months", are
written once, after it.

Where a browser cannot switch, the choices are not drawn and every price
shows each currency side by side, separated by a middle dot. That is also
what a page with wrapped prices and no switch looks like.

**What it needs.** Prices already written once per currency, in one order, in
the visible text. The real name of each currency for its option, in the
visitor's words: "US dollars" tells them more than "USD", and two dollars on
one page need telling apart. A short label saying what the choice does. The
value of each option is its currency code in lower case. Structured data is
not switched: it keeps one currency, the page's first.

**Pairing.** Directly above `pricing-tiers`, under the page's opening, so the
choice is made before the first price is read. One per page: two switches
would disagree. It changes nothing but the prices, so it sits anywhere above
them; below the plans it is a control found after the decision.

**Brand adaptability.** `--chip-radius` shapes the options, and the picked
one fills with `--color-primary` and `--color-on-primary`, the contract's
stated pair. Options are 44px tall at least and wrap onto a second row on a
phone; six short names fit two rows at 320px. A brand may raise
`--currency-switch-target` and should not lower it.

**Behaviour (gated).** The fieldset carries the `currency` hook. On platforms
serving the behaviour library the visitor's choice is remembered on that
device for the site's other pages, and the change is announced to a screen
reader in the words of `data-hub-currency-announce` (default "Prices shown
in") followed by the option's name. Without the library the switch works
exactly as authored and opens in the first currency every time.
