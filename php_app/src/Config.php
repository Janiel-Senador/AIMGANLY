<?php

declare(strict_types=1);

namespace App;

final class Config
{
    public static function rootPath(): string
    {
        return dirname(__DIR__, 2);
    }

    public static function appPath(): string
    {
        return dirname(__DIR__);
    }

    public static function dataPath(): string
    {
        return self::appPath() . DIRECTORY_SEPARATOR . 'storage';
    }

    public static function exportPath(): string
    {
        return self::dataPath() . DIRECTORY_SEPARATOR . 'exports';
    }

    public static function inventoryPath(): string
    {
        return self::dataPath() . DIRECTORY_SEPARATOR . 'inventory.json';
    }

    public static function bpiTemplatePath(): string
    {
        return getenv('BPI_TEMPLATE_PATH') ?: 'C:\Users\Jan\Downloads\PDRN-MAPPING-1_efa98837-83fc-4d76-987a-3101659aafce.xls';
    }

    public static function maybankTemplatePath(): string
    {
        return self::rootPath() . DIRECTORY_SEPARATOR . 'maybank' . DIRECTORY_SEPARATOR . 'pdrn' . DIRECTORY_SEPARATOR . 'MAYBANK PDRN.xlsx';
    }

    public static function templateDefinitions(): array
    {
        return [
            'bpi' => [
                'label' => 'BPI PDRN',
                'path' => self::bpiTemplatePath(),
                'sheet_name' => 'PDRN',
            ],
            'maybank' => [
                'label' => 'Maybank PDRN',
                'path' => self::maybankTemplatePath(),
                'sheet_name' => 'Sheet1',
            ],
        ];
    }

    public static function users(): array
    {
        $ciEmail = strtolower(trim((string) (getenv('CI_EMAIL') ?: 'ci@company.com')));
        $aoEmail = strtolower(trim((string) (getenv('AO_EMAIL') ?: 'janielsenador@gmail.com')));
        $officerEmail = strtolower(trim((string) (getenv('OFFICER_EMAIL') ?: 'officer@company.com')));

        return [
            $ciEmail => [
                'password' => (string) (getenv('CI_PASSWORD') ?: 'CI123456'),
                'role' => 'ci',
                'name' => 'CI Encoder',
            ],
            $aoEmail => [
                'password' => (string) (getenv('AO_PASSWORD') ?: '123456'),
                'role' => 'ao',
                'name' => 'Account Officer',
            ],
            $officerEmail => [
                'password' => (string) (getenv('OFFICER_PASSWORD') ?: 'Officer123!'),
                'role' => 'officer',
                'name' => 'Senior Account Officer',
            ],
        ];
    }

    public static function geminiApiKey(): string
    {
        return trim((string) getenv('GEMINI_API_KEY'));
    }
}
