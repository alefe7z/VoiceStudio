# Support page

The support page puts the monthly development goal, donation amounts, and Ko-fi / PayPal links first. Selecting an amount carries it into PayPal; Ko-fi lets you choose the amount on its own page. No checkout opens until you choose a provider.

Star and community links offer other ways to help. The Electron page uses the official VoiceStudio logo, a single donation panel and an icon grid for contact channels; it shows no sponsor logos or Pro card. No accordion hides those actions. Controls support keyboard navigation, and decorative interaction animations respect reduced-motion preferences.

The app shows no advertising footer, sponsor placements, Get Pro or Star buttons, or `/pro` pricing page. Support is reached only from Settings → Support. Integrations is reachable from the sidebar and opens the directory.


On the Integrations page, only entries with a built-in setup show Works with VoiceStudio and capability chips; the rest are marked External link. Setup details and source links are recorded in [the directory notes](integration-directory.md).

License keys require OS-backed encryption; activation fails with a storage error
when the keyring is unavailable or Electron selects plaintext storage. Existing
legacy key files remain readable for deactivation.
