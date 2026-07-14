# AIMGANLY PHP

This is the PHP rewrite of the CI -> AO -> Officer workflow.

## Features

- login with CI, AO, and Officer roles
- CI notes submission
- AO queue and workbook generation
- BPI / Maybank template export
- Officer inbox with workbook download
- Gemini image analysis page for Officer
- JSON-based inventory storage in `php_app/storage/inventory.json`

## Run

From the project root:

```powershell
cd php_app
composer install
php -S 127.0.0.1:8000 -t public
```

Then open:

```text
http://127.0.0.1:8000
```

## Config

The PHP app reads environment values from the project root `.env` when available.

Supported variables:

- `GEMINI_API_KEY`
- `CI_EMAIL`
- `CI_PASSWORD`
- `AO_EMAIL`
- `AO_PASSWORD`
- `OFFICER_EMAIL`
- `OFFICER_PASSWORD`
- `BPI_TEMPLATE_PATH`

## Notes

- The Maybank template is loaded from `maybank/pdrn/MAYBANK PDRN.xlsx`
- Generated files are saved in `php_app/storage/exports`
- The PHP rewrite currently focuses on the core workflow and export path first
