---
name: SignalWatch Professional
colors:
  surface: '#f9f9ff'
  surface-dim: '#cfdaf2'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eeff'
  surface-container-high: '#dee8ff'
  surface-container-highest: '#d8e3fb'
  on-surface: '#111c2d'
  on-surface-variant: '#424754'
  inverse-surface: '#263143'
  inverse-on-surface: '#ecf1ff'
  outline: '#727785'
  outline-variant: '#c2c6d6'
  surface-tint: '#005ac2'
  primary: '#0058be'
  on-primary: '#ffffff'
  primary-container: '#2170e4'
  on-primary-container: '#fefcff'
  inverse-primary: '#adc6ff'
  secondary: '#855300'
  on-secondary: '#ffffff'
  secondary-container: '#fea619'
  on-secondary-container: '#684000'
  tertiary: '#b61722'
  on-tertiary: '#ffffff'
  tertiary-container: '#da3437'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a42'
  on-primary-fixed-variant: '#004395'
  secondary-fixed: '#ffddb8'
  secondary-fixed-dim: '#ffb95f'
  on-secondary-fixed: '#2a1700'
  on-secondary-fixed-variant: '#653e00'
  tertiary-fixed: '#ffdad7'
  tertiary-fixed-dim: '#ffb3ad'
  on-tertiary-fixed: '#410004'
  on-tertiary-fixed-variant: '#930013'
  background: '#f9f9ff'
  on-background: '#111c2d'
  surface-variant: '#d8e3fb'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Hanken Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-mono:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-caps:
    fontFamily: Hanken Grotesk
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 0.25rem
  sm: 0.5rem
  md: 1rem
  lg: 1.5rem
  xl: 2rem
  2xl: 3rem
  gutter: 1.5rem
  margin-mobile: 1rem
  margin-desktop: 2.5rem
---

## Brand & Style

This design system is built for high-stakes technical environments requiring rapid cognitive processing of complex RF data. The brand personality is clinical, authoritative, and precise, avoiding decorative flourishes in favor of functional clarity.

The aesthetic follows a **Modern Corporate** approach with a strong emphasis on **Data-Centric Minimalism**. By utilizing a high-ratio of white space and a rigid structural grid, the interface reduces visual noise, allowing critical spectrum anomalies to surface immediately. The emotional response should be one of calm control and absolute reliability.

## Colors

The palette is rooted in a professional "Utility-First" logic. 

- **Primary (Blue):** Used for interactive states, primary actions, and nominal signal readings.
- **Warning (Amber):** Reserved strictly for moderate interference or non-critical anomalies.
- **Critical (Coral-red):** High-contrast color dedicated to severe signal breaches and hardware failures.
- **Neutral/Background:** The environment uses an off-white base to reduce eye strain, while pure white surfaces indicate elevated content containers. Text is rendered in deep Navy to ensure maximum legibility against the light background.

## Typography

The system utilizes **Hanken Grotesk** for its contemporary, geometric balance and exceptional legibility in technical dashboards. It provides a sharp, professional look that bridges the gap between traditional corporate and modern tech.

For technical data points, frequencies (MHz/GHz), and timestamps, **JetBrains Mono** is employed to ensure that numerical characters are distinct and align vertically in tables and lists.

- **Headlines:** Use a tighter letter-spacing for a grounded, authoritative feel.
- **Data Labels:** Use the `label-caps` style for section headers within cards to create a clear hierarchy.

## Layout & Spacing

The layout utilizes a **Fixed Grid** model for the main dashboard to ensure data visualizations maintain their aspect ratios and readability. 

- **Grid:** 12-column system on desktop with 24px gutters.
- **Structure:** A persistent slim left-hand navigation rail (72px) expands on hover, maximizing the canvas for live-stream charts.
- **Breakpoints:**
  - **Desktop (1280px+):** 12 columns, 40px side margins.
  - **Tablet (768px - 1279px):** 8 columns, 24px side margins. Large charts stack vertically.
  - **Mobile (<767px):** 4 columns, 16px side margins. Data tables convert to card-lists.

## Elevation & Depth

Depth is communicated through **Tonal Layers** and **Ambient Shadows** rather than heavy borders.

1.  **Level 0 (Base):** Off-white (#F8FAFC) background.
2.  **Level 1 (Surface):** Pure white cards with a 1px border (#E2E8F0). This is the default state for data modules.
3.  **Level 2 (Active/Hover):** Cards gain a very soft, diffused shadow (0px 4px 12px rgba(30, 41, 59, 0.05)) to indicate interactivity.
4.  **Level 3 (Overlays):** Slide-out drawers and modals. These use a higher-elevation shadow (0px 12px 32px rgba(30, 41, 59, 0.1)) and a background backdrop blur (4px) to maintain context while focusing the user.

## Shapes

The shape language is **Soft** and restrained. A 4px (`0.25rem`) corner radius is applied to standard UI elements like input fields, small buttons, and tags. Large containers and dashboard cards use the `rounded-lg` (8px) value to provide a sophisticated, modern feel without appearing overly "bubbly" or consumer-grade.

## Components

### Buttons & Inputs
- **Primary Action:** Solid Blue (#3B82F6) with white text. No gradients.
- **Secondary Action:** White fill with 1px Blue border.
- **Technical Inputs:** Input fields use `label-mono` for values. Focus states utilize a 2px Blue ring with a 2px offset.

### Summary Cards
Compact containers used for high-level KPIs (e.g., "Active Signals"). They feature a top-aligned `label-caps` title, a `display-lg` value, and a small sparkline chart at the bottom.

### Ranked Lists
Used for "Top Interference Sources." These utilize a zebra-stripe pattern on hover using the Off-white base color. They must include a status indicator dot (Primary, Warning, or Critical) on the far left.

### Slide-out Drawer
Appears from the right at a fixed width of 400px. It is used for "Signal Details." It should contain high-density metadata tables and a secondary, high-resolution waterfall chart.

### Charts & Viz
Charts should use a 1.5pt stroke width for lines. The area under lines should have a subtle 5% opacity fill of the line color. Grid lines within charts must be the `border_subtle` color and set to a 0.5pt thickness.