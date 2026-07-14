# AIMGANLY

This repository now contains two app versions:

- `php_app/` - the active PHP version
- `python_papp/` - the old Python Streamlit version moved into its own folder

## Active App

The active app is the PHP rewrite inside `php_app`.

Run it with:

```powershell
cd php_app
composer install
php -S 127.0.0.1:8000 -t public
```

Open:

```text
http://127.0.0.1:8000
```

## Legacy Python App

The previous Python app is preserved in `python_papp`.

That folder contains:

- `app.py`
- `ci_utils.py`
- `gemini_client.py`
- `inventory_store.py`
- `requirements.txt`
- `.env.example`

## Shared Assets

- `maybank/pdrn/` keeps the Maybank workbook template used by the app
- root `.env` can still be used for shared secrets like `GEMINI_API_KEY`
