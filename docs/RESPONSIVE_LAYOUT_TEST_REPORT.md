# Responsive layout test report

Test date: 13 August 2026

## Automated coverage

The browser test uses the installed desktop Chrome through Playwright Core and
checks four representative viewport sizes:

| Device class | Viewport |
| --- | --- |
| Mobile | 390 × 844 |
| Tablet | 768 × 1024 |
| Laptop | 1366 × 768 |
| Desktop | 1920 × 1080 |

Fourteen representative routes are checked at every size: home, about,
contact, gallery, services, shop, booking, cart, login, registration, account,
management, management reports and POS. This produces 56 page/viewport cases.

For each case the test verifies:

- the page renders without a server error;
- a semantic `main` landmark and document title are present;
- the document does not create horizontal page scrolling;
- ordinary content is not clipped outside the viewport;
- deliberately scrollable category bars and tables are treated as intentional;
- mobile/tablet display the mobile-menu control and can open and close it with
  Escape; and
- laptop/desktop display the primary navigation and hide the mobile control.

Run the test while the frontend development server is available:

```powershell
cd frontend
npm.cmd run dev
```

Then, in another terminal:

```powershell
cd frontend
npm.cmd run test:responsive
```

Set `RESPONSIVE_TEST_BASE_URL` or `CHROME_PATH` when testing another deployment
or browser location.

## Result

All 56 automated layout cases passed. The initial run correctly revealed that
the services and shop category rows extend beyond narrow viewports; inspection
confirmed these rows are intentionally horizontally scrollable rather than
causing document-level overflow.

## Manual checks still required

Automation cannot validate visual taste or real touch ergonomics completely.
Before launch, manually check on at least one physical phone and tablet:

1. text remains comfortably readable without zooming;
2. buttons and form controls are comfortable to tap;
3. the on-screen keyboard does not hide the active booking, checkout or login
   field;
4. orientation changes preserve entered form data;
5. long management tables scroll horizontally without trapping the page; and
6. images look correctly cropped on the actual display.
