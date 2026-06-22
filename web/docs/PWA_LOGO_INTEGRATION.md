# Orbit PWA Logo Integration Spec

## Objective

Integrate the Orbit logo as the browser favicon and home-screen app icon for the Jarvis web app.

This spec applies only to:

```text
C:\Users\migue\Documents\jarvis\web
```

Do not apply this change to:

```text
C:\Users\migue\Documents\nominas
```

`jarvis` and `nominas` are separate projects.

## Required Assets

Place all icon assets under:

```text
web/public/icons/
```

Required files:

```text
web/public/icons/favicon-32.png
web/public/icons/orbit-apple-touch-icon.png
web/public/icons/orbit-icon-192.png
web/public/icons/orbit-icon-512.png
web/public/icons/orbit-icon.svg
```

Asset requirements:

- `favicon-32.png`: `32x32`, browser tab icon.
- `orbit-apple-touch-icon.png`: `180x180`, iPhone home-screen icon.
- `orbit-icon-192.png`: `192x192`, PWA manifest icon.
- `orbit-icon-512.png`: `512x512`, high-resolution PWA manifest icon.
- `orbit-icon.svg`: source/reference vector for the Orbit logo.

The PNGs should use a dark square background with the pink Orbit mark centered. Do not bake rounded corners into the image; iOS applies its own app-icon mask.

## Manifest

Create:

```text
web/public/manifest.webmanifest
```

Expected content:

```json
{
  "name": "Orbit",
  "short_name": "Orbit",
  "description": "Soft UI web client for Orbit",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "background_color": "#0b0d12",
  "theme_color": "#0b0d12",
  "icons": [
    {
      "src": "/icons/orbit-icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/orbit-icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
}
```

## Next.js Metadata

Update:

```text
web/app/layout.tsx
```

The `metadata` export should include:

```ts
export const metadata: Metadata = {
  applicationName: "Orbit",
  title: "Orbit",
  description: "Soft UI web client for Orbit",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    title: "Orbit",
    statusBarStyle: "black-translucent",
  },
  icons: {
    icon: [
      {
        url: "/icons/favicon-32.png",
        sizes: "32x32",
        type: "image/png",
      },
    ],
    apple: [
      {
        url: "/icons/orbit-apple-touch-icon.png",
        sizes: "180x180",
        type: "image/png",
      },
    ],
  },
};
```

The `viewport` export should include:

```ts
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#0b0d12",
};
```

## Validation

From:

```text
C:\Users\migue\Documents\jarvis\web
```

Run:

```powershell
npm run build
```

Expected result:

- Build completes successfully.
- Generated HTML includes:
  - `<link rel="manifest" href="/manifest.webmanifest">`
  - `<link rel="icon" href="/icons/favicon-32.png" ...>`
  - `<link rel="apple-touch-icon" href="/icons/orbit-apple-touch-icon.png" ...>`
  - `<meta name="theme-color" content="#0b0d12">`

Runtime checks:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:3000/manifest.webmanifest
Invoke-WebRequest -UseBasicParsing http://localhost:3000/icons/orbit-apple-touch-icon.png
Invoke-WebRequest -UseBasicParsing http://localhost:3000/icons/favicon-32.png
```

Expected runtime results:

- Manifest returns status `200`.
- PNG icons return `Content-Type: image/png`.

## iPhone Home-Screen Test

1. Open the Jarvis web app in Safari.
2. Use the Share button.
3. Select `Add to Home Screen`.
4. Confirm the displayed app name is `Orbit`.
5. Confirm the app icon uses the dark square background with the pink Orbit logo.

If iPhone keeps showing an old icon, delete the old home-screen shortcut and add it again. iOS can cache PWA icons aggressively.

## Current Local Dev URL

When the dev server is running from `jarvis/web`, use:

```text
http://localhost:3000/
```

From a phone on the same Wi-Fi network, use the computer's local IP, for example:

```text
http://192.168.1.244:3000/
```

